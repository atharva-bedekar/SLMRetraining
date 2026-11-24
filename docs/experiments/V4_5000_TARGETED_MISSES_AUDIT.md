# V4-5000 Targeted Misses Audit (`run_id: 2f58650627fa8d6a`)

- **Date:** 2026-11-24
- **Experiment:** `v4_regenerated_labels_5000_gen_rp_1.00_fb1.08`
- **Judge run:** `2f58650627fa8d6a` (`gemini-4-hydrogen`, `source_grounded_v2`, 100 paired validation cases, baseline reused from `8b852f1592dfcc99`)
- **Aggregate scores:** Source fidelity `0.323 → 0.619` (`+0.296`), Source coverage `0.357 → 0.625` (`+0.268`); `97/100` allowed-schema valid, `98/100` JSON valid, `1/100` reached 2048-token budget (`5/100` triggered `fb=1.08`).
- **Audit scope:** All **9 unique cases** across the 4 fidelity losses, 3 coverage losses (`validation:2654` is in both), and 3 non-schema/budget cases (`validation:937` is both non-schema and the sole budget hit).

---

## Executive Summary

| Root-cause bucket | Unique cases | Case IDs | Takeaway |
| :--- | :---: | :--- | :--- |
| **Relation / attribute misbinding (primary)** | **6 / 9** | `validation:816`, `validation:2775`, `validation:2654`, `validation:933`, `validation:2510`, `validation:2890` | **Dominant failure mode** — accounts for **4/4 fidelity losses**, **2/3 coverage losses**, and the only fidelity-poor non-schema case (`validation:2890`). |
| **Truncation / premature EOS (high fidelity)** | **2 / 9** | `validation:937`, `validation:2308` | Both scored **0.8 fidelity**; `validation:937` hit the 2048-token budget in a repetition loop even after `fb=1.08`, and `validation:2308` emitted a premature EOS at 247 tokens right after `surgeries`. |
| **Minor omission + baseline verbatim-copy artifact** | **1 / 9** | `validation:1193` | V4-5000 is strong (`0.8` / `0.8`, valid schema); baseline scored `0.9` coverage by copying the entire note verbatim into `"visit motivation"`. |
| **Pure schema key slip (isolated)** | **0 / 9** | *(only `validation:2890` has a disallowed key)* | `validation:2890`'s single disallowed key (`treatments[3].details`) is a side effect of misbinding a fall event into `treatments`. |

> **Judge artifact on `validation:933`:** V4-5000's `0.0` fidelity score is a **judge thought-leak/parse failure** in `scores.json` (`"Wait - do not include extra text! Let me output only JSON cleanly..."`), not a true `0.0`. The output still has substantive misbindings (detailed below), but true fidelity losses vs. baseline are effectively **3, not 4**.

---

## Case-by-Case Summary Table

| Case ID | Buckets | Fid (B → FT, Δ) | Cov (B → FT, Δ) | Tokens / EOS / Schema | Primary Failure Mode |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `validation:816` | Fidelity loss | `0.8 → 0.5` (`-0.3`) | `0.4 → 0.6` (`+0.2`) | 581 / EOS / Valid | Relation/attribute misbinding |
| `validation:2775` | Fidelity loss | `0.6 → 0.5` (`-0.1`) | `0.4 → 0.6` (`+0.2`) | 649 / EOS / Valid | Relation/attribute misbinding (timeline & entity cross-wiring) |
| `validation:2654` | Fidelity + Coverage loss | `0.9 → 0.6` (`-0.3`) | `1.0 → 0.6` (`-0.4`) | 540 / EOS / Valid | Relation/attribute misbinding + missing facts *(baseline verbatim-copy)* |
| `validation:933` | Fidelity loss | `0.2 → 0.0` (`-0.2`) | `0.3 → 0.5` (`+0.2`) | 489 / EOS / Valid | Judge thought-leak (`0.0` artifact) + relation/attribute misbinding & missing facts |
| `validation:1193` | Coverage loss | `0.8 → 0.8` (`+0.0`) | `0.9 → 0.8` (`-0.1`) | 527 / EOS / Valid | Minor omission (1 trailing sentence) + baseline verbatim-copy artifact |
| `validation:2510` | Coverage loss | `0.3 → 0.4` (`+0.1`) | `0.5 → 0.4` (`-0.1`) | 371 / EOS / Valid | Relation/attribute misbinding (1-step timeline shift) + missing facts |
| `validation:937` | Non-schema + Budget (`fb=1.08`) | `0.3 → 0.8` (`+0.5`) | `0.3 → 0.6` (`+0.3`) | 2048 / Budget / Invalid | Repetition-loop truncation (`max_5gram=159`, unterminated string) |
| `validation:2890` | Non-schema | `0.3 → 0.4` (`+0.1`) | `0.3 → 0.5` (`+0.2`) | 682 / EOS / Invalid | Severe relation/attribute misbinding + 1 disallowed key (`treatments[3].details`) |
| `validation:2308` | Non-schema | `0.3 → 0.8` (`+0.5`) | `0.3 → 0.4` (`+0.1`) | 247 / EOS / Invalid | Premature EOS / structural JSON truncation after `surgeries` |

---

## 1. The 4 Fidelity Losses

### `validation:816` — Fid `0.8 → 0.5` (`-0.3`), Cov `0.4 → 0.6` (`+0.2`)
- **Format:** Valid JSON & schema, 581 tokens, clean EOS.
- **Primary cause:** **Relation/attribute misbinding** (+ secondary omissions of late-note facts).
- **Specific errors:**
  - *Test→result over-broadcasting:* Input states `"thyroid profile, cortisol level, vitamin B12, and ammonia levels were checked... and she was found to have elevated ammonia at 142"`. Output marks `Thyroid profile`, `cortisol level`, `vitamin B12`, and `ammonia levels` all `"elevated"`. Similarly marks `serum levels of vitamins` and `essential minerals` `"deficient"` without support while omitting `zinc`.
  - *Surgery/chronology merge:* Merges 1-month-prior `"revision surgery on her gastric bypass for anastomotic bleeding"` with 4-year-prior `"gastric surgery"` into `gastric bypass` (`four years prior`, `for anastomotic bleeding`) and invents `"rehabilitation surgery performed four years prior"` from `"rehabilitation center"`.
  - *Drug→reaction misbinding:* Attaches `"reaction to treatment": "normal renal function"` to `lactulose` and `rifaximin` (stolen from the CRRT sentence instead of `"progressive hyperammonemia to 432 mmol/L, despite treatment"`).
  - *Role/attribute slip:* Lists `"neurological assessment"` in `symptoms`; puts `"from a rehabilitation center after having been discharged a month earlier"` in symptom `time`.
- **Baseline context:** Baseline only extracted the first half of the note verbatim (coverage `0.4`), avoiding errors in the dense second half.

### `validation:2775` — Fid `0.6 → 0.5` (`-0.1`), Cov `0.4 → 0.6` (`+0.2`)
- **Format:** Valid JSON & schema, 649 tokens, clean EOS.
- **Primary cause:** **Relation/attribute misbinding (heavy timeline & entity cross-wiring).**
- **Specific errors:**
  - *Date cross-wiring:* Assigns the staging CT date (`25 November 2013`) to both `radiotherapy` (Jan–Feb 2014) and `doxorubicin` (Mar–Jul 2014); dates liver metastases in history to doxorubicin's dates (`19 March 2014 – 2 July 2014`, actually `30 April 2015`).
  - *Comorbidity→surgery halluciation:* Turns `"struma resection in 1990, and diverticulosis of the colon"` into surgeries `{"Type":"diverticulosis","time":"1990"}` and `{"Type":"surgery","time":"1990","details":"for diverticulosis of the colon"}`.
  - *Test→result merge:* Attaches MRI finding (`6 liver metastases between 1 and 14 mm`, 11 May 2015) to `CT of the abdomen` (30 April 2015) and omits MRI.
  - *Drug/role misbinding:* Duplicates pazopanib under `"name": "radiotherapy", "dosage": "oral therapy with pazopanib"`; places `abdominal sonography` under `symptoms`.
- **Baseline context:** Baseline stopped before the oncology timeline (coverage `0.4`).

### `validation:2654` — Fid `0.9 → 0.6` (`-0.3`), Cov `1.0 → 0.6` (`-0.4`) *(also a Coverage Loss)*
- **Format:** Valid JSON & schema, 540 tokens, clean EOS.
- **Primary cause:** **Relation/attribute misbinding + Missing facts** (amplified by baseline verbatim-copying).
- **Specific errors:**
  - *Event-status/polarity flip:* Input states `"The patient was not eligible for TEVAR"`; output asserts `{"name":"TEVAR","reaction to treatment":"planned"}`.
  - *Unsupported date & role slip:* Drops `"asymptomatic"` and emits `KD` and `ALSA` as `symptoms` with fabricated `"time":"2008"`. Mutates `gastrectomy` → `Gastroenterectomy`; garbles LSCA embolization details (`"followed LSCA embolization"`).
  - *Missing facts:* Omits preoperative coronary angiography (no significant CAD), echocardiography (normal cardiac function), asymptomatic status, retrotracheal/retroesophageal ALSCA course, and planned descending aorta replacement.
- **Baseline context:** Baseline dumped the entire clinical note almost verbatim into an unclosed `"visit motivation"` string (invalid JSON/schema, but rewarded `0.9`/`1.0` under the syntax-agnostic rubric).

### `validation:933` — Fid `0.2 → 0.0` (`-0.2`), Cov `0.3 → 0.5` (`+0.2`)
- **Format:** Valid JSON & schema, 489 tokens, clean EOS.
- **Primary cause:** **Judge evaluation artifact (`0.0` thought-leak) + Underlying relation/attribute misbinding & missing facts.**
- **Judge artifact:** `gemini-4-hydrogen` emitted its internal thought monologue instead of valid JSON in `scores.json`, defaulting the score to `0.0`.
- **Underlying model errors:**
  - *Drug→reaction misbinding:* Attaches `"reaction to treatment": "new chest mass"` to all 5 post-MI discharge drugs (`aspirin`, `atorvastatin`, `metoprolol`, `prasugrel`, `ramipril`), treating a 2-month-later return complaint as a reaction to every cardiac medication.
  - *Test→result misbinding:* Assigns catheterization LAD occlusion/stenting to `echocardiogram`.
  - *Chronology & polarity flips:* Dates `placement of drug-eluting stent` to `"two months after successful cardiac procedure"`; discharge summary asserts `"discontinued prasugrel and aspirin"` (Input: `"continued on aspirin"`); a duplicate cangrelor entry states `"stopped 2 days prior to entrance into the operating room"` (conflating prasugrel stop time with cangrelor).
  - *Missing facts:* Omits the sarcoma presentation/clearance, General Surgery bleeding-risk refusal, and final sarcoma biopsy/excision.

---

## 2. The 3 Coverage Losses

### `validation:2654` — Cov `1.0 → 0.6` (`-0.4`)
- Detailed above (**relation/attribute misbinding + missing facts + baseline verbatim-copying**).

### `validation:1193` — Cov `0.9 → 0.8` (`-0.1`), Fid `0.8 → 0.8` (`+0.0`)
- **Format:** Valid JSON & schema, 527 tokens, clean EOS.
- **Primary cause:** **Baseline verbatim-copy artifact + 1 minor omission + minor field-role slips.**
- **Details:** V4-5000 is high quality (`0.8`/`0.8`), omitting only the cut-off trailing sentence (`"The option of close follow-up was discussed, but in the institutional tumor board discussion, the consensus opinion"`). Minor field-role slips: `"location": "at birth"` on `"no swelling"`, `Birth history` / `Antenatal and birth history` placed under `diagnosis tests`, and the surgical planning sentence appended inside the CT `result`.
- **Baseline context:** Same verbatim-copying pattern as `validation:2654` (baseline dumped the full note into `"visit motivation"` and even hallucinated a completion for the truncated ending).

### `validation:2510` — Cov `0.5 → 0.4` (`-0.1`), Fid `0.3 → 0.4` (`+0.1`)
- **Format:** Valid JSON & schema, 371 tokens, clean EOS (no truncation).
- **Primary cause:** **Relation/attribute misbinding (systematic 1-step timeline shift) + Missing facts.**
- **Specific errors:**
  - *Timeline shift:* `mechanical ventilation machine` dated `at the age of 33` (Input: `34`); `cane` and `walker` dated `at the age of 34` (Input: `37`); `unable to get up by herself` / `unable to climb stairs` dated `at the age of 39` (Input: during the 3 years post-delivery before age `37`); post-delivery weakness dated `at the age of 34` (Input: pregnancy at `33`).
  - *Unsupported treatment + polarity flip:* Invents `"neurosurgical evaluation"` in `treatments` with `"reaction to treatment": "not wrongly thought that her health problems, in general, was mainly related to being overweight"` (reversing Input's `"It was wrongly thought..."`).
  - *Missing facts:* Drops the presenting complaint (`"visit motivation": "None"` instead of 4 episodes of lower limb paralysis + ER admission), childhood motor/written-language delay and school exercise difficulty, first pregnancy at 33, and maternal family history (mother died at 66 from heart attack / non-compaction cardiomyopathy).

---

## 3. The 3 Non-Schema / Budget Cases

### `validation:937` — Non-Schema + Reached Budget + `fb=1.08` | Fid `0.3 → 0.8` (`+0.5`), Cov `0.3 → 0.6` (`+0.3`)
- **Format:** `parse_valid=False`, `Unterminated string starting at: line 1 column 868`, 2048 tokens, `ended_with_eos=False`, `max_5gram=159`.
- **Primary cause:** **Repetition-loop truncation** (not a schema slip).
- **Details:** Both `rp=1.00` and the `fb=1.08` fallback hit 2048 tokens while describing complex coronary anatomy in `diagnosis tests[4]` (64-slice MSCT), looping on `"ascending into right anterior atrioventricular groove; "` until truncation. This omitted the severe calcified proximal/mid-LAD lesion and 8-day coronary angiography, though expressed assertions remained faithful (`0.8`).

### `validation:2890` — Non-Schema | Fid `0.3 → 0.4` (`+0.1`), Cov `0.3 → 0.5` (`+0.2`)
- **Format:** `parse_valid=True`, `allowed_schema_valid=False` (`treatments[3]: disallowed key details`), 682 tokens, clean EOS.
- **Primary cause:** **Severe relation/attribute misbinding + 1 disallowed key + missing facts.**
- **Specific errors:**
  - *Schema slip (caused by role misbinding):* `treatments[3]` emitted `{"name":"mechanical ground level fall","time":"the following day","details":"performed after sustaining a mechanical ground level fall"}` using surgery/symptom key `"details"`.
  - *Cut-off date back-assignment:* Input ends mid-sentence at `"At his 14-week postoperative appointment, it was noted that"`; model retroactively assigns 8-week and immediate postop events (`quadriceps atrophy`, `weight bearing as tolerated`, `knee immobilizer`) to `"at 14-week postoperative appointment"`.
  - *Duration/anatomy swaps:* Merges 3-week immobilizer and 8-week toe-touch weight bearing into `"limited to toe-touch weight bearing for 3 weeks"`; places both standard and locked screws `"submuscularly proximal to the fracture"` (standard screws were percutaneous proximal, locked screws in the distal segment).
  - *Role & negation slips:* Lists `limited lateral approach to the distal femur` as a `symptom`, `diabetes`/`coronary artery disease`/`mechanical ground level fall` as `treatments`, `stair lift`/`knee immobilizer` as `medical examinations`, and creates double negation (`"no pain..."` + `"denied"`).
  - *Missing facts:* Omits abnormal lab findings, calcium/vitamin D supplements, and 8-week radiographs (adequate callus formation).

### `validation:2308` — Non-Schema | Fid `0.3 → 0.8` (`+0.5`), Cov `0.3 → 0.4` (`+0.1`)
- **Format:** `parse_valid=False` (`Expecting ',' delimiter: line 2 column 1`), 247 tokens, `ended_with_eos=True`.
- **Primary cause:** **Premature EOS / structural JSON truncation** (not a budget hit).
- **Details:** After `surgeries[4]`, the model emitted `\n}` directly instead of closing `]` and continuing through `symptoms`, `medical examinations`, `diagnosis tests`, `treatments`, and `discharge`. Expressed facts remained faithful (`0.8`), with only minor surgery-detail repetition (`"The lingual cortical plate was left intact."` attached to two excision entries), but the missing 5 sections drove coverage down to `0.4`.

---

## Recurring Failure Patterns & Next-Step Implications

1. **Relation/attribute binding is the clear bottleneck** (schema validity is already `97/100` and budget hits are `1/100`):
   - **Timeline / date cross-wiring** (`816`, `2775`, `2510`, `2890`, `933`) — especially multi-date clinical courses and dangling cut-off dates at the end of truncated notes.
   - **`reaction to treatment` misuse** (`816`, `933`, `2654`, `2510`) — binding subsequent complaints, unrelated normal findings, negated eligibility, or inverted prose as treatment reactions.
   - **List-to-attribute over-broadcasting** (`816`, `2890`) — applying one item's result or anatomical location to sibling items in the same sentence.
   - **Section/role confusion** (`816`, `2775`, `2654`, `2890`) — exams/procedures in `symptoms`, comorbidities/events in `treatments` or `surgeries`.
2. **Decoding/termination issues are now isolated to 2 cases** (`validation:937` anatomical repetition loop past `fb=1.08`; `validation:2308` premature EOS closing brace).
3. **Evaluation hygiene:**
   - Re-judge `validation:933` Fidelity to remove the `0.0` thought-leak artifact.
   - Keep in mind that 2 of the 3 coverage losses (`validation:2654`, `validation:1193`) are against a baseline that copied raw notes verbatim into `"visit motivation"`.

---

## Source Artifacts

- `results_v4_5000/deepeval_100_rp1/judgments/2f58650627fa8d6a/paired_comparison.csv`
- `results_v4_5000/deepeval_100_rp1/judgments/2f58650627fa8d6a/scores.json`
- `results_v4_5000/deepeval_100_rp1/judgments/2f58650627fa8d6a/summary.json`
- `results_v4_5000/deepeval_100_rp1/paired_cases.json`
- `results_v4_5000/comparison/finetuned_v4_5000__gen_rp_1.00/generation_diagnostics.json`
- `results_v4_5000/comparison/finetuned_v4_5000__gen_rp_1.00/schema_violations.json`
- `results_v4_5000/comparison/finetuned_v4_5000__gen_rp_1.00/per_case.csv`
