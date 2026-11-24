"""Run gen_rp=1.00_fb1.08 across all 100 frozen validation cases on the V4-1325 adapter."""
import json
import os
import random
import time
from pathlib import Path

import pandas as pd
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessor, LogitsProcessorList

from scripts.build_v4_notebooks import find_schema_violations, score_run_records


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


def main():
    root = Path("/content/clinical_v4_rp1")
    os.chdir(root)

    contract = json.loads((root / "results_v4/baseline/comparison_contract.json").read_text(encoding="utf-8"))
    val_path = root / "prepared_clinical_dataset/ca7b6e90c1019441/validation.jsonl"
    cases = [json.loads(line) for line in val_path.read_text(encoding="utf-8").split("\n") if line.strip()]
    assert [c["case_id"] for c in cases] == contract["case_ids"]

    out_dir = root / "results_v4/comparison/finetuned_v4__gen_rp_1.00"
    out_dir.mkdir(parents=True, exist_ok=True)
    gen_path = out_dir / "generations.json"
    diag_path = out_dir / "generation_diagnostics.json"
    raw_path = out_dir / "raw_rp1_generations.json"

    # Seed from the already-completed 20 cases if out_dir is empty
    seed_dir = root / "results_v4/comparison/finetuned_v4__gen_rp_1.00_20"
    if not gen_path.exists() and (seed_dir / "generations.json").exists():
        gen_path.write_text((seed_dir / "generations.json").read_text(encoding="utf-8"), encoding="utf-8")
        diag_path.write_text((seed_dir / "generation_diagnostics.json").read_text(encoding="utf-8"), encoding="utf-8")
        raw_path.write_text((seed_dir / "raw_rp1_generations.json").read_text(encoding="utf-8"), encoding="utf-8")

    generations = json.loads(gen_path.read_text(encoding="utf-8")) if gen_path.exists() else {}
    diagnostics = json.loads(diag_path.read_text(encoding="utf-8")) if diag_path.exists() else {}
    raw_gens = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}

    pending = [c for c in cases if not (generations.get(c["case_id"], "").strip() and c["case_id"] in diagnostics)]
    print(f"Resuming gen_rp=1.00_fb1.08 (100 cases): cached={len(cases)-len(pending)}, pending={len(pending)}", flush=True)

    if pending:
        token = os.environ.get("HF_TOKEN")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        assert device == "cuda"
        tokenizer = AutoTokenizer.from_pretrained(contract["model"], revision=contract["base_model_revision"], token=token)
        pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id
        random.seed(contract["seed"])
        torch.manual_seed(contract["seed"])
        base_m = AutoModelForCausalLM.from_pretrained(
            contract["model"], revision=contract["base_model_revision"], token=token, dtype=torch.float32
        ).to(device)
        model = PeftModel.from_pretrained(base_m, str(root / "results_v4/finetuned_v4/adapter"), is_trainable=False).eval()
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
                finite = bool(torch.isfinite(logits).all().item())
                del logits
                if not finite:
                    raise RuntimeError(f"Non-finite logits on {key}")
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
                        **inputs,
                        max_new_tokens=max_new,
                        do_sample=False,
                        pad_token_id=pad_id,
                        logits_processor=LogitsProcessorList([GeneratedOnlyRepetitionPenalty(1.08, n_prompt)]),
                    )
                    final_ids = out_fb[0, n_prompt:].tolist()
                    final_text = tokenizer.decode(final_ids, skip_special_tokens=True)

            diagnostics[key] = {
                "prompt_tokens": n_prompt,
                "rp1_generated_tokens": len(ids_rp1),
                "rp1_reached_budget": hit_budget,
                "fallback_to_gen_rp_1.08_triggered": fb_triggered,
                "generated_tokens": len(final_ids),
                "finite_first_token_logits": finite,
                "empty_output": not final_text.strip(),
                "reached_budget": len(final_ids) >= max_new,
                "ended_with_eos": bool(final_ids) and final_ids[-1] in eos_ids,
            }
            diag_path.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
            generations[key] = final_text
            gen_path.write_text(json.dumps(generations, ensure_ascii=False, indent=2), encoding="utf-8")
            print(
                f"[finetuned_v4 | gen_rp_1.00_100] {len(generations)}/100 {key}: rp1_toks={len(ids_rp1)}, fallback={fb_triggered}, final_toks={len(final_ids)} ({time.monotonic()-started:.1f}s)",
                flush=True,
            )

    # Score raw_rp1 and fb1.08 across all 100 cases
    raw_diags = {k: {**v, "generated_tokens": v["rp1_generated_tokens"], "reached_budget": v["rp1_reached_budget"]} for k, v in diagnostics.items()}
    _, sum_raw = score_run_records(cases, raw_gens, raw_diags)
    df_fb, sum_fb = score_run_records(cases, generations, diagnostics)
    sum_fb["fallback_triggered_cases"] = sum(1 for c in cases if diagnostics[c["case_id"]].get("fallback_to_gen_rp_1.08_triggered"))

    df_fb.to_csv(out_dir / "per_case.csv", index=False)
    (out_dir / "aggregate.json").write_text(json.dumps(sum_fb, indent=2), encoding="utf-8")
    (out_dir / "aggregate_raw_rp1.json").write_text(json.dumps(sum_raw, indent=2), encoding="utf-8")
    (out_dir / "schema_violations.json").write_text(json.dumps(find_schema_violations(cases, generations), indent=2), encoding="utf-8")
    print("COMPLETE 100-case gen_rp=1.00_fb1.08:", json.dumps(sum_fb, indent=2), flush=True)


if __name__ == "__main__":
    main()
