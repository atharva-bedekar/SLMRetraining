"""Submit a 200-request Gemini Batch API job for V4-1325 (gen_rp=1.00_fb1.08) finetuned outputs, reusing saved base judgments."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from scripts.evaluate_v4_1325 import parse_inlined_response
from scripts.phase_results import ROOT, digest, read_json
from scripts.run_deepeval import atomic_json, create_metrics, run_lock
from scripts.source_grounded_rubric import METRIC_STEPS, VERSION


def prepare(root=ROOT):
    root = Path(root)
    result = root / "results_v4"
    contract = read_json(result / "baseline/comparison_contract.json")
    prepared = root / "prepared_clinical_dataset" / contract["dataset_version"]
    rows = [json.loads(x) for x in (prepared / "validation.jsonl").read_text(encoding="utf-8").split("\n") if x.strip()]
    assert len(rows) == 100 and [r["case_id"] for r in rows] == contract["case_ids"]

    base_dir = result / "baseline/gen_rp_1.08"
    ft_dir = result / "comparison/finetuned_v4__gen_rp_1.00"
    base_gens = read_json(base_dir / "generations.json")
    ft_gens = read_json(ft_dir / "generations.json")

    flags = {}
    for model, folder in (("baseline", base_dir), ("finetuned", ft_dir)):
        with (folder / "per_case.csv").open(encoding="utf-8", newline="") as handle:
            scores = list(csv.DictReader(handle))
        flags[model] = {r["case_id"]: r for r in scores}
        assert len(scores) == 100 and set(flags[model]) == set(contract["case_ids"])

    # Reuse the 200 baseline judgments from 8b852f1592dfcc99
    prev_scores_path = result / "deepeval_100/judgments/8b852f1592dfcc99/scores.json"
    prev_scores = read_json(prev_scores_path)
    base_records = [r for r in prev_scores if r["model"] == "baseline"]
    assert len(base_records) == 200

    pairs = [
        dict(
            case_id=r["case_id"],
            input=r["note"],
            expected_output=r["reference"],
            baseline_output=base_gens[r["case_id"]],
            finetuned_output=ft_gens[r["case_id"]],
            format_metrics={m: flags[m][r["case_id"]] for m in flags},
        )
        for r in rows
    ]
    selection = dict(
        experiment="v4_regenerated_labels_1325_gen_rp_1.00_fb1.08",
        dataset_version=contract["dataset_version"],
        selected_cases=100,
        new_finetuned_measurements=200,
        reused_baseline_run="8b852f1592dfcc99",
        reused_baseline_scores_sha256=hashlib.sha256(prev_scores_path.read_bytes()).hexdigest(),
        case_ids=contract["case_ids"],
        pairs_sha256=digest(pairs),
        rubric_version=VERSION,
        metric_steps=METRIC_STEPS,
    )
    directory = result / "deepeval_100_rp1"
    directory.mkdir(parents=True, exist_ok=True)
    for fname, val in (("selection_manifest.json", selection), ("paired_cases.json", pairs)):
        p = directory / fname
        if p.exists() and read_json(p) != val:
            raise ValueError(f"{fname} changed")
        if not p.exists():
            atomic_json(p, val)
    return directory, selection, pairs, base_records


def run_batch(root=ROOT, model="gemini-4-hydrogen", poll_seconds=300):
    directory, selection, pairs, base_records = prepare(root)
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
    os.environ["DEEPEVAL_DISABLE_DOTENV"] = "1"
    version = importlib.metadata.version("deepeval")
    assert version == "4.3.4"

    from dotenv import load_dotenv
    load_dotenv(Path(root) / ".env.local")
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    assert key, "Set GEMINI_API_KEY in .env.local"

    from deepeval.metrics.g_eval import schema as gschema
    from deepeval.models import GeminiModel
    from deepeval.test_case import LLMTestCase
    from google.genai import types

    judge = GeminiModel(model=model, api_key=key, temperature=0, use_vertexai=False)
    client = judge.load_model()

    contract = dict(
        selection_sha256=digest(selection),
        pairs_sha256=digest(pairs),
        backend="gemini_batch_200_ft_only",
        model=model,
        deepeval_version=version,
        rubric_version=VERSION,
        truth_source="input clinical note",
    )
    out = directory / "judgments" / digest(contract)[:16]
    out.mkdir(parents=True, exist_ok=True)

    with run_lock(out):
        if not (out / "run_contract.json").exists():
            atomic_json(out / "run_contract.json", contract)

        safety_settings = [
            types.SafetySetting(category=cat, threshold=types.HarmBlockThreshold.BLOCK_NONE)
            for cat in (
                types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            )
        ]
        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=gschema.ReasonScore,
            safety_settings=safety_settings,
            temperature=0.0,
        )

        items, inlined_requests = [], []
        for pair in pairs:
            tc = LLMTestCase(input=pair["input"], expected_output=pair["expected_output"], actual_output=pair["finetuned_output"])
            for metric in create_metrics(judge, source_grounded=True):
                prompt = metric._results_prompt(tc, multimodal=False, _additional_context=None)
                meta = {"case_id": pair["case_id"], "model": "finetuned", "metric": metric.name}
                items.append(meta)
                inlined_requests.append(types.InlinedRequest(contents=prompt, metadata=meta, config=gen_config))
        assert len(inlined_requests) == 200

        batch_state_path = out / "batch_job.json"
        if batch_state_path.exists():
            bstate = read_json(batch_state_path)
            job_name = bstate["job_name"]
        else:
            job = client.batches.create(
                model=model,
                src=inlined_requests,
                config={"display_name": f"clinical_v4_rp1_200_{out.name}"},
            )
            job_name = job.name
            bstate = {
                "job_name": job_name,
                "model": model,
                "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
                "requests_count": 200,
            }
            atomic_json(batch_state_path, bstate)
            print(f"Submitted 200-request Gemini BatchJob: {job_name}", flush=True)

        while True:
            job = client.batches.get(name=job_name)
            state_name = str(job.state.name if job.state else "UNKNOWN")
            bstate.update(state=state_name, last_checked_at_utc=datetime.now(timezone.utc).isoformat(), done=bool(job.done))
            atomic_json(batch_state_path, bstate)
            print(f"[{bstate['last_checked_at_utc']}] BatchJob {job_name} state={state_name} done={job.done}", flush=True)
            if job.done:
                assert state_name == "JOB_STATE_SUCCEEDED", f"Batch failed: {state_name} {job.error}"
                by_id = {p["case_id"]: p for p in pairs}
                ft_records = []
                for item, resp_item in zip(items, job.dest.inlined_responses):
                    score, reason = parse_inlined_response(resp_item)
                    ft_records.append(
                        dict(
                            case_id=item["case_id"],
                            model="finetuned",
                            metric=item["metric"],
                            score=score,
                            reason=reason,
                            format_metrics=by_id[item["case_id"]]["format_metrics"]["finetuned"],
                        )
                    )
                all_records = base_records + ft_records
                assert len(all_records) == 400
                atomic_json(out / "scores.json", all_records)

                comparison = []
                for pair in pairs:
                    for metric in METRIC_STEPS:
                        scores = {r["model"]: r["score"] for r in all_records if r["case_id"] == pair["case_id"] and r["metric"] == metric}
                        comparison.append(
                            {
                                "case_id": pair["case_id"],
                                "metric": metric,
                                **scores,
                                "finetuned_minus_baseline": scores["finetuned"] - scores["baseline"],
                            }
                        )
                with (out / "paired_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(comparison[0]))
                    writer.writeheader()
                    writer.writerows(comparison)

                summary = {
                    "complete": True,
                    "backend": "gemini_batch_200_ft_only",
                    "model": model,
                    "selected_cases": 100,
                    "paired_test_cases": 200,
                    "measurements": 400,
                    "reused_baseline_run": "8b852f1592dfcc99",
                    "mean_scores": {
                        metric: {
                            m: sum(r["score"] for r in all_records if r["metric"] == metric and r["model"] == m) / 100
                            for m in ("baseline", "finetuned")
                        }
                        for metric in METRIC_STEPS
                    },
                    "mean_paired_deltas": {
                        metric: sum(r["finetuned_minus_baseline"] for r in comparison if r["metric"] == metric) / 100
                        for metric in METRIC_STEPS
                    },
                    "rubric_version": VERSION,
                    "truth_source": "input clinical note",
                    "run_id": out.name,
                }
                atomic_json(out / "summary.json", summary)
                print("Completed 200-request rp1 BatchJob:", json.dumps(summary, indent=2), flush=True)
                return out
            time.sleep(poll_seconds)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--batch", action="store_true")
    p.add_argument("--poll-seconds", type=int, default=300)
    p.add_argument("--model", default="gemini-4-hydrogen")
    args = p.parse_args()
    if args.prepare_only or not args.batch:
        prepare()
        print("Prepared 200-request rp1 batch (reusing 200 base scores); no API calls made.")
    else:
        run_batch(model=args.model, poll_seconds=args.poll_seconds)
