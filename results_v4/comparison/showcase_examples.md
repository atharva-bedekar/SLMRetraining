# Side-by-Side Showcase (`gen_rp_1.08`)

## validation:2438
- **Base:** raw_valid=False, exact_F1=0.058, soft_F1=0.172, toks=1136
- **Fine-tuned v3:** raw_valid=True, exact_keys=False, exact_F1=0.614, soft_F1=0.699, toks=602

**Clinical Note (excerpt):**
```
We present the case of a 51-year-old Caucasian woman with a four-year history of recurrent, right-sided facial pain, in the distribution of all three branches of the trigeminal nerve. These episodes occurred on average two to three times per week and were characterised by brief episodes of unilateral right-sided sharp lancinating pain, lasting on average less than one minute and predominantly affecting the maxillary and mandibular divisions of the trigeminal nerve, although occasionally involving all three branches. Attacks were typically triggered by such actions as washing her face or smilin...
```
**Reference JSON:**
```json
{"visit motivation":"four-year history of recurrent, right-sided facial pain","admission":[],"patient information":{"age":"51-year-old","sex":"woman"},"patient medical history":{"physiological context":"no prior history of headache"},"surgeries":[{"Type":"decompression of her right trigeminal nerve","time":"nine months after the initial onset of her symptoms","details":"symptoms worsened following this"},{"Type":"radiofrequency ablation","time":"14 months after the decompressive surgery","details":"resulted in some permanent numbness in her right infra-orbital area but no pain relief"}],"symptoms":[{"name of symptom":"recurrent, right-sided facial pain","location":"right-sided facial, in the distribution of all three branches of the trigeminal nerve, predominantly affecting the maxillary and mandibular divisions, although occasionally involving all three branches","time":"four-year history","details":"characterised by brief episodes of sharp lancinating pain, lasting on average less than one minute, occurring on average two to three times per week, typically triggered by actions such as washing her face or smiling"},{"name of symptom":"no headaches","details":"no associated headach
```
**Base Output:**
```
```json
{
  "visit motivation": "a 51-year-old Caucasian woman with a four-year history of recurrent, right-sided facial pain, in the distribution of all three branches of the trigeminal nerve.",
  "admission": [
    {
      "reason": "acute onset of acute facial pain",
      "dosage": "up to 1200 mg daily",
      "duration": "two to three times per week",
      "details": "brief episodes of unilateral right-sided sharp lancinating pain, lasting on average less than one minute and predominantly affecting the maxillary and mandibular divisions of the trigeminal nerve, although occasionally involving all three branches."
    },
    {
      "reason": "initial treatment with gabapentin (up to 1200 mg daily)",
      "dosage": "up to 800 mg daily",
      "duration": "without significant benefit",
      "details": "carbamazepine (up to 800 mg daily)"
    },
    {
      "reason": "neurosurgical 
```
**Fine-Tuned v3 Output:**
```json
{"visit motivation":"None","admission":[],"patient information":{"age":"51-year-old","sex":"woman"},"patient medical history":{"physiological context":"Four-year history of recurrent, right-sided facial pain, in the distribution of all three branches of the trigeminal nerve; no other features associated with these attacks; no prior history of headache and no family history of trigeminal neuralgia"},"surgeries":[{"Type":"decompression of her right trigeminal nerve","time":"nine months after the initial onset of her symptoms","details":"resulted in some permanent numbness in her right infra-orbital area but no pain relief"},{"Type":"radiofrequency ablation","time":"14 months after the decompressive surgery","details":"resulted in some permanent numbness in her right infra-orbital area but no pain relief"}],"symptoms":[{"name of symptom":"facial pain","location":"right-sided","time":"four-year history","details":"recurrent, right-sided, distributed across all three branches of the trigeminal nerve, typically occurring on average two to three times per week, characterized by brief episodes of unilateral sharp lancinating pain lasting on average less than one minute, predominantly affec
```

## validation:113
- **Base:** raw_valid=False, exact_F1=0.019, soft_F1=0.092, toks=804
- **Fine-tuned v3:** raw_valid=True, exact_keys=False, exact_F1=0.574, soft_F1=0.695, toks=616

**Clinical Note (excerpt):**
```
A 44-year-old female had been suffering from dry cough, myalgia, and arthralgia since 2013 and was diagnosed as DM (Table ). Her symptoms were abated by combination treatment using prednisolone and tacrolimus. However, the cough, pyrexia, and arthralgia recurred due to the exacerbation of DM. The patient was admitted to our hospital for further checkup and treatment. Laboratory data showed that her white blood cell count and C-reactive protein levels were elevated. Her serum carcinoembryonic antigen and carbohydrate antigen 19-9 were not elevated (Table ). Enhanced computed tomography showed a...
```
**Reference JSON:**
```json
{"visit motivation":"further checkup and treatment","admission":[{"reason":"further checkup and treatment"}],"patient information":{"age":"44-year-old","sex":"female"},"patient medical history":{"physiological context":"diagnosed as DM"},"surgeries":[{"Type":"hepatic medial segmentectomy"},{"Type":"cholecystectomy"}],"symptoms":[{"name of symptom":"dry cough","time":"since 2013"},{"name of symptom":"myalgia","time":"since 2013"},{"name of symptom":"arthralgia","time":"since 2013"},{"name of symptom":"cough","details":"recurred due to the exacerbation of DM"},{"name of symptom":"pyrexia","details":"recurred due to the exacerbation of DM"},{"name of symptom":"arthralgia","details":"recurred due to the exacerbation of DM"}],"medical examinations":[],"diagnosis tests":[{"test":"white blood cell count","result":"elevated"},{"test":"C-reactive protein levels","result":"elevated"},{"test":"serum carcinoembryonic antigen","result":"not elevated"},{"test":"carbohydrate antigen 19-9","result":"not elevated"},{"test":"Enhanced computed tomography","result":"20-mm low-density tumor with a gradual enhancement in segment 4 of the liver"},{"test":"Ultrasonography","result":"20-mm tumor in segment
```
**Base Output:**
```
```json
{
  "visit motivation": "Dry cough, myalgia, and arthralgia",
  "admission": [
    {
      "reason": "Aborted by combination treatment using prednisolone and tacrolimus",
      "age": 44,
      "sex": "Female"
    },
    {
      "reason": "Elevated white blood cell count and C-reactive protein levels",
      "age": 44,
      "sex": "Female"
    }
  ],
  "patient information": {
    "age": 44,
    "sex": "Female"
  },
  "patient medical history": {
    "physiological context": "aborted by combination treatment using prednisolone and tacrolimus",
    "specific symptoms": ["dry cough", "myalgia", "arthralgia", "arthralgia"]
  },
  "surgery": [
    {
      "type": "Surgery",
      "time": "2013",
      "details": "Treatment: Prednisolone and tacrolimus"
    },
    {
      "type": "Surgery",
      "time": "2020",
      "details": "Treatment: Prednisolone and tacrolimus"
    }
  ],
  "
```
**Fine-Tuned v3 Output:**
```json
{"visit motivation":"further checkup and treatment","admission":[{"reason":"further checkup and treatment"}],"patient information":{"age":"44-year-old","sex":"female"},"patient medical history":{},"surgeries":[{"Type":"hepatic medial segmentectomy and cholecystectomy","details":"performed in the resected specimen"}],"symptoms":[{"name of symptom":"dry cough","time":"since 2013"},{"name of symptom":"myalgia","time":"since 2013"},{"name of symptom":"arthralgia","location":"arthralgia","time":"since 2013"},{"name of symptom":"cough","time":"since 2013"},{"name of symptom":"pyrexia","time":"since 2013"},{"name of symptom":"arthralgia","time":"since 2013"},{"name of symptom":"recurrence","time":"due to the exacerbation of DM","details":"aborted by combination treatment using prednisolone and tacrolimus"},{"name of symptom":"recurrence","time":"due to the exacerbation of DM","details":"recurred due to the exacerbation of DM"},{"name of symptom":"no postoperative complications","details":"made a satisfactory recovery with no postoperative complications"}],"medical examinations":[],"diagnosis tests":[{"test":"White blood cell count","result":"elevated"},{"test":"C-reactive protein levels",
```

## validation:398
- **Base:** raw_valid=False, exact_F1=0.000, soft_F1=0.019, toks=748
- **Fine-tuned v3:** raw_valid=True, exact_keys=False, exact_F1=0.286, soft_F1=0.447, toks=573

**Clinical Note (excerpt):**
```
In 2018, a Caucasian 54-year-old woman presented to our institution of Nuclear Medicine for a breast cancer with bone metastases. She reported fulvestrant therapy and ten cycles of radiotherapy and she also reported the beginning of zoledronate therapy (i.e., zometa) in June 2015, which was suspended in June 2017 due to the appearance of bone exposure, after the dental extraction of the upper right first molar.
The intraoral clinical examination showed an area of exposed necrotic bone, with oroantral communication associated with suppuration and pain. The computed tomography (CT) scan showed h...
```
**Reference JSON:**
```json
{"visit motivation":"breast cancer with bone metastases","admission":[],"patient information":{"age":"54-year-old","sex":"woman"},"patient medical history":{},"surgeries":[{"Type":"dental extraction","details":"upper right first molar"}],"symptoms":[{"name of symptom":"bone exposure","time":"June 2017","details":"appearance after the dental extraction of the upper right first molar"},{"name of symptom":"suppuration"},{"name of symptom":"pain"}],"medical examinations":[{"name":"intraoral clinical examination","result":"showed an area of exposed necrotic bone, with oroantral communication associated with suppuration and pain"}],"diagnosis tests":[{"test":"computed tomography (CT) scan","result":"showed how ONJ process involved the entire upper right maxilla, and the ONJ was classified as Stage 3 (SICMF-SIPMO staging system)"},{"test":"bone scan with 99mTc-methylene diphosphonate","result":"confirmed neoplastic bone lesions"},{"test":"technetium polyphosphate 99mTc scan","result":"demonstrated increased 99mTc accumulation in areas of increased blood flow and new bone formation secondary to the infection"}],"treatments":[{"name":"fulvestrant therapy"},{"name":"radiotherapy","dosage":"t
```
**Base Output:**
```
```json
{
  "visit motivation": "Patient's refusal to receive treatment and taking into account the bone disease.",
  "admission": [
    {
      "reason": "Bone disease",
      "dose": "1 g i. m. 2 × daily for 7 days"
    },
    {
      "reason": "Bone disease",
      "dose": "250 mg per os 2 × daily for 7 days"
    }
  ],
  "patient information": {
    "age": "54",
    "sex": "Female",
    "medical history": {
      "physiological context": "Fulvestrant therapy and ten cycles of radiotherapy and she also reported the beginning of zoledronate therapy (i.e., zometa) in June 2015, which was suspended in June 2017 due to the appearance of bone exposure, after the dental extraction of the upper right first molar.",
      "surgery": [
        "Dental extraction of upper right first molar"
      ]
    },
    "symptoms": [
      {
        "name": "fulvestrant therapy",
        "location": "uppe
```
**Fine-Tuned v3 Output:**
```json
{"visit motivation":"breast cancer with bone metastases","admission":[],"patient information":{"age":"54-year-old","sex":"woman"},"patient medical history":{},"surgeries":[{"Type":"dental extraction of the upper right first molar","time":"June 2017"},{"Type":"medical treatment based on the administration of ampicillin and sulbactam (1 g i. m. 2 × daily for 7 days)","details":"on the dental extraction of the upper right first molar"}],"symptoms":[{"name of symptom":"bone exposure","location":"upper right first molar","time":"in 2018","details":"due to the appearance of bone exposure"},{"name of symptom":"no pain","location":"upper right first molar","details":"denied"},{"name of symptom":"no osteolysis","location":"bone","details":"denied"}],"medical examinations":[{"name":"intraoral clinical examination","result":"area of exposed necrotic bone, with oroantral communication associated with suppuration and pain"},{"name":"computed tomography (CT) scan","result":"ONJ process involved the entire upper right maxilla, and the ONJ was classified as Stage 3 (SICMF-SIPMO staging system)"},{"name":"initial antibiotic therapy for ONJ","result":"ineffective conservative treatment because ONJ w
```

## validation:979
- **Base:** raw_valid=False, exact_F1=0.030, soft_F1=0.060, toks=1434
- **Fine-tuned v3:** raw_valid=False, exact_keys=False, exact_F1=0.000, soft_F1=0.000, toks=2048

**Clinical Note (excerpt):**
```
A 64-year-old female was referred to our surgical oncology clinic for evaluation of cystic lesions of the pancreas found on CT scan at an outside hospital after she presented with a history of approximately nine months of vague epigastric pain, nausea and vomiting. She had a 50-year history of daily tobacco use (0.5 pack per day) and nightly alcohol use that had reportedly stopped around the same time as the onset of her symptoms, but she was otherwise healthy.
She had also undergone an MRI/MRCP at the outside hospital that revealed multiple cystic loculations of the pancreas that appeared to ...
```
**Reference JSON:**
```json
{"visit motivation":"evaluation of cystic lesions of the pancreas found on CT scan at an outside hospital","admission":[],"patient information":{"age":"64-year-old","sex":"female"},"patient medical history":{"physiological context":"50-year history of daily tobacco use (0.5 pack per day) and nightly alcohol use that had reportedly stopped around the same time as the onset of her symptoms, but she was otherwise healthy"},"surgeries":[{"Type":"total pancreatectomy with duodenectomy, cholecystectomy, and splenectomy"}],"symptoms":[{"name of symptom":"pain","location":"epigastric","time":"approximately nine months","details":"vague"},{"name of symptom":"nausea","time":"approximately nine months"},{"name of symptom":"vomiting","time":"approximately nine months"}],"medical examinations":[],"diagnosis tests":[{"test":"CT scan at an outside hospital","result":"cystic lesions of the pancreas"},{"test":"MRI/MRCP at the outside hospital","result":"multiple cystic loculations of the pancreas that appeared to be possibly in communication with the main pancreatic duct, calcifications in the head of the pancreas consistent with chronic pancreatitis"},{"test":"Carbohydrate Antigen 19-9 (CA 19-9)",
```
**Base Output:**
```
```json
{
  "visit motivation": "A 64-year-old female was referred to our surgical oncology clinic for evaluation of cystic lesions of the pancreas found on CT scan at an outside hospital after she presented with a history of approximately nine months of vague epigastric pain, nausea and vomiting.",
  "admission": [
    {
      "reason": "History of approximately nine months of vague epigastric pain, nausea and vomiting.",
      "details": "She had a 50-year history of daily tobacco use (0.5 pack per day) and nightly alcohol use that had reportedly stopped around the same time as the onset of her symptoms, but she was otherwise healthy."
    },
    {
      "reason": "A 50-year history of daily tobacco use (0.5 pack per day) and nightly alcohol use that had reportedly stopped around the same time as the onset of her symptoms, but she was otherwise healthy.",
      "details": "She also und
```
**Fine-Tuned v3 Output:**
```json
{"visit motivation":"evaluation of cystic lesions of the pancreas found on CT scan at an outside hospital after she presented with a history of approximately nine months of vague epigastric pain, nausea and vomiting","admission":[],"patient information":{"age":"64-year-old","sex":"female"},"patient medical history":{"physiological context":"50-year history of daily tobacco use (0.5 pack per day) and nightly alcohol use that had reportedly stopped around the same time as the onset of her symptoms; otherwise healthy"},"surgeries":[{"Type":"total pancreatectomy with duodenectomy","details":"creation of a"},{"Type":"cholecystectomy","details":"creation of a"},{"Type":"splenectomy","details":"creation of a"}],"symptoms":[{"name of symptom":"gastrointestinal pain","location":"abdominal","time":"approximately nine months","details":"vague epigastric"},{"name of symptom":"nausea","time":"approximately nine months","details":"vomiting"},{"name of symptom":"vomiting","time":"approximately nine months","details":"vomiting"},{"name of symptom":"pain","location":"epigastric","time":"approximately nine months","details":"vague"},{"name of symptom":"nocturnal","time":"approximately nine months","
```
