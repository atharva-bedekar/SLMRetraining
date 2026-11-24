# Clinical JSON extraction fine-tuning

Reproducible FP32 LoRA experiments with `google/gemma-3-270m-it`, extracting clinical notes into ten-section JSON. The latest completed experiment is **v4-5000: 5,000 regenerated training examples, reduced 30-path schema, `gen_rp=1.00_fb1.08` decoding, and 100 frozen development cases**.

Start with the [session handoff](docs/SESSION_HANDOFF.md), [v4-1325 & v4-5000 report](docs/experiments/V4_5000_RUN.md), [documentation index](docs/README.md), and [run catalog](docs/experiments/RUN_CATALOG.md).

## Current results

| Same 100 development cases | Base (`gen_rp_1.08`) | `v4-1325` (`gen_rp_1.00_fb1.08`) | `v4-5000` (`gen_rp_1.00_fb1.08`) |
| --- | ---: | ---: | ---: |
| Raw-valid JSON | 0/100 | 92/100 | **98/100** |
| Allowed keys and types | 0/100 | 86/100 | **97/100** |
| Mean strict reference fact F1 | 1.45% | 29.41% | **40.17%** |
| Mean soft reference fact F1 | 4.10% | 42.03% | **55.27%** |
| Source fidelity (`gemini-4-hydrogen`) | 0.323 | 0.537 | **0.619** |
| Source coverage (`gemini-4-hydrogen`) | 0.357 | 0.561 | **0.625** |

Generation and all 400 `source_grounded_v2` measurements are complete for both `v4-1325` (`f8c214409451ed92`) and `v4-5000` (`2f58650627fa8d6a`). On `v4-5000`, paired BCa bootstrap 95% CIs vs. base are `[+0.259, +0.331]` for fidelity (93W/3T/4L) and `[+0.235, +0.298]` for coverage (95W/2T/3L). These are development results against regenerated references and LLM source-consistency judgments, not clinician-adjudicated accuracy.

## Repository map

| Location | Purpose |
| --- | --- |
| [clinical_sft/](clinical_sft/) | Separate standalone CLI pilot pipeline |
| [scripts/](scripts/README.md) | Preparation, evaluation, audit, report, Colab, and local inference CLI (`infer_v4_cli.py`) |
| [notebooks/](notebooks/README.md) | `v4_5000`, `v4_1325`, `v3_1325`, `v2_5000`, and `v2` workflows |
| [prepared_clinical_dataset/](prepared_clinical_dataset/README.md) | Frozen dataset manifests (large regenerated datasets are gitignored) |
| [results_v4_5000/](results_v4_5000/) | Latest `v4-5000` adapter, checkpoints, generation, and `gemini-4-hydrogen` eval |
| [results_v4/](results_v4/) | `v4-1325` adapter, checkpoints, decoding ablations, and `gemini-4-hydrogen` eval |
| [results_v3/](results_v3/README.md) | Preserved `v3-1325` training, generation, semantic evaluation, and 100-case audit |
| [results_v2_5000/](results_v2_5000/README.md) | Preserved full-schema 5,000-example experiment |
| [results_v2/](results_v2/README.md) | Preserved full-schema 30-case experiment |
| [docs/](docs/README.md) | Handoff, experiment reports, guides, protocols, and HTML overview |
| [input.md](input.md) | Demo clinical notes and reference outputs for local CLI testing |
| [archive/](archive/README.md) | Older docs, planning evidence, prompts, notebooks, and pilots |
| [tests/](tests/) | Offline unit tests |

Frozen artifact paths and provenance-hashed execution sources stay stable. Current and historical artifacts are cataloged without rewriting saved predictions, labels or contracts.

## Run and verify

The primary workflow is [notebooks/v3_1325/](notebooks/v3_1325/), in numbered order. See the [experiment protocol](docs/experiments/REDUCED_SCHEMA_1325_RUN.md) and [dataset/cleaning guide](docs/data/README.md). Preparation requires the ML dependencies and Hugging Face access to Gemma; model execution needs a suitable GPU. The project `pyproject.toml`/`uv.lock` describe a different dependency stack from the recorded Colab runs; use notebook setup cells for reproduction.

The separate CLI workflow uses [requirements-clinical.txt](requirements-clinical.txt) and its [guide](docs/guides/CLINICAL_PIPELINE.md). Its data and contracts are not interchangeable with notebook artifacts. Judge dependencies are isolated in [requirements-deepeval.txt](requirements-deepeval.txt); execution requires explicit runner flags. Gemini remains disabled.

From the repository root, offline checks require no GPU or model downloads:

```bash
python -m unittest discover -s tests -v
python -m scripts.check_remaining_validation
```

On this Windows workspace, use `.venv/Scripts/python.exe` if the system Python alias is unavailable.
