"""Regenerate the extra 3,675 V2-5000 training notes via Gemini 3.8 Flash Batch API, apply V4 hygiene/repair, and package V4-5000."""
import argparse
import concurrent.futures
import json
import time
from collections import Counter
from pathlib import Path

from scripts.clean_and_repair_regenerated_v3 import (
    REPAIR_SYSTEM_PROMPT,
    build_strict_response_schema,
    check_semantic_hygiene_defects,
    deterministic_clean_v3_obj,
    repair_single_case,
)
from scripts.finalize_regenerated_v3 import normalize_and_fix_symptoms
from scripts.package_v4_regenerated_dataset import encode_regenerated_row
from scripts.phase_results import ROOT, read_json
from scripts.prepare_v2_dataset import DATASET_ID, DATASET_REVISION, MAX_SEQUENCE_LENGTH, MODEL_ID, MODEL_REVISION, digest
from scripts.prepare_v3_dataset import SCHEMA, schema_valid
from scripts.regenerate_v3_labels_batch import DEFAULT_MODEL, extract_text_from_response, get_gemini_client, now_str, save_job_state

DEFAULT_OUT_DIR = ROOT / "prepared_clinical_dataset" / "v4_5000_regenerated_gemini_3_8_flash"


def load_extra_3675_rows():
    v2_5k = [json.loads(l) for l in (ROOT / "prepared_clinical_dataset/3f8f10951130896b/train.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]
    v4_1325 = [json.loads(l) for l in (ROOT / "prepared_clinical_dataset/ca7b6e90c1019441/train.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]
    assert [r["note_sha256"] for r in v2_5k[:1325]] == [r["note_sha256"] for r in v4_1325]
    extra = v2_5k[1325:]
    assert len(extra) == 3675
    return extra


def assemble_extra_batch(out_dir: Path, max_output_tokens: int = 4096):
    out_dir.mkdir(parents=True, exist_ok=True)
    extra_rows = load_extra_3675_rows()
    schema = build_strict_response_schema()
    req_path = out_dir / "batch_requests.jsonl"
    seen = set()
    with req_path.open("w", encoding="utf-8") as handle:
        for row in extra_rows:
            cid = row["case_id"]
            assert cid not in seen
            seen.add(cid)
            entry = {
                "key": cid,
                "request": {
                    "contents": [{"role": "user", "parts": [{"text": f"Clinical note:\n{row['note']}"}]}],
                    "system_instruction": {"parts": [{"text": REPAIR_SYSTEM_PROMPT}]},
                    "generation_config": {
                        "temperature": 0.0,
                        "max_output_tokens": max_output_tokens,
                        "response_mime_type": "application/json",
                        "response_schema": schema,
                    },
                },
            }
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Dry run PASSED: {len(extra_rows)} valid JSONL requests written to {req_path} ({req_path.stat().st_size / 1024**2:.2f} MB)")
    return req_path, extra_rows


def process_and_finalize(client, batch_job, out_dir: Path):
    resp_path = out_dir / "batch_responses.jsonl"
    if not resp_path.exists():
        dest_file = getattr(getattr(batch_job, "dest", None), "file_name", None)
        if not dest_file:
            raise RuntimeError("Batch job succeeded but dest.file_name is missing.")
        raw_bytes = client.files.download(file=dest_file)
        resp_path.write_bytes(raw_bytes)

    parsed_by_key = {}
    failures = []
    for line in resp_path.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        item = json.loads(line)
        key = item.get("key")
        if item.get("error"):
            failures.append({"case_id": key, "stage": "api_error", "error": item["error"]})
            continue
        text, err = extract_text_from_response(item.get("response") or {})
        if err:
            failures.append({"case_id": key, "stage": "empty_response", "error": err})
            continue
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            failures.append({"case_id": key, "stage": "json_decode", "error": str(exc)})
            continue
        if not schema_valid(obj):
            failures.append({"case_id": key, "stage": "schema_valid", "error": "Failed 30-path schema_valid"})
            continue
        parsed_by_key[key] = obj

    extra_rows = load_extra_3675_rows()
    by_id = {r["case_id"]: r for r in extra_rows}

    # Retry any initial failures synchronously via Gemini 3.8 Flash (with retries)
    if failures:
        from google.genai import types
        strict_schema = build_strict_response_schema()
        print(f"Retrying {len(failures)} failed batch items synchronously...", flush=True)
        for f in list(failures):
            cid = f["case_id"]
            if cid in parsed_by_key:
                continue
            note = by_id[cid]["note"]
            last_err = None
            for attempt in range(1, 5):
                try:
                    resp = client.models.generate_content(
                        model=DEFAULT_MODEL,
                        contents=f"Clinical note:\n{note}",
                        config=types.GenerateContentConfig(
                            system_instruction=REPAIR_SYSTEM_PROMPT,
                            temperature=0.0,
                            max_output_tokens=8192,
                            response_mime_type="application/json",
                            response_schema=strict_schema,
                            thinking_config=types.ThinkingConfig(thinking_budget=512),
                        ),
                    )
                    obj = json.loads(resp.text or "")
                    assert schema_valid(obj)
                    parsed_by_key[cid] = obj
                    last_err = None
                    break
                except Exception as exc:
                    last_err = exc
                    time.sleep(1.5 * attempt)
            if last_err is not None:
                raise RuntimeError(f"Failed to retry {cid}: {last_err}")

    assert len(parsed_by_key) == 3675, f"Expected 3675, got {len(parsed_by_key)}"

    # Apply exact V4 deterministic scrubber + defect repair + canonical symptom negation
    cleaned_rows = []
    defective = []
    for row in extra_rows:
        cid = row["case_id"]
        obj, _ = deterministic_clean_v3_obj(parsed_by_key[cid])
        defects = check_semantic_hygiene_defects(obj, row["note"])
        if defects:
            defective.append((cid, row["note"], obj, defects))
        cleaned_rows.append((row, obj))

    if defective:
        print(f"Targeted repair on {len(defective)} extra rows with semantic hygiene defects...", flush=True)
        strict_schema = build_strict_response_schema()
        repaired_map = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            futs = {
                pool.submit(repair_single_case, client, DEFAULT_MODEL, strict_schema, by_id[cid], defects): cid
                for cid, _, _, defects in defective
            }
            for fut in concurrent.futures.as_completed(futs):
                cid, new_ref, err = fut.result()
                if new_ref is not None:
                    repaired_map[cid] = json.loads(new_ref)
        for idx, (row, obj) in enumerate(cleaned_rows):
            if row["case_id"] in repaired_map:
                cleaned_rows[idx] = (row, repaired_map[row["case_id"]])

    # Canonical "no <symptom>" unification
    final_extra = []
    sym_changes = Counter()
    for row, obj in cleaned_rows:
        obj, ch = normalize_and_fix_symptoms(obj, row["note"])
        for c in ch:
            sym_changes[c.split(":")[0]] += 1
        assert schema_valid(obj)
        final_extra.append({
            "case_id": row["case_id"],
            "source_split": row.get("source_split", "train"),
            "source_index": row.get("source_index"),
            "source_sha256": row.get("source_sha256"),
            "note_sha256": row.get("note_sha256"),
            "note": row["note"],
            "reference": json.dumps(obj, ensure_ascii=False, separators=(",", ":")),
        })

    (out_dir / "regenerated_extra_3675.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final_extra),
        encoding="utf-8",
    )

    # Package full V4-5000 (preserving 1,325 train + 100 val from ca7b6e90c1019441 verbatim!)
    import importlib.metadata
    from datasets import Dataset, DatasetDict
    from transformers import AutoTokenizer

    v4_1325_dir = ROOT / "prepared_clinical_dataset/ca7b6e90c1019441"
    v4_train_1325 = [json.loads(l) for l in (v4_1325_dir / "train.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]
    v4_val_100 = [json.loads(l) for l in (v4_1325_dir / "validation.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]

    tokenizer = AutoTokenizer.from_pretrained(str(ROOT / "results_v3/finetuned_v3/adapter"), use_fast=True)
    encoded_extra = [encode_regenerated_row(r, r["reference"], tokenizer) for r in final_extra]
    all_train = v4_train_1325 + encoded_extra
    assert len(all_train) == 5000
    assert len({r["note_sha256"] for r in all_train}) == 5000
    assert not ({r["note_sha256"] for r in all_train} & {r["note_sha256"] for r in v4_val_100})

    max_train_tok = max(r["total_tokens"] for r in all_train)
    assert max_train_tok <= 1651, f"Max total_tokens {max_train_tok} exceeds 1,651 T4 FP32 watermark!"

    splits = {"train": all_train, "validation": v4_val_100}
    hashes = {s: digest(rows) for s, rows in splits.items()}
    cfg = {
        "schema_version": 3,
        "label_version": "v4_5000_regenerated_gemini_3_8_flash_cleaned",
        "schema": SCHEMA,
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "dataset": DATASET_ID,
        "dataset_revision": DATASET_REVISION,
        "seed": 42,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "transformers": importlib.metadata.version("transformers"),
        "datasets": importlib.metadata.version("datasets"),
        "source_v4_1325_version": "ca7b6e90c1019441",
        "source_v2_5000_version": "3f8f10951130896b",
        "teacher_model": "gemini-3.8-flash",
    }
    version = digest({"config": cfg, "splits": hashes})[:16]
    pkg_dir = ROOT / "prepared_clinical_dataset" / version
    pkg_dir.mkdir(parents=True, exist_ok=True)
    DatasetDict({s: Dataset.from_list(rows) for s, rows in splits.items()}).save_to_disk(str(pkg_dir / "dataset"))
    for s, rows in splits.items():
        (pkg_dir / f"{s}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    manifest = {
        "version": version,
        "config": cfg,
        "split_sha256": hashes,
        "counts": {"train": len(all_train), "validation": len(v4_val_100)},
        "lengths": {
            s: {
                "max": max(r["total_tokens"] for r in rows),
                "mean": sum(r["total_tokens"] for r in rows) / len(rows),
                "mean_supervised": sum(r["supervised_tokens"] for r in rows) / len(rows),
                "max_supervised": max(r["supervised_tokens"] for r in rows),
            }
            for s, rows in splits.items()
        },
        "total_supervised_tokens_per_epoch": sum(r["supervised_tokens"] for r in all_train),
        "total_supervised_tokens_3_epochs": 3 * sum(r["supervised_tokens"] for r in all_train),
        "symptom_normalization_counts": dict(sym_changes),
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "prepared_clinical_dataset/latest_v4_5000.json").write_text(json.dumps({"version": version}, indent=2), encoding="utf-8")
    print(f"PACKAGED V4-5000: version={version}, max_train_tokens={max_train_tok}, val_sha={hashes['validation']}", flush=True)


def package_from_regenerated(out_dir: Path):
    final_extra = [
        json.loads(l)
        for l in (out_dir / "regenerated_extra_3675.jsonl").read_text(encoding="utf-8").split("\n")
        if l.strip()
    ]
    assert len(final_extra) == 3675
    import importlib.metadata
    from datasets import Dataset, DatasetDict
    from transformers import AutoTokenizer

    v4_1325_dir = ROOT / "prepared_clinical_dataset/ca7b6e90c1019441"
    v4_train_1325 = [json.loads(l) for l in (v4_1325_dir / "train.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]
    v4_val_100 = [json.loads(l) for l in (v4_1325_dir / "validation.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]

    tokenizer = AutoTokenizer.from_pretrained(str(ROOT / "results_v3/finetuned_v3/adapter"), use_fast=True)
    encoded_extra = [encode_regenerated_row(r, r["reference"], tokenizer) for r in final_extra]
    all_train = v4_train_1325 + encoded_extra
    assert len(all_train) == 5000
    assert len({r["note_sha256"] for r in all_train}) == 5000
    assert not ({r["note_sha256"] for r in all_train} & {r["note_sha256"] for r in v4_val_100})

    max_train_tok = max(r["total_tokens"] for r in all_train)
    assert max_train_tok <= 1651, f"Max total_tokens {max_train_tok} exceeds 1,651 T4 FP32 watermark!"

    splits = {"train": all_train, "validation": v4_val_100}
    hashes = {s: digest(rows) for s, rows in splits.items()}
    cfg = {
        "schema_version": 3,
        "label_version": "v4_5000_regenerated_gemini_3_8_flash_cleaned",
        "schema": SCHEMA,
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "dataset": DATASET_ID,
        "dataset_revision": DATASET_REVISION,
        "seed": 42,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "transformers": importlib.metadata.version("transformers"),
        "datasets": importlib.metadata.version("datasets"),
        "source_v4_1325_version": "ca7b6e90c1019441",
        "source_v2_5000_version": "3f8f10951130896b",
        "teacher_model": "gemini-3.8-flash",
    }
    version = digest({"config": cfg, "splits": hashes})[:16]
    pkg_dir = ROOT / "prepared_clinical_dataset" / version
    pkg_dir.mkdir(parents=True, exist_ok=True)
    DatasetDict({s: Dataset.from_list(rows) for s, rows in splits.items()}).save_to_disk(str(pkg_dir / "dataset"))
    for s, rows in splits.items():
        (pkg_dir / f"{s}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    manifest = {
        "version": version,
        "config": cfg,
        "split_sha256": hashes,
        "counts": {"train": len(all_train), "validation": len(v4_val_100)},
        "lengths": {
            s: {
                "max": max(r["total_tokens"] for r in rows),
                "mean": sum(r["total_tokens"] for r in rows) / len(rows),
                "mean_supervised": sum(r["supervised_tokens"] for r in rows) / len(rows),
                "max_supervised": max(r["supervised_tokens"] for r in rows),
            }
            for s, rows in splits.items()
        },
        "total_supervised_tokens_per_epoch": sum(r["supervised_tokens"] for r in all_train),
        "total_supervised_tokens_3_epochs": 3 * sum(r["supervised_tokens"] for r in all_train),
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "prepared_clinical_dataset/latest_v4_5000.json").write_text(json.dumps({"version": version}, indent=2), encoding="utf-8")
    print(f"PACKAGED V4-5000: version={version}, max_train_tokens={max_train_tok}, val_sha={hashes['validation']}", flush=True)


def run_batch(out_dir: Path, model: str, poll_seconds: int, resume: bool):
    from google.genai import types
    client = get_gemini_client()
    job_path = out_dir / "batch_job.json"
    if resume:
        batch_job = client.batches.get(name=read_json(job_path)["job_name"])
    else:
        req_path, _ = assemble_extra_batch(out_dir)
        uploaded = client.files.upload(file=str(req_path), config=types.UploadFileConfig(display_name="v4-5000-extra-3675-regen", mime_type="jsonl"))
        batch_job = client.batches.create(model=model, src=uploaded.name, config=types.CreateBatchJobConfig(display_name="v4-5000-extra-3675-regen"))
        save_job_state(job_path, batch_job, model)
        print(f"[{now_str()}] Batch started! Job={batch_job.name}", flush=True)

    terminal = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}
    while True:
        state = save_job_state(job_path, batch_job, model)
        print(f"[{now_str()}] Batch {batch_job.name} state={state}", flush=True)
        if state in terminal:
            break
        time.sleep(poll_seconds)
        batch_job = client.batches.get(name=batch_job.name)
    if state != "JOB_STATE_SUCCEEDED":
        raise RuntimeError(f"Batch failed: {state}")
    process_and_finalize(client, batch_job, out_dir)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--poll-interval", type=int, default=300)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--resume", action="store_true")
    g.add_argument("--package-only", action="store_true")
    args = p.parse_args()
    if args.package_only:
        package_from_regenerated(args.out_dir)
    elif args.run or args.resume:
        run_batch(args.out_dir, args.model, args.poll_interval, resume=args.resume)
    else:
        assemble_extra_batch(args.out_dir)
