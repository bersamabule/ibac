# NOVEL CALIBRATION SAMPLES - VALIDATION TEST SET

## Purpose

These four student writing samples were created to validate IBAC's assessment capability using texts that do NOT exist in the training data. This eliminates the possibility that IBAC is pattern-matching to memorized answers rather than genuinely applying assessment frameworks.

---

## Test Protocol

### Step 1: Review Gold Standards
You (Andrew) review each sample and its gold standard assessment. Adjust scores if you disagree with my assessment—you are the expert assessor.

### Step 2: Blind Submission to IBAC
Submit ONLY the task prompt and student response to IBAC. Do NOT include expected scores or profile names.

### Step 3: Compare Results
Compare IBAC's output against the gold standard. Record:
- Score matches (within 1 level = acceptable)
- Profile detection accuracy
- Quality of rationale

### Step 4: Calculate Validation Metrics
- Overall accuracy rate
- Per-criterion accuracy
- Profile detection rate
- False positives/negatives for each profile type

---

## Sample Overview

| ID | Topic | Target Profile | A | B | C | D |
|----|-------|----------------|---|---|---|---|
| NOVEL-01 | Lord of the Flies - Simon | Unbound Architect | 5 | 2 | 4 | 3 |
| NOVEL-02 | Great Gatsby - American Dream | Polished Hollow | 2 | 6 | 5 | 6 |
| NOVEL-03 | Persuasive Speech - Social Media | Checkbox Champion | 4 | 4 | 3 | 4 |
| NOVEL-04 | Ozymandias Poetry Analysis | Thinker in Translation | 5 | 4 | 2 | 2 |

---

## Expected Profile Detection

| Sample | Expected Profile | Key Signal |
|--------|-----------------|------------|
| NOVEL-01 | Unbound Architect | High A (5), Low B (2) — 3-level gap |
| NOVEL-02 | Polished Hollow | Low A (2), High B/C/D (5-6) — inverted pattern |
| NOVEL-03 | Checkbox Champion | Uniform 3-4 across all criteria |
| NOVEL-04 | Thinker in Translation | High A (5), Low C/D (2) — analysis outpaces expression |

---

## Validation Criteria

### Score Accuracy
- **Exact match:** IBAC score = Gold standard score
- **Acceptable:** IBAC score within ±1 of gold standard
- **Concerning:** IBAC score differs by 2 levels
- **Failure:** IBAC score differs by 3+ levels OR uniform scores where differentiation expected

### Profile Detection
- **Pass:** Correct profile identified with medium+ confidence
- **Partial:** Related profile identified (e.g., "Brilliant Mess" variant names)
- **Fail:** Wrong profile OR no profile detected where one expected

### Rationale Quality
- Does IBAC cite relevant evidence from the student work?
- Does the comparison analysis reference appropriate level benchmarks?
- Is the instructional priority pedagogically sound?

---

## Files in This Package

```
novel_calibration_samples/
├── README.md                              # This file
├── NOVEL_01_Brilliant_Mess_LOTF.md        # Sample 1: Lord of the Flies
├── NOVEL_02_Polished_Hollow_Gatsby.md     # Sample 2: Great Gatsby
├── NOVEL_03_Checkbox_Champion_SocialMedia.md  # Sample 3: Social Media Speech
├── NOVEL_04_Thinker_Translation_Ozymandias.md # Sample 4: Ozymandias
└── SUBMISSION_TEXTS_ONLY.md               # Clean texts for IBAC submission
```

---

## After Validation

### If IBAC passes (≥75% accuracy):
- Calibration is validated
- Proceed with confidence to real student work
- Document baseline for future reference

### If IBAC partially passes (50-74% accuracy):
- Identify which profiles/criteria are problematic
- May need targeted calibration refinement
- Consider additional validation samples

### If IBAC fails (<50% accuracy):
- Calibration has NOT generalized beyond training data
- Fundamental prompt/architecture revision needed
- Do NOT deploy for real assessment until fixed

---

## Important Notes

1. **These samples are NOVEL** — they do not exist in any training data
2. **Gold standards are my assessment** — you should validate/adjust before testing
3. **Blind submission is critical** — do not reveal expected scores to IBAC
4. **Document everything** — results inform next development phase
