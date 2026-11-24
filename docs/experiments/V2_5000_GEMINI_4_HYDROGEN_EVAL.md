# Full-Schema v2 / 5,000 — Gemini 4 Hydrogen Evaluation (`8993a8dd5f5f3a18`)

This document records the standalone local DeepEval evaluation of the `v2_5000` full-schema run using **Gemini 4 Hydrogen** (`gemini-4-hydrogen`) on the same 100 frozen validation cases.

## Run Metadata

| Field | Value |
| :--- | :--- |
| **Run ID** | `8993a8dd5f5f3a18` |
| **Backend / Model** | `gemini` / `gemini-4-hydrogen` |
| **Rubric** | `source_grounded_v2` |
| **Truth Source** | `input clinical note` (source-grounded, treating synthetic references as secondary) |
| **Cases / Measurements** | 100 frozen validation cases · 200 paired test cases · 400 measurements |
| **Status** | Complete (`complete: true`) |

## Results Summary

| Metric | Baseline Mean | Fine-Tuned Mean | Mean Paired Delta | Wins / Ties / Losses | 100k Paired BCa 95% CI |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Source fidelity** | `0.386` | `0.539` | `+0.153` | `68W / 21T / 11L` | `[+0.115, +0.190]` |
| **Source coverage** | `0.412` | `0.550` | `+0.138` | `69W / 17T / 14L` | `[+0.101, +0.175]` |

## Artifacts

- [Summary JSON](../../results_v2_5000/deepeval_100/judgments/8993a8dd5f5f3a18/summary.json)
- [Paired Comparison CSV](../../results_v2_5000/deepeval_100/judgments/8993a8dd5f5f3a18/paired_comparison.csv)
- [Scores and Reasons JSON](../../results_v2_5000/deepeval_100/judgments/8993a8dd5f5f3a18/scores.json)
- [Run Contract JSON](../../results_v2_5000/deepeval_100/judgments/8993a8dd5f5f3a18/run_contract.json)
- [Progress JSON](../../results_v2_5000/deepeval_100/judgments/8993a8dd5f5f3a18/progress.json)

## Related Documentation

- [V2_5000_SESSION_HANDOFF.md](V2_5000_SESSION_HANDOFF.md)
- [FULL_SCHEMA_V2_5000_RUN.md](FULL_SCHEMA_V2_5000_RUN.md)
- [SLM_Clinical_Extraction_Overview.html](../SLM_Clinical_Extraction_Overview.html)
