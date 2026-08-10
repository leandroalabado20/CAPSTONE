# Job Recommendation Inference — Full Notes
**Script:** `recommend.py`
**Input:** 4 applicant profile fields + list of active job vacancies
**Output:** Ranked vacancy list with suitability scores per vacancy
**Depends on:** `../ml/recommendation_pipeline.pkl`

---

## What this script does in one sentence

It takes an applicant's four profile fields, cleans them the same way the training pipeline did, converts the result into a number vector, runs the saved Logistic Regression model to produce a confidence score for each of the five occupational categories, assigns each active job vacancy the score of its category, and returns the vacancies sorted from most suitable to least suitable.

---

## Why a separate inference script?

The training script (`machinelearning.py`) runs once offline and saves the pipeline. At runtime, the web system does not retrain — it only loads the saved pipeline and runs predictions. The inference logic is separated into `recommend.py` so that:

1. The text cleaning function (`clean_profile()`) is defined once in one place and imported by Flask — no risk of rewriting it differently in the web layer.
2. The recommendation logic can be tested independently before building the web system.
3. The script serves as the canonical reference for how inference works, documented separately from training.

---

## Step 1 — Text Cleaning (clean_profile)

The four profile fields are cleaned using the **exact same steps** applied in `preprocess.py` during training. This is a hard requirement — if any cleaning step differs, the words in the profile may not match the 356-term TF-IDF vocabulary, and the scores will be wrong.

| Step | What happens |
|---|---|
| Fill blank WORK EXPERIENCE | If empty, replaced with 'NO EXPERIENCE' |
| Lowercase | All four fields converted to lowercase |
| Remove special characters | `[^a-z0-9\s]` replaced with a space |
| Collapse whitespace | Multiple spaces collapsed into one |
| Strip numeric noise | Duration prefixes (`5 mos as`, `2 years as`) removed from WORK EXPERIENCE only |
| Concatenate | `EDUC LEVEL + PREFERRED POSITION + SKILLS + WORK EXPERIENCE` joined into one string |

**Why the cleaning must be identical:**
The TF-IDF vectorizer learned its 356-word vocabulary and IDF weights from training profiles that were cleaned by `preprocess.py`. At inference time, the same vectorizer maps words from the new profile against that same vocabulary. If the new profile contains words that were cleaned differently — for example, a comma left in because special character removal was skipped — those words become unrecognized tokens and their TF-IDF scores drop to zero. The classifier then makes its decision based on an incomplete representation of the applicant's profile.

---

## Step 2 — TF-IDF Vectorization

The cleaned PROFILE_TEXT string is passed to the fitted TF-IDF vectorizer loaded from `recommendation_pipeline.pkl`. The vectorizer converts the string into a sparse vector of 356 numerical weights — one weight per term in the vocabulary.

The vectorizer is not refitted. It was fitted once during training on 866 training records. At inference time, only `transform()` is called, applying the already-fixed vocabulary and IDF weights to the new profile. This is the same constraint enforced during training: the test set was also only transformed, never used to refit the vectorizer.

---

## Step 3 — predict_proba()

The 356-term vector is passed to the saved Logistic Regression classifier. The classifier runs `predict_proba()` — not `predict()`.

**Why predict_proba() and not predict():**

| Method | Output | Use |
|---|---|---|
| `predict()` | Single winning category label | Classification only — no confidence information |
| `predict_proba()` | Probability score for each of the 5 categories | Recommendation ranking — every category gets a score |

`predict_proba()` returns five numbers that sum to 1.0. Each number represents the model's confidence that the applicant's profile belongs to that occupational category. Using these probabilities as suitability scores means:

- Vacancies in the top category get the highest score
- Vacancies in secondary categories still get a meaningful score rather than zero
- If no active vacancies exist in the top category, vacancies from the next-best category rank above the rest
- The staff always receives a ranked list regardless of which categories currently have open positions

---

## Step 4 — Score Assignment

Each active job vacancy in the database belongs to one of the five occupational categories. The vacancy is assigned the `predict_proba()` score of its category:

```
vacancy category → look up its probability score → assign as suitability score
```

All vacancies under the same occupational category receive the same suitability score — the model scores categories, not individual job titles. Two vacancies under Sales/Service/Retail both receive the Sales/Service/Retail probability score.

---

## Step 5 — Sort and Rank

The scored vacancies are sorted in descending order by suitability score. The vacancy with the highest score receives Rank 1. Only the top 5 vacancies are returned. If multiple vacancies share the same score (same category), they are sorted among themselves in the order they appear in the database query (typically by date added or employer name, determined by the Flask application).

---

## Step 6 — Output

The function returns a list of dictionaries, each containing:

| Field | Type | Description |
|---|---|---|
| `rank` | int | Position in the ranked list (1 = best match) |
| `title` | str | Job title |
| `employer` | str | Employer name |
| `category` | str | Occupational category |
| `suitability_score` | float | Raw probability (0.0 to 1.0) |
| `suitability_pct` | str | Formatted percentage (e.g. '82.4%') |

In the Flask application, this list is passed directly to the Jinja2 template that renders the Job Recommendation tab. The staff sees the ranked list with suitability percentages and decides which vacancy to refer the applicant to.

---

## Flask Integration Notes

When the Flask application is built, the following applies:

1. **Load pipeline at startup** — call `load_pipeline()` once when Flask starts, store the result in the app context. Do not reload on every request.

2. **Import clean_profile** — do not rewrite the text cleaning in the Flask route. Import `clean_profile()` from this file or copy it verbatim. Any difference in cleaning breaks the recommendation.

3. **Vacancies from database** — the `vacancies` parameter comes from a SQLite query for all active job vacancies. Each vacancy record must include its occupational category so the score can be assigned.

4. **Display** — pass the returned ranked list to the Jinja2 template. The `suitability_pct` field is ready to display directly.

---

## Output Summary

| Component | Description |
|---|---|
| `clean_profile()` | Canonical text cleaning function for inference — must match preprocess.py |
| `load_pipeline()` | Loads recommendation_pipeline.pkl from disk |
| `recommend()` | Full inference function: clean → vectorize → score → rank → return |
| Demo run (`__main__`) | Runs a sample profile against sample vacancies to verify the pipeline works end-to-end |
