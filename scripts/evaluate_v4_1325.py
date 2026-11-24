"""Prepare and evaluate the 100 v4 (ca7b6e90c1019441) pairs via the Gemini Batch API (or sequential DeepEval) with 5-minute polling."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from scripts.phase_results import ROOT, digest, read_json
from scripts.run_deepeval import atomic_json, create_metrics, evaluate, run_lock
from scripts.source_grounded_rubric import METRIC_STEPS, VERSION


def prepare(root=ROOT):
    root = Path(root)
    result = root / "results_v4"
    contract = read_json(result / "baseline/comparison_contract.json")
    prepared = root / "prepared_clinical_dataset" / contract["dataset_version"]
    manifest = read_json(prepared / "manifest.json")
    rows = [json.loads(x) for x in (prepared / "validation.jsonl").read_text(encoding="utf-8").split("\n") if x.strip()]
    frozen = [json.loads(x) for x in (root / "prepared_clinical_dataset/e80798edebe5aba5/validation.jsonl").read_text(encoding="utf-8").split("\n") if x.strip()]
    assert len(rows) == 100 and manifest["counts"] == dict(train=1325, validation=100)
    assert [(r["case_id"], r["note"], r["prompt_text"]) for r in rows] == [(r["case_id"], r["note"], r["prompt_text"]) for r in frozen]
    assert digest(rows) == manifest["split_sha256"]["validation"] == contract["validation_sha256"]
    assert manifest["split_sha256"]["train"] == contract["train_sha256"]
    assert [r["case_id"] for r in rows] == contract["case_ids"]
    assert digest([r["prompt_text"] for r in rows]) == contract["prompt_sha256"]
    assert read_json(result / "finetuned_v4/comparison_contract.json") == contract
    run_cfg = read_json(result / "finetuned_v4/run_config.json")
    assert run_cfg["train_examples"] == 1325 and run_cfg["num_train_epochs"] == 3
    assert run_cfg["comparison_contract_sha256"] == digest(contract)
    training = read_json(result / "finetuned_v4/metrics.json")
    assert training["train"]["epoch"] == 3.0

    outputs, flags, sources = {}, {}, []
    for model, folder in (
        ("baseline", result / "baseline/gen_rp_1.08"),
        ("finetuned", result / "comparison/finetuned__gen_rp_1.08"),
    ):
        outputs[model] = read_json(folder / "generations.json")
        with (folder / "per_case.csv").open(encoding="utf-8", newline="") as handle:
            scores = list(csv.DictReader(handle))
        flags[model] = {r["case_id"]: r for r in scores}
        assert len(scores) == 100 and set(flags[model]) == set(outputs[model]) == set(contract["case_ids"])
        for row in rows:
            score = flags[model][row["case_id"]]
            assert score["reference"] == row["reference"] and score["generated"] == outputs[model][row["case_id"]]
        sources += [folder / "generations.json", folder / "per_case.csv"]

    pairs = [
        dict(
            case_id=r["case_id"],
            input=r["note"],
            expected_output=r["reference"],
            baseline_output=outputs["baseline"][r["case_id"]],
            finetuned_output=outputs["finetuned"][r["case_id"]],
            format_metrics={m: flags[m][r["case_id"]] for m in flags},
        )
        for r in rows
    ]
    selection = dict(
        experiment="v4_regenerated_labels_1325",
        dataset_version=contract["dataset_version"],
        selected_cases=100,
        paired_test_cases=200,
        planned_metric_measurements=400,
        case_ids=contract["case_ids"],
        comparison_contract_sha256=digest(contract),
        pairs_sha256=digest(pairs),
        rubric_version=VERSION,
        metric_steps=METRIC_STEPS,
        evaluation_scope="Unchanged source_grounded_v2 rubric (input clinical note is sole authority; regenerated v4 reference is secondary checklist).",
        source_sha256={
            str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources
        },
    )
    directory = result / "deepeval_100"
    directory.mkdir(parents=True, exist_ok=True)
    for filename, value in (("selection_manifest.json", selection), ("paired_cases.json", pairs)):
        path = directory / filename
        if path.exists() and read_json(path) != value:
            raise ValueError("Frozen evaluation inputs changed; refusing to reuse scores")
        if not path.exists():
            atomic_json(path, value)
    return directory, selection, pairs


def build_batch_requests(pairs, judge_model):
    """Build the 400 exact GEval prompts and structured-output InlinedRequests."""
    from deepeval.metrics.g_eval import schema as gschema
    from deepeval.test_case import LLMTestCase
    from google.genai import types

    items = []
    inlined_requests = []
    safety_settings = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
    gen_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=gschema.ReasonScore,
        safety_settings=safety_settings,
        temperature=0.0,
    )

    for index, pair in enumerate(pairs):
        models = ("baseline", "finetuned") if index % 2 == 0 else ("finetuned", "baseline")
        for model_key in models:
            test_case = LLMTestCase(
                input=pair["input"],
                expected_output=pair["expected_output"],
                actual_output=pair[model_key + "_output"],
            )
            for metric in create_metrics(judge_model, source_grounded=True):
                prompt = metric._results_prompt(test_case, multimodal=False, _additional_context=None)
                meta = {
                    "case_id": pair["case_id"],
                    "model": model_key,
                    "metric": metric.name,
                }
                items.append({**meta, "prompt": prompt})
                inlined_requests.append(
                    types.InlinedRequest(
                        contents=prompt,
                        metadata=meta,
                        config=gen_config,
                    )
                )
    assert len(inlined_requests) == 400
    return items, inlined_requests


def parse_inlined_response(resp_item):
    if resp_item.error is not None and getattr(resp_item.error, "message", None):
        raise RuntimeError(f"Batch item failed: {resp_item.error}")
    response = resp_item.response
    if response is None:
        raise RuntimeError("Batch item returned None response")
    parsed = getattr(response, "parsed", None)
    if parsed is not None and hasattr(parsed, "score") and hasattr(parsed, "reason"):
        raw_score = float(parsed.score)
        reason = str(parsed.reason)
    else:
        text = getattr(response, "text", None)
        if not text:
            cands = getattr(response, "candidates", None) or []
            if cands and getattr(cands[0], "content", None) and cands[0].content.parts:
                text = cands[0].content.parts[0].text
        if not text:
            raise RuntimeError("Batch item returned empty text")
        obj = json.loads(text)
        raw_score = float(obj["score"])
        reason = str(obj["reason"])
    # Normalize 0-10 GEval score to 0.0-1.0 exactly as GEval.measure() does: (g_score - 0) / 10
    norm_score = raw_score / 10.0
    if not math.isfinite(norm_score) or not 0.0 <= norm_score <= 1.0:
        raise ValueError(f"Normalized score out of range [0, 1]: {norm_score} (raw={raw_score})")
    if not reason.strip():
        raise ValueError("Empty reason in batch response")
    return norm_score, reason


def finalize_batch_results(out, pairs, contract, model_name, items, inlined_responses):
    if len(inlined_responses) != len(items):
        raise ValueError(f"Expected {len(items)} responses, got {len(inlined_responses)}")
    by_id = {p["case_id"]: p for p in pairs}
    records = []
    for item, resp_item in zip(items, inlined_responses):
        meta = getattr(resp_item, "metadata", None) or {}
        cid = meta.get("case_id") or item["case_id"]
        m_key = meta.get("model") or item["model"]
        metric_name = meta.get("metric") or item["metric"]
        assert (cid, m_key, metric_name) == (item["case_id"], item["model"], item["metric"])
        score, reason = parse_inlined_response(resp_item)
        records.append(
            dict(
                case_id=cid,
                model=m_key,
                metric=metric_name,
                score=score,
                reason=reason,
                format_metrics=by_id[cid]["format_metrics"][m_key],
            )
        )

    expected_keys = {(p["case_id"], m, met) for p in pairs for m in ("baseline", "finetuned") for met in METRIC_STEPS}
    completed = {(r["case_id"], r["model"], r["metric"]) for r in records}
    assert len(records) == 400 and completed == expected_keys
    atomic_json(out / "scores.json", records)

    comparison = []
    for pair in pairs:
        for metric in METRIC_STEPS:
            scores = {r["model"]: r["score"] for r in records if r["case_id"] == pair["case_id"] and r["metric"] == metric}
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
        "backend": "gemini_batch",
        "model": model_name,
        "selected_cases": len(pairs),
        "paired_test_cases": len(pairs) * 2,
        "measurements": len(records),
        "mean_scores": {
            metric: {
                model: sum(r["score"] for r in records if r["metric"] == metric and r["model"] == model) / len(pairs)
                for model in ("baseline", "finetuned")
            }
            for metric in METRIC_STEPS
        },
        "mean_paired_deltas": {
            metric: sum(r["finetuned_minus_baseline"] for r in comparison if r["metric"] == metric) / len(pairs)
            for metric in METRIC_STEPS
        },
        "rubric_version": contract["rubric_version"],
        "truth_source": "input clinical note",
        "run_id": out.name,
    }
    atomic_json(out / "summary.json", summary)
    return summary


def run_batch(root=ROOT, model="gemini-4-hydrogen", poll_seconds=300, status_only=False):
    directory, selection, pairs = prepare(root)
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
    os.environ["DEEPEVAL_DISABLE_DOTENV"] = "1"
    version = importlib.metadata.version("deepeval")
    if version != "4.3.4":
        raise RuntimeError("Use the isolated requirements-deepeval.txt environment (.venv/deepeval-tools)")

    from dotenv import load_dotenv
    load_dotenv(Path(root) / ".env.local")
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Set GEMINI_API_KEY in .env.local or the process environment.")

    from deepeval.models import GeminiModel
    judge = GeminiModel(model=model, api_key=key, temperature=0, use_vertexai=False)
    client = judge.load_model()

    contract = dict(
        selection_sha256=digest(selection),
        pairs_sha256=digest(pairs),
        backend="gemini_batch",
        model=model,
        deepeval_version=version,
        metric_steps=METRIC_STEPS,
        rubric_version=VERSION,
        evaluation_params=["input", "actual_output", "expected_output"],
        truth_source="input clinical note",
        reference_role="fallible regenerated v4 checklist",
        score_normalization="DeepEval GEval 0-10 divided by 10 (Gemini Batch API structured output)",
    )
    out = directory / "judgments" / digest(contract)[:16]
    out.mkdir(parents=True, exist_ok=True)

    with run_lock(out):
        contract_path = out / "run_contract.json"
        if contract_path.exists() and read_json(contract_path) != contract:
            raise ValueError("Judge contract changed")
        if not contract_path.exists():
            atomic_json(contract_path, contract)

        items, inlined_requests = build_batch_requests(pairs, judge)
        batch_state_path = out / "batch_job.json"
        if not (out / "batch_requests_preview.json").exists():
            atomic_json(
                out / "batch_requests_preview.json",
                {"count": len(items), "requests_sha256": digest(items), "sample_first": items[0]},
            )

        if (out / "summary.json").exists() and read_json(out / "summary.json").get("complete"):
            print(f"Batch evaluation already complete at {out / 'summary.json'}")
            return out

        if batch_state_path.exists():
            bstate = read_json(batch_state_path)
            job_name = bstate["job_name"]
            print(f"Resuming monitoring for existing Gemini BatchJob: {job_name}", flush=True)
        else:
            if status_only:
                print("No batch job submitted yet.")
                return out
            job = client.batches.create(
                model=model,
                src=inlined_requests,
                config={"display_name": f"clinical_v4_deepeval_100_{out.name}"},
            )
            job_name = job.name
            bstate = {
                "job_name": job_name,
                "model": model,
                "run_id": out.name,
                "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
                "state": str(job.state.name if job.state else "UNKNOWN"),
                "requests_count": len(inlined_requests),
                "requests_sha256": digest(items),
            }
            atomic_json(batch_state_path, bstate)
            print(f"Submitted 400-request Gemini BatchJob: {job_name} (state={bstate['state']})", flush=True)

        while True:
            job = client.batches.get(name=job_name)
            state_name = str(job.state.name if job.state else "UNKNOWN")
            bstate.update(
                state=state_name,
                last_checked_at_utc=datetime.now(timezone.utc).isoformat(),
                done=bool(job.done),
            )
            atomic_json(batch_state_path, bstate)
            atomic_json(
                directory / "progress.json",
                {
                    "status": "complete" if state_name == "JOB_STATE_SUCCEEDED" else "running_batch",
                    "batch_job_name": job_name,
                    "batch_state": state_name,
                    "updated_at_utc": bstate["last_checked_at_utc"],
                    "run_id": out.name,
                    "expected_measurements": 400,
                },
            )
            print(f"[{bstate['last_checked_at_utc']}] BatchJob {job_name} state={state_name} done={job.done}", flush=True)
            if job.done:
                if state_name != "JOB_STATE_SUCCEEDED":
                    raise RuntimeError(f"BatchJob {job_name} ended with state {state_name}: {job.error}")
                inlined_resps = job.dest.inlined_responses if (job.dest and job.dest.inlined_responses) else None
                if not inlined_resps:
                    raise RuntimeError(f"BatchJob {job_name} succeeded but dest.inlined_responses is empty")
                summary = finalize_batch_results(out, pairs, contract, model, items, inlined_resps)
                print("Completed and verified all 400 batch judgments:", json.dumps(summary, indent=2), flush=True)
                return out
            if status_only:
                return out
            time.sleep(poll_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true", help="Freeze pairs only; no API calls")
    parser.add_argument("--batch", action="store_true", help="Submit or resume the 400-request Gemini Batch job and poll every 5 minutes")
    parser.add_argument("--status-only", action="store_true", help="Check batch status once and exit without sleeping")
    parser.add_argument("--poll-seconds", type=int, default=300, help="Polling interval in seconds (default: 300 = 5 minutes)")
    parser.add_argument("--model", default="gemini-4-hydrogen")
    args = parser.parse_args()
    if args.prepare_only or not (args.batch or args.status_only):
        prepare()
        print("Prepared 100 paired cases / 400 measurements; no judge calls made.")
    else:
        run_batch(model=args.model, poll_seconds=args.poll_seconds, status_only=args.status_only)
