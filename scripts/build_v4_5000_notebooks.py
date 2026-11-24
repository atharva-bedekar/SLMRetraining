"""Build isolated notebooks and baseline for V4-5000 (0d520299c998a045) training and gen_rp=1.00_fb1.08 evaluation."""
import copy
import json
import shutil
from pathlib import Path

from scripts.build_v4_notebooks import digest, score_run_records

ROOT = Path(__file__).resolve().parents[1]


def prepare_baseline(root=ROOT):
    version = json.loads((root / "prepared_clinical_dataset/latest_v4_5000.json").read_text(encoding="utf-8"))["version"]
    pdir = root / "prepared_clinical_dataset" / version
    manifest = json.loads((pdir / "manifest.json").read_text(encoding="utf-8"))
    val_rows = [json.loads(l) for l in (pdir / "validation.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()]
    v4_contract = json.loads((root / "results_v4/baseline/comparison_contract.json").read_text(encoding="utf-8"))

    assert manifest["split_sha256"]["validation"] == v4_contract["validation_sha256"]
    assert [c["case_id"] for c in val_rows] == v4_contract["case_ids"]
    assert digest([c["prompt_text"] for c in val_rows]) == v4_contract["prompt_sha256"]

    baseline_dir = root / "results_v4_5000/baseline"
    cond_dir = baseline_dir / "gen_rp_1.08"
    cond_dir.mkdir(parents=True, exist_ok=True)

    contract = copy.deepcopy(v4_contract)
    contract["dataset_version"] = version
    contract["train_sha256"] = manifest["split_sha256"]["train"]
    contract["validation_sha256"] = manifest["split_sha256"]["validation"]
    (baseline_dir / "comparison_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")

    selection = [{"case_id": c["case_id"], "note": c["note"], "reference": c["reference"], "prompt_text": c["prompt_text"]} for c in val_rows]
    (baseline_dir / "selection.json").write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.copy2(root / "results_v4/baseline/gen_rp_1.08/generations.json", cond_dir / "generations.json")
    shutil.copy2(root / "results_v4/baseline/gen_rp_1.08/generation_diagnostics.json", cond_dir / "generation_diagnostics.json")
    shutil.copy2(root / "results_v4/baseline/gen_rp_1.08/per_case.csv", cond_dir / "per_case.csv")
    shutil.copy2(root / "results_v4/baseline/gen_rp_1.08/aggregate.json", cond_dir / "aggregate.json")
    shutil.copy2(root / "results_v4/baseline/summary_metrics.csv", baseline_dir / "summary_metrics.csv")
    shutil.copy2(root / "results_v4/baseline/summary_metrics.json", baseline_dir / "summary_metrics.json")
    return contract


def build_notebooks(root=ROOT):
    dest = root / "notebooks/v4_5000"
    dest.mkdir(parents=True, exist_ok=True)

    # 1. 01_baseline_eval.ipynb (derive from clean v3_1325 source)
    nb01 = copy.deepcopy(json.loads((root / "notebooks/v3_1325/01_baseline_eval.ipynb").read_text(encoding="utf-8")))
    install = '%pip install -q "transformers==4.57.6" "datasets==4.8.5" "peft==0.18.1" "accelerate==1.15.0" pandas huggingface_hub nbclient nbformat\n'
    import re
    for c in nb01["cells"]:
        src = "".join(c["source"])
        src = src.replace("/content/clinical_v3", "/content/clinical_v4_5000")
        src = src.replace("/content/results_v3", "/content/clinical_v4_5000/results_v4_5000")
        src = src.replace("results_v3", "results_v4_5000")
        src = src.replace("latest_v3.json", "latest_v4_5000.json")
        src = src.replace(
            'for split, sha in manifest["split_sha256"].items():\n    assert digest(prepared[split].to_list()) == sha',
            'for split, sha in manifest["split_sha256"].items():\n    rows_chk = [json.loads(l) for l in (prepared_dir / f"{split}.jsonl").read_text(encoding="utf-8").split("\\n") if l.strip()]\n    assert digest(rows_chk) == sha',
        )
        if c["cell_type"] == "code":
            if src.startswith("%pip install"):
                src = install
            src = re.sub(
                r'for package in \("transformers", "datasets"\):\n\s+assert importlib\.metadata\.version\(package\) == cfg\[package\], \(\n\s+f"\{package\} mismatch: \{importlib\.metadata\.version\(package\)\} vs \{cfg\[package\]\}"\n\s+\)',
                'assert importlib.metadata.version("transformers") == "4.57.6"',
                src,
            )
            c.update(outputs=[], execution_count=None)
            if not src.startswith("%"):
                compile(src, str(dest / "01_baseline_eval.ipynb"), "exec")
        c["source"] = src.splitlines(keepends=True)
    (dest / "01_baseline_eval.ipynb").write_text(json.dumps(nb01, indent=1, ensure_ascii=False), encoding="utf-8")

    # 2. 02_finetune.ipynb (5,000 rows, 3 epochs -> 1,875 optimizer steps)
    nb02 = copy.deepcopy(json.loads((root / "notebooks/v3_1325/02_finetune.ipynb").read_text(encoding="utf-8")))
    for c in nb02["cells"]:
        src = "".join(c["source"])
        src = src.replace("/content/clinical_v3", "/content/clinical_v4_5000")
        src = src.replace("/content/results_v3", "/content/clinical_v4_5000/results_v4_5000")
        src = src.replace("results_v3", "results_v4_5000")
        src = src.replace("finetuned_v3", "finetuned_v4_5000")
        src = src.replace("latest_v3.json", "latest_v4_5000.json")
        src = src.replace(
            'for split, sha in manifest["split_sha256"].items():\n    assert digest(prepared[split].to_list()) == sha',
            'for split, sha in manifest["split_sha256"].items():\n    rows_chk = [json.loads(l) for l in (prepared_dir / f"{split}.jsonl").read_text(encoding="utf-8").split("\\n") if l.strip()]\n    assert digest(rows_chk) == sha',
        )
        if c["cell_type"] == "code":
            if src.startswith("%pip install"):
                src = install
            if "loss = model(**batch).loss" in src:
                start = src.index("loss = model(**batch).loss")
                end = src.index("model_check = {", start)
                src = (
                    src[:start]
                    + """def backward_check():
    loss = model(**batch).loss
    assert torch.isfinite(loss), "Non-finite initial loss"
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
    assert grads and all(bool(torch.isfinite(g).all()) for g in grads), "Non-finite gradients"
    return loss, grads

try:
    loss, grads = backward_check()
except torch.cuda.OutOfMemoryError:
    model.zero_grad(set_to_none=True)
    torch.cuda.empty_cache()
    GRADIENT_CHECKPOINTING = True
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    torch.cuda.reset_peak_memory_stats()
    loss, grads = backward_check()
"""
                    + src[end:]
                )
            src = src.replace("save_total_limit=2,", "save_total_limit=3,")
            src = src.replace(
                "class SaveProgress(TrainerCallback):",
                """class SaveLiveLog(TrainerCallback):
    def on_log(self, args, state, control, **kwargs):
        pending = OUTPUT_DIR / "training_log.pending"
        pending.write_text(json.dumps(state.log_history, indent=2), encoding="utf-8")
        pending.replace(OUTPUT_DIR / "training_log.json")

class SaveProgress(TrainerCallback):""",
            )
            src = src.replace("callbacks=[SaveProgress()],", "callbacks=[SaveProgress(), SaveLiveLog()],")
            src = src.replace(
                "result = trainer.train()",
                """from transformers.trainer_utils import get_last_checkpoint
last_checkpoint = get_last_checkpoint(str(OUTPUT_DIR / "checkpoints")) if (OUTPUT_DIR / "checkpoints").exists() else None
result = trainer.train(resume_from_checkpoint=last_checkpoint)
assert trainer.state.global_step == 1875 and trainer.state.epoch == 3.0""",
            )
            src = src.replace(
                '    shutil.rmtree(OUTPUT_DIR / "checkpoints")',
                '    print("Retaining resumable checkpoints (625, 1250, 1875) until local archival is verified.")',
            )
            c.update(outputs=[], execution_count=None)
            if not src.startswith("%"):
                compile(src, str(dest / "02_finetune.ipynb"), "exec")
        c["source"] = src.splitlines(keepends=True)
    (dest / "02_finetune.ipynb").write_text(json.dumps(nb02, indent=1, ensure_ascii=False), encoding="utf-8")

    # 3. 03_eval_and_compare.ipynb (100 frozen cases using gen_rp=1.00_fb1.08 + schema_violations + archive)
    nb03 = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": nb02["metadata"],
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# V4-5000 Evaluation (`gen_rp=1.00_fb1.08`)\nEvaluate all 100 frozen validation cases on `finetuned_v4_5000`."]},
            {"cell_type": "code", "execution_count": None, "outputs": [], "metadata": {}, "source": ['%pip install -q "transformers==4.57.6" "datasets==4.8.5" "peft==0.18.1" "accelerate==1.15.0" pandas huggingface_hub\n']},
            {
                "cell_type": "code",
                "execution_count": None,
                "outputs": [],
                "metadata": {},
                "source": """import json, os, random, shutil, time
from pathlib import Path
import pandas as pd
import torch
from datasets import load_from_disk
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessor, LogitsProcessorList

os.chdir("/content/clinical_v4_5000")
import sys
sys.path.insert(0, str(Path.cwd()))
from scripts.build_v4_notebooks import digest, find_schema_violations, score_run_records

class GeneratedOnlyRepetitionPenalty(LogitsProcessor):
    def __init__(self, penalty: float, prompt_length: int):
        self.penalty = float(penalty)
        self.prompt_length = int(prompt_length)
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        if self.penalty == 1.0 or input_ids.shape[1] <= self.prompt_length:
            return scores
        gen_ids = input_ids[:, self.prompt_length :]
        if gen_ids.shape[0] == 1:
            gen_ids = torch.unique(gen_ids[0]).unsqueeze(0)
        score = torch.gather(scores, 1, gen_ids)
        score = torch.where(score < 0, score * self.penalty, score / self.penalty)
        return scores.scatter(1, gen_ids, score)

root = Path.cwd()
contract = json.loads((root / "results_v4_5000/baseline/comparison_contract.json").read_text(encoding="utf-8"))
pdir = root / "prepared_clinical_dataset" / contract["dataset_version"]
cases = load_from_disk(str(pdir / "dataset"))["validation"].to_list()
assert [c["case_id"] for c in cases] == contract["case_ids"]
assert digest([c["prompt_text"] for c in cases]) == contract["prompt_sha256"]

out_dir = root / "results_v4_5000/comparison/finetuned_v4_5000__gen_rp_1.00"
out_dir.mkdir(parents=True, exist_ok=True)
gen_path, diag_path, raw_path = out_dir / "generations.json", out_dir / "generation_diagnostics.json", out_dir / "raw_rp1_generations.json"
generations = json.loads(gen_path.read_text(encoding="utf-8")) if gen_path.exists() else {}
diagnostics = json.loads(diag_path.read_text(encoding="utf-8")) if diag_path.exists() else {}
raw_gens = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}

token = os.environ.get("HF_TOKEN")
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained(contract["model"], revision=contract["base_model_revision"], token=token)
pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id
random.seed(contract["seed"])
torch.manual_seed(contract["seed"])
base_m = AutoModelForCausalLM.from_pretrained(contract["model"], revision=contract["base_model_revision"], token=token, dtype=torch.float32).to(device)
model = PeftModel.from_pretrained(base_m, str(root / "results_v4_5000/finetuned_v4_5000/adapter"), is_trainable=False).eval()
eos = model.generation_config.eos_token_id
eos_ids = eos if isinstance(eos, list) else [eos]
max_new = int(contract["max_new_tokens"])
started = time.monotonic()

for case in cases:
    key = case["case_id"]
    if generations.get(key, "").strip() and key in diagnostics:
        continue
    inputs = tokenizer(case["prompt_text"], return_tensors="pt", add_special_tokens=False).to(device)
    n_prompt = inputs.input_ids.shape[1]
    with torch.inference_mode():
        logits = model(**inputs, logits_to_keep=1).logits[:, -1, :]
        assert bool(torch.isfinite(logits).all().item())
        del logits
        out_rp1 = model.generate(**inputs, max_new_tokens=max_new, do_sample=False, pad_token_id=pad_id)
        ids_rp1 = out_rp1[0, n_prompt:].tolist()
        text_rp1 = tokenizer.decode(ids_rp1, skip_special_tokens=True)
        raw_gens[key] = text_rp1
        raw_path.write_text(json.dumps(raw_gens, ensure_ascii=False, indent=2), encoding="utf-8")
        hit_budget = len(ids_rp1) >= max_new
        fb_triggered = False
        final_ids, final_text = ids_rp1, text_rp1
        if hit_budget:
            fb_triggered = True
            out_fb = model.generate(
                **inputs, max_new_tokens=max_new, do_sample=False, pad_token_id=pad_id,
                logits_processor=LogitsProcessorList([GeneratedOnlyRepetitionPenalty(1.08, n_prompt)]),
            )
            final_ids = out_fb[0, n_prompt:].tolist()
            final_text = tokenizer.decode(final_ids, skip_special_tokens=True)
    diagnostics[key] = {
        "prompt_tokens": n_prompt, "rp1_generated_tokens": len(ids_rp1), "rp1_reached_budget": hit_budget,
        "fallback_to_gen_rp_1.08_triggered": fb_triggered, "generated_tokens": len(final_ids),
        "finite_first_token_logits": True, "empty_output": not final_text.strip(),
        "reached_budget": len(final_ids) >= max_new, "ended_with_eos": bool(final_ids) and final_ids[-1] in eos_ids,
    }
    diag_path.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    generations[key] = final_text
    gen_path.write_text(json.dumps(generations, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[finetuned_v4_5000 | gen_rp_1.00] {len(generations)}/100 {key}: rp1_toks={len(ids_rp1)}, fb={fb_triggered}, final={len(final_ids)} ({time.monotonic()-started:.1f}s)", flush=True)

df_fb, sum_fb = score_run_records(cases, generations, diagnostics)
sum_fb["fallback_triggered_cases"] = sum(1 for c in cases if diagnostics[c["case_id"]].get("fallback_to_gen_rp_1.08_triggered"))
df_fb.to_csv(out_dir / "per_case.csv", index=False)
(out_dir / "aggregate.json").write_text(json.dumps(sum_fb, indent=2), encoding="utf-8")
(out_dir / "schema_violations.json").write_text(json.dumps(find_schema_violations(cases, generations), indent=2), encoding="utf-8")

base_sum = json.loads((root / "results_v4_5000/baseline/gen_rp_1.08/aggregate.json").read_text(encoding="utf-8"))
summary_rows = [{"model": "base", "decoding": "gen_rp_1.08", **base_sum}, {"model": "finetuned_v4_5000", "decoding": "gen_rp_1.00_fb1.08", **sum_fb}]
pd.DataFrame(summary_rows).to_csv(root / "results_v4_5000/comparison/summary_comparison.csv", index=False)
(root / "results_v4_5000/comparison/summary_comparison.json").write_text(json.dumps(summary_rows, indent=2), encoding="utf-8")
archive = shutil.make_archive(str((root / "results_v4_5000/comparison").resolve()), "zip", root_dir=root / "results_v4_5000", base_dir="comparison")
print("V4-5000 COMPARISON COMPLETE:", json.dumps(sum_fb, indent=2), "archive=", archive, flush=True)
""".splitlines(keepends=True),
            },
        ],
    }
    compile("".join(nb03["cells"][2]["source"]), str(dest / "03_eval_and_compare.ipynb"), "exec")
    (dest / "03_eval_and_compare.ipynb").write_text(json.dumps(nb03, indent=1, ensure_ascii=False), encoding="utf-8")
    return dest


if __name__ == "__main__":
    c = prepare_baseline(ROOT)
    d = build_notebooks(ROOT)
    print(f"Prepared V4-5000 baseline (version={c['dataset_version']}) and notebooks at {d}")
