# Live Demo Cases (`v4` Clinical SFT)

Copy any **Clinical Note** below and paste it into the CLI, or run the command:

```powershell
# Fine-tuned V4-1325 adapter (default)
.venv\Scripts\python.exe -m scripts.infer_v4_cli

# Fine-tuned V4-5000 adapter
.venv\Scripts\python.exe -m scripts.infer_v4_cli --mode v4-5000

# Unadapted baseline
.venv\Scripts\python.exe -m scripts.infer_v4_cli --mode baseline
```

> **Tip:** On Windows, paste the note and press `Ctrl+Z` then `Enter` to submit.

---

## Case 1: `validation:435`
*28-year-old female — OCD / psychiatric consultation*

### Clinical Note (copy & paste into CLI)

```text
A 28-year-old female from another prefecture came to our department for psychiatric diagnosis and treatment. Because her obstetrician informed her that her husband's sperm and her egg were old given their age, she worried about the health of her fetus during pregnancy. After reading a newspaper article on Down syndrome, she began to have thoughts about the term Down syndrome. When she thought of it, she subsequently and repeatedly thought of the word healthy until she canceled the term Down syndrome. She was diagnosed with OCD in a psychiatric hospital at the age of 26, but she refused to be treated because she believed that she could cure the OCD with her own efforts. When she was 27 years old, the words unhappy, death, die, and kill came to her mind at the same time as the face of an acquaintance. She tried to counteract these obsessive-compulsive thoughts by repeatedly thinking of the words different and not die. After four months, she began to think of the words rape, crematorium, neck hanging, unhappy, death, die, and kill and then images of a shelf of gods, a shrine, a Buddhist altar, the sun, and the sky. She tried to avoid looking at these things. She visualized the faces of her parents, siblings, and relatives appearing in her images at the same time as the images of these words. She tried to erase the words and images by repeating the word different. Because her obsessive-compulsive symptoms did not improve, she revisited the psychiatric hospital and was diagnosed with OCD again. Treatment with aripiprazole and fluvoxamine was initiated. She had received psychoanalytic counseling from a psychiatrist for 6 months, but she did not experience relief. She discontinued the psychoanalytic counseling and drug treatment after consultation with her doctor. Next, she visited our department with the hope of improving her obsessive-compulsive symptoms. She was
```

<details>
<summary>Full Templated Prompt (optional, for <code>--raw</code>)</summary>

```text
<bos><start_of_turn>user
Extract only clinical facts explicitly stated in the supplied note into one JSON object. Return JSON only, without markdown or commentary. Preserve negation, uncertainty, historical versus current events, and which findings or doses belong to each event or drug. Do not infer missing facts or complete cut-off text. Include all ten top-level fields. The allowed fields and types are: visit motivation is a string; admission is an array of objects with optional fields reason; patient information is an object with optional fields age, sex; patient medical history is an object with optional fields physiological context; surgeries is an array of objects with optional fields Type, time, details; symptoms is an array of objects with optional fields name of symptom, location, time, details; medical examinations is an array of objects with optional fields name, result; diagnosis tests is an array of objects with optional fields test, result; treatments is an array of objects with optional fields name, dosage, time, reaction to treatment; discharge is an object with optional fields discharge summary. Use [] for empty arrays, {} for empty objects, and "None" for absent visit motivation. Omit missing inner fields. Do not add other keys or repeat identical entries.

Clinical note:
A 28-year-old female from another prefecture came to our department for psychiatric diagnosis and treatment. Because her obstetrician informed her that her husband's sperm and her egg were old given their age, she worried about the health of her fetus during pregnancy. After reading a newspaper article on Down syndrome, she began to have thoughts about the term Down syndrome. When she thought of it, she subsequently and repeatedly thought of the word healthy until she canceled the term Down syndrome. She was diagnosed with OCD in a psychiatric hospital at the age of 26, but she refused to be treated because she believed that she could cure the OCD with her own efforts. When she was 27 years old, the words unhappy, death, die, and kill came to her mind at the same time as the face of an acquaintance. She tried to counteract these obsessive-compulsive thoughts by repeatedly thinking of the words different and not die. After four months, she began to think of the words rape, crematorium, neck hanging, unhappy, death, die, and kill and then images of a shelf of gods, a shrine, a Buddhist altar, the sun, and the sky. She tried to avoid looking at these things. She visualized the faces of her parents, siblings, and relatives appearing in her images at the same time as the images of these words. She tried to erase the words and images by repeating the word different. Because her obsessive-compulsive symptoms did not improve, she revisited the psychiatric hospital and was diagnosed with OCD again. Treatment with aripiprazole and fluvoxamine was initiated. She had received psychoanalytic counseling from a psychiatrist for 6 months, but she did not experience relief. She discontinued the psychoanalytic counseling and drug treatment after consultation with her doctor. Next, she visited our department with the hope of improving her obsessive-compulsive symptoms. She was<end_of_turn>
<start_of_turn>model
```

</details>

### Reference Output (Regenerated Label)

```json
{
  "visit motivation": "psychiatric diagnosis and treatment",
  "admission": [],
  "patient information": {
    "age": "28-year-old",
    "sex": "female"
  },
  "patient medical history": {
    "physiological context": "pregnancy"
  },
  "surgeries": [],
  "symptoms": [
    {
      "name of symptom": "worried about the health of her fetus",
      "time": "during pregnancy"
    },
    {
      "name of symptom": "thoughts about the term Down syndrome"
    },
    {
      "name of symptom": "subsequently and repeatedly thought of the word healthy until she canceled the term Down syndrome"
    },
    {
      "name of symptom": "obsessive-compulsive thoughts",
      "time": "When she was 27 years old",
      "details": "the words unhappy, death, die, and kill came to her mind at the same time as the face of an acquaintance"
    },
    {
      "name of symptom": "counteract these obsessive-compulsive thoughts",
      "time": "When she was 27 years old",
      "details": "repeatedly thinking of the words different and not die"
    },
    {
      "name of symptom": "obsessive-compulsive thoughts and images",
      "time": "After four months",
      "details": "think of the words rape, crematorium, neck hanging, unhappy, death, die, and kill and then images of a shelf of gods, a shrine, a Buddhist altar, the sun, and the sky"
    },
    {
      "name of symptom": "avoidance behavior",
      "time": "After four months",
      "details": "avoid looking at these things"
    },
    {
      "name of symptom": "obsessive images",
      "time": "After four months",
      "details": "visualized the faces of her parents, siblings, and relatives appearing in her images at the same time as the images of these words"
    },
    {
      "name of symptom": "compulsive thoughts",
      "time": "After four months",
      "details": "tried to erase the words and images by repeating the word different"
    },
    {
      "name of symptom": "obsessive-compulsive symptoms"
    }
  ],
  "medical examinations": [],
  "diagnosis tests": [
    {
      "test": "psychiatric diagnosis",
      "result": "OCD"
    },
    {
      "test": "psychiatric diagnosis",
      "result": "OCD again"
    }
  ],
  "treatments": [
    {
      "name": "treatment",
      "time": "at the age of 26",
      "reaction to treatment": "refused to be treated because she believed that she could cure the OCD with her own efforts"
    },
    {
      "name": "aripiprazole",
      "reaction to treatment": "discontinued after consultation with her doctor"
    },
    {
      "name": "fluvoxamine",
      "reaction to treatment": "discontinued after consultation with her doctor"
    },
    {
      "name": "psychoanalytic counseling from a psychiatrist",
      "time": "for 6 months",
      "reaction to treatment": "did not experience relief; discontinued after consultation with her doctor"
    }
  ],
  "discharge": {}
}
```

---

## Case 2: `validation:1812`
*Term male infant — repeat caesarean section*

### Clinical Note (copy & paste into CLI)

```text
A male infant, who was term appropriate for gestational age, was born via repeat caesarean section to a healthy 26-year-old woman. No family history of bleeding disorders was reported by the mother. Pregnancy was unremarkable, and Apgar scores were 9 and 9 at 1 and 5 minutes, respectively. On initial physical examination, a localized hematoma to the left parietotemporal region was identified. A routine complete blood count (CBC) displayed normal counts. It was decided to repeat the CBC in 12 hours and, in the interim, to observe for dissemination of the blood collection. Prior to the next blood test, the physician was called to the bedside because the infant now had a change in his clinical examination: pale and tachycardic. His examination now revealed a large palpable fluid wave that extended behind the neck and left ear. Given the infant’s change in clinical status and concern for a subgaleal hematoma, the infant was transferred to the neonatal intensive care unit (NICU). The repeat CBC showed a hemoglobin level of 7.6 g/dL, with a hematocrit of 22% and platelets of 169 × 109/L. In the NICU, the patient received a transfusion of 20 cc/kg of O Rh-negative packed red cells. His coagulation profile disclosed a normal prothrombin time but an activated partial thromboplastin time (PTT) of 101 seconds (normal = 25-30 seconds).
Subsequently, a FVIII level was ordered, which was very low at <0.01 U/mL. He was diagnosed with severe HA and was initially treated with 50 U/kg of recombinant FVIII. His repeat doses were adjusted to bring his FVIII level to 100%. A computed tomography (CT) scan of the head revealed a large subgaleal hematoma, beginning in the left parietal area, extending to the occiput and down the nape of the neck. The infant was discharged at 1 week of age following a repeat head imaging confirming complete resolution of the
```

<details>
<summary>Full Templated Prompt (optional, for <code>--raw</code>)</summary>

```text
<bos><start_of_turn>user
Extract only clinical facts explicitly stated in the supplied note into one JSON object. Return JSON only, without markdown or commentary. Preserve negation, uncertainty, historical versus current events, and which findings or doses belong to each event or drug. Do not infer missing facts or complete cut-off text. Include all ten top-level fields. The allowed fields and types are: visit motivation is a string; admission is an array of objects with optional fields reason; patient information is an object with optional fields age, sex; patient medical history is an object with optional fields physiological context; surgeries is an array of objects with optional fields Type, time, details; symptoms is an array of objects with optional fields name of symptom, location, time, details; medical examinations is an array of objects with optional fields name, result; diagnosis tests is an array of objects with optional fields test, result; treatments is an array of objects with optional fields name, dosage, time, reaction to treatment; discharge is an object with optional fields discharge summary. Use [] for empty arrays, {} for empty objects, and "None" for absent visit motivation. Omit missing inner fields. Do not add other keys or repeat identical entries.

Clinical note:
A male infant, who was term appropriate for gestational age, was born via repeat caesarean section to a healthy 26-year-old woman. No family history of bleeding disorders was reported by the mother. Pregnancy was unremarkable, and Apgar scores were 9 and 9 at 1 and 5 minutes, respectively. On initial physical examination, a localized hematoma to the left parietotemporal region was identified. A routine complete blood count (CBC) displayed normal counts. It was decided to repeat the CBC in 12 hours and, in the interim, to observe for dissemination of the blood collection. Prior to the next blood test, the physician was called to the bedside because the infant now had a change in his clinical examination: pale and tachycardic. His examination now revealed a large palpable fluid wave that extended behind the neck and left ear. Given the infant’s change in clinical status and concern for a subgaleal hematoma, the infant was transferred to the neonatal intensive care unit (NICU). The repeat CBC showed a hemoglobin level of 7.6 g/dL, with a hematocrit of 22% and platelets of 169 × 109/L. In the NICU, the patient received a transfusion of 20 cc/kg of O Rh-negative packed red cells. His coagulation profile disclosed a normal prothrombin time but an activated partial thromboplastin time (PTT) of 101 seconds (normal = 25-30 seconds).
Subsequently, a FVIII level was ordered, which was very low at <0.01 U/mL. He was diagnosed with severe HA and was initially treated with 50 U/kg of recombinant FVIII. His repeat doses were adjusted to bring his FVIII level to 100%. A computed tomography (CT) scan of the head revealed a large subgaleal hematoma, beginning in the left parietal area, extending to the occiput and down the nape of the neck. The infant was discharged at 1 week of age following a repeat head imaging confirming complete resolution of the<end_of_turn>
<start_of_turn>model
```

</details>

### Reference Output (Regenerated Label)

```json
{
  "visit motivation": "None",
  "admission": [
    {
      "reason": "infant’s change in clinical status and concern for a subgaleal hematoma"
    }
  ],
  "patient information": {
    "age": "infant",
    "sex": "male"
  },
  "patient medical history": {
    "physiological context": "term appropriate for gestational age"
  },
  "surgeries": [],
  "symptoms": [
    {
      "name of symptom": "localized hematoma",
      "time": "initial physical examination"
    },
    {
      "name of symptom": "pale"
    },
    {
      "name of symptom": "tachycardic"
    },
    {
      "name of symptom": "fluid wave",
      "location": "behind the neck and left ear",
      "details": "large palpable fluid wave"
    }
  ],
  "medical examinations": [
    {
      "name": "Apgar scores",
      "result": "9 and 9 at 1 and 5 minutes, respectively"
    },
    {
      "name": "initial physical examination",
      "result": "a localized hematoma to the left parietotemporal region was identified"
    },
    {
      "name": "clinical examination",
      "result": "pale and tachycardic; large palpable fluid wave that extended behind the neck and left ear"
    }
  ],
  "diagnosis tests": [
    {
      "test": "routine complete blood count (CBC)",
      "result": "normal counts"
    },
    {
      "test": "repeat CBC",
      "result": "hemoglobin level of 7.6 g/dL, with a hematocrit of 22% and platelets of 169 × 109/L"
    },
    {
      "test": "prothrombin time",
      "result": "normal"
    },
    {
      "test": "activated partial thromboplastin time (PTT)",
      "result": "101 seconds (normal = 25-30 seconds)"
    },
    {
      "test": "FVIII level",
      "result": "very low at <0.01 U/mL"
    },
    {
      "test": "computed tomography (CT) scan of the head",
      "result": "large subgaleal hematoma, beginning in the left parietal area, extending to the occiput and down the nape of the neck"
    },
    {
      "test": "repeat head imaging",
      "result": "confirming complete resolution of the"
    }
  ],
  "treatments": [
    {
      "name": "transfusion of O Rh-negative packed red cells",
      "dosage": "20 cc/kg"
    },
    {
      "name": "recombinant FVIII",
      "dosage": "50 U/kg initially",
      "reaction to treatment": "repeat doses were adjusted to bring his FVIII level to 100%"
    }
  ],
  "discharge": {
    "discharge summary": "discharged at 1 week of age following a repeat head imaging confirming complete resolution of the"
  }
}
```

---

## Case 3: `validation:1539`
*15-year-old boy — right wrist pain after fall*

### Clinical Note (copy & paste into CLI)

```text
A 15-year-old boy presented to the clinic with a right wrist pain, which is aggravated for 3 months ago. The patient hurt his right wrist after a fall while playing soccer a year prior to the presentation. The patient did not receive any treatment despite experiencing pain during laborious tasks, since he was able to perform daily activities. Upon physical examination, the radial side of the wrist had mild edema and evident anatomical snuff box tenderness. The patient displayed a limited ROM with flexion and extension angles of 70° and 60°, respectively, in the right wrist (80° and 90° in the left wrist, respectively). The radial and ulnar deviation angles in the right wrist were 15° and 50°, respectively (25° and 50° in the left wrist, respectively). When we examined the patient, the wrist showed mild swelling on the radial aspect as well as anatomical snuff box tenderness. He displayed limited ROM, flexion and extension angles of the right wrist were 70° and 60°, respectively (with 80° and 90° in the left). The radial and ulnar deviation angles in the right wrist were 15° and 50°, respectively (with 25° and 50° in the left).
Initial plain wrist radiographs demonstrated nonunion of a fracture in the waist of the scaphoid (Fig. A). A computed tomography (CT) was obtained and indicated nonunion in the scaphoid waist and lateral intra-scaphoid angle of about 88°. The results induced the finding of humpback deformity (Fig. B).
Arthroscopic bone grafting and percutaneous K wires fixation was performed under general anesthesia. The mid-carpal joint arthroscopic findings revealed nonunion in the waist area, with punctate bleeding observed in proximal and distal fragments after arthroscopic debridement and removal of necrotic tissue, at the nonunion site. The associated injury was Geissler grade II instability at the volar side of the SL joint (Fig. C-G).[ We could get a complete bone
```

<details>
<summary>Full Templated Prompt (optional, for <code>--raw</code>)</summary>

```text
<bos><start_of_turn>user
Extract only clinical facts explicitly stated in the supplied note into one JSON object. Return JSON only, without markdown or commentary. Preserve negation, uncertainty, historical versus current events, and which findings or doses belong to each event or drug. Do not infer missing facts or complete cut-off text. Include all ten top-level fields. The allowed fields and types are: visit motivation is a string; admission is an array of objects with optional fields reason; patient information is an object with optional fields age, sex; patient medical history is an object with optional fields physiological context; surgeries is an array of objects with optional fields Type, time, details; symptoms is an array of objects with optional fields name of symptom, location, time, details; medical examinations is an array of objects with optional fields name, result; diagnosis tests is an array of objects with optional fields test, result; treatments is an array of objects with optional fields name, dosage, time, reaction to treatment; discharge is an object with optional fields discharge summary. Use [] for empty arrays, {} for empty objects, and "None" for absent visit motivation. Omit missing inner fields. Do not add other keys or repeat identical entries.

Clinical note:
A 15-year-old boy presented to the clinic with a right wrist pain, which is aggravated for 3 months ago. The patient hurt his right wrist after a fall while playing soccer a year prior to the presentation. The patient did not receive any treatment despite experiencing pain during laborious tasks, since he was able to perform daily activities. Upon physical examination, the radial side of the wrist had mild edema and evident anatomical snuff box tenderness. The patient displayed a limited ROM with flexion and extension angles of 70° and 60°, respectively, in the right wrist (80° and 90° in the left wrist, respectively). The radial and ulnar deviation angles in the right wrist were 15° and 50°, respectively (25° and 50° in the left wrist, respectively). When we examined the patient, the wrist showed mild swelling on the radial aspect as well as anatomical snuff box tenderness. He displayed limited ROM, flexion and extension angles of the right wrist were 70° and 60°, respectively (with 80° and 90° in the left). The radial and ulnar deviation angles in the right wrist were 15° and 50°, respectively (with 25° and 50° in the left).
Initial plain wrist radiographs demonstrated nonunion of a fracture in the waist of the scaphoid (Fig. A). A computed tomography (CT) was obtained and indicated nonunion in the scaphoid waist and lateral intra-scaphoid angle of about 88°. The results induced the finding of humpback deformity (Fig. B).
Arthroscopic bone grafting and percutaneous K wires fixation was performed under general anesthesia. The mid-carpal joint arthroscopic findings revealed nonunion in the waist area, with punctate bleeding observed in proximal and distal fragments after arthroscopic debridement and removal of necrotic tissue, at the nonunion site. The associated injury was Geissler grade II instability at the volar side of the SL joint (Fig. C-G).[ We could get a complete bone<end_of_turn>
<start_of_turn>model
```

</details>

### Reference Output (Regenerated Label)

```json
{
  "visit motivation": "right wrist pain, which is aggravated for 3 months ago",
  "admission": [],
  "patient information": {
    "age": "15-year-old",
    "sex": "boy"
  },
  "patient medical history": {
    "physiological context": "The patient hurt his right wrist after a fall while playing soccer a year prior to the presentation. The patient did not receive any treatment despite experiencing pain during laborious tasks, since he was able to perform daily activities."
  },
  "surgeries": [
    {
      "Type": "Arthroscopic bone grafting and percutaneous K wires fixation",
      "details": "performed under general anesthesia. The mid-carpal joint arthroscopic findings revealed nonunion in the waist area, with punctate bleeding observed in proximal and distal fragments after arthroscopic debridement and removal of necrotic tissue, at the nonunion site. The associated injury was Geissler grade II instability at the volar side of the SL joint"
    }
  ],
  "symptoms": [
    {
      "name of symptom": "wrist pain",
      "location": "right wrist",
      "time": "a year prior to the presentation",
      "details": "aggravated for 3 months ago"
    },
    {
      "name of symptom": "pain",
      "details": "during laborious tasks"
    }
  ],
  "medical examinations": [
    {
      "name": "physical examination of the radial side of the wrist",
      "result": "mild edema and mild swelling"
    },
    {
      "name": "anatomical snuff box examination",
      "result": "evident anatomical snuff box tenderness"
    },
    {
      "name": "ROM flexion and extension angles of right wrist",
      "result": "70° and 60°, respectively (80° and 90° in the left wrist, respectively)"
    },
    {
      "name": "radial and ulnar deviation angles in the right wrist",
      "result": "15° and 50°, respectively (25° and 50° in the left wrist, respectively)"
    }
  ],
  "diagnosis tests": [
    {
      "test": "Initial plain wrist radiographs",
      "result": "nonunion of a fracture in the waist of the scaphoid"
    },
    {
      "test": "computed tomography (CT)",
      "result": "nonunion in the scaphoid waist and lateral intra-scaphoid angle of about 88°, inducing the finding of humpback deformity"
    }
  ],
  "treatments": [],
  "discharge": {}
}
```
