"""One-off local CLI for Gemma 3 270M baseline or V4-1325 LoRA adapter."""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessorList

from clinical_sft.common import strip_fences
from scripts.run_v4_100_gen_rp1 import GeneratedOnlyRepetitionPenalty

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT = ROOT / "results_v4/baseline/comparison_contract.json"
DEFAULT_ADAPTER = ROOT / "results_v4/finetuned_v4/adapter"
V4_5000_ADAPTER = ROOT / "results_v4_5000/finetuned_v4_5000/adapter"
DEFAULT_ENV_FILE = ROOT / ".env.local"
DEFAULT_SYSTEM = (
    "Extract only clinical facts explicitly stated in the supplied note into one JSON object. "
    "Return JSON only, without markdown or commentary. Preserve negation, uncertainty, "
    "historical versus current events, and which findings or doses belong to each event or drug. "
    "Do not infer missing facts or complete cut-off text. Include all ten top-level fields. "
    "The allowed fields and types are: visit motivation is a string; admission is an array of "
    "objects with optional fields reason; patient information is an object with optional fields "
    "age, sex; patient medical history is an object with optional fields physiological context; "
    "surgeries is an array of objects with optional fields Type, time, details; symptoms is an "
    "array of objects with optional fields name of symptom, location, time, details; medical "
    "examinations is an array of objects with optional fields name, result; diagnosis tests is an "
    "array of objects with optional fields test, result; treatments is an array of objects with "
    "optional fields name, dosage, time, reaction to treatment; discharge is an object with "
    "optional fields discharge summary. Use [] for empty arrays, {} for empty objects, and "
    "\"None\" for absent visit motivation. Omit missing inner fields. Do not add other keys or "
    "repeat identical entries.\n\nClinical note:\n"
)


def format_output(text: str) -> str:
    """Strip markdown code fences and pretty-print JSON when valid."""
    cleaned = strip_fences(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return cleaned
    return json.dumps(parsed, ensure_ascii=False, indent=2)


def build_prompt(tokenizer, raw_input: str, *, is_raw: bool = False) -> str:
    """Use raw prompt as-is if already templated; otherwise wrap note with v4 system prompt."""
    if is_raw or "<start_of_turn>user" in raw_input:
        return raw_input
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": f"{DEFAULT_SYSTEM}{raw_input.strip()}"}],
        tokenize=False,
        add_generation_prompt=True,
    )


def resolve_hf_token(env_file: Path = DEFAULT_ENV_FILE) -> str | None:
    """Return HF_TOKEN from environment or .env.local without logging it."""
    for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            k, v = stripped.split("=", 1)
            if k.strip() in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
                return v.strip().strip('"').strip("'")
    return None


def download_model_to_cache(contract_path: Path, token: str | None) -> Path:
    """Download the contracted base model revision into the local Hugging Face cache."""
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    local_dir = snapshot_download(
        repo_id=contract["model"],
        revision=contract["base_model_revision"],
        token=token,
    )
    return Path(local_dir)


def load_model(contract_path: Path, adapter_path: Path, mode: str, token: str | None):
    """Load base Gemma 3 model (and V4 LoRA adapter when mode='finetuned') on CUDA or CPU."""
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    device = "cuda" if torch.cuda.is_available() else "cpu"

    random.seed(contract["seed"])
    torch.manual_seed(contract["seed"])

    tokenizer = AutoTokenizer.from_pretrained(
        contract["model"],
        revision=contract["base_model_revision"],
        token=token,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        contract["model"],
        revision=contract["base_model_revision"],
        token=token,
        dtype=torch.float32,
    ).to(device)
    if mode == "baseline":
        return base_model.eval(), tokenizer, contract, device
    model = PeftModel.from_pretrained(base_model, str(adapter_path), is_trainable=False).eval()
    return model, tokenizer, contract, device


def generate_once(model, tokenizer, prompt_text: str, max_new_tokens: int, device: str, mode: str):
    """Run baseline (gen_rp=1.08) or finetuned (gen_rp=1.00_fb1.08) greedy decoding."""
    pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    inputs = tokenizer(prompt_text, return_tensors="pt", add_special_tokens=False).to(device)
    n_prompt = inputs.input_ids.shape[1]

    with torch.inference_mode():
        if mode == "baseline":
            out = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=pad_id,
                logits_processor=LogitsProcessorList([GeneratedOnlyRepetitionPenalty(1.08, n_prompt)]),
            )
            ids = out[0, n_prompt:].tolist()
            fallback = False
        else:
            out_rp1 = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=pad_id,
            )
            ids = out_rp1[0, n_prompt:].tolist()
            fallback = False
            if len(ids) >= max_new_tokens:
                fallback = True
                out_fb = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    pad_token_id=pad_id,
                    logits_processor=LogitsProcessorList([GeneratedOnlyRepetitionPenalty(1.08, n_prompt)]),
                )
                ids = out_fb[0, n_prompt:].tolist()

    text = tokenizer.decode(ids, skip_special_tokens=True)
    return text, len(ids), fallback


def read_user_input(args) -> str:
    if args.prompt is not None:
        return args.prompt
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Paste clinical note or prompt, then press Ctrl+Z + Enter (Windows) or Ctrl+D (Unix):", file=sys.stderr)
    return sys.stdin.read()


def main():
    parser = argparse.ArgumentParser(
        description="Run one-off inference with Gemma 3 270M (baseline gen_rp=1.08, finetuned V4, or V4-5000 gen_rp=1.00_fb1.08)."
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=("finetuned", "v4-5000", "baseline"),
        default="finetuned",
        help="Run V4-1325 LoRA (default), V4-5000 LoRA, or unadapted baseline.",
    )
    parser.add_argument("-p", "--prompt", help="Inline clinical note or full prompt text.")
    parser.add_argument("-f", "--file", help="Path to a text file containing the clinical note or prompt.")
    parser.add_argument("--raw", action="store_true", help="Send input verbatim without wrapping in the v4 clinical prompt.")
    parser.add_argument("--download-only", action="store_true", help="Download and cache the base model, then exit.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT, help="Path to comparison_contract.json.")
    parser.add_argument("--adapter", type=Path, default=None, help="Override LoRA adapter directory.")
    args = parser.parse_args()

    adapter_path = args.adapter or (V4_5000_ADAPTER if args.mode == "v4-5000" else DEFAULT_ADAPTER)

    token = resolve_hf_token()
    if args.download_only:
        t0 = time.monotonic()
        cache_path = download_model_to_cache(args.contract, token)
        print(f"Model cached at {cache_path} in {time.monotonic() - t0:.1f}s.", file=sys.stderr)
        return

    raw_input = read_user_input(args)
    if not raw_input.strip():
        parser.error("Input is empty.")

    t0 = time.monotonic()
    target_desc = "baseline (no adapter)" if args.mode == "baseline" else f"{args.mode} ({adapter_path})"
    print(f"Loading {target_desc}...", file=sys.stderr)
    model, tokenizer, contract, device = load_model(args.contract, adapter_path, args.mode, token)
    print(f"Loaded on {device} in {time.monotonic() - t0:.1f}s.", file=sys.stderr)

    prompt_text = build_prompt(tokenizer, raw_input, is_raw=args.raw)
    t1 = time.monotonic()
    output_text, n_tokens, fallback = generate_once(
        model, tokenizer, prompt_text, int(contract["max_new_tokens"]), device, args.mode
    )
    print(
        f"Generated {n_tokens} tokens in {time.monotonic() - t1:.1f}s (mode={args.mode}, fallback_1.08={fallback}).",
        file=sys.stderr,
    )
    print(format_output(output_text))


if __name__ == "__main__":
    main()
