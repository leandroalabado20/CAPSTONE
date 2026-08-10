# ML Training Pipeline — Notes and Actual Results
**Script:** `machinelearning.py`
**Input:** `../preprocessing/preprocessed_dataset.csv`
**Output:** `recommendation_pipeline.pkl`
**Last run:** 2026-08-06

---

## What this script does in one sentence

It takes the clean text profiles produced by `preprocess.py`, converts them into numbers the computer can work with (TF-IDF), trains three classification algorithms on those numbers, picks the one that performs best across all five job categories equally, and saves it so the web system can use it to recommend jobs without retraining.

---

## Step 1 — Load the preprocessed dataset

The script reads `preprocessed_dataset.csv` which was produced by `preprocess.py`. That file has exactly three columns:

| Column | What it contains |
|---|---|
| PROFILE_TEXT | One text string per applicant combining their education, preferred position, skills, and work experience — all cleaned and normalized |
| OCCUPATIONAL CATEGORY | Human-readable category name — for reference |
| LABEL | An integer 0–4 representing the occupational category that applicant was placed into |

**Actual dataset loaded:**

| Label | Occupational Category | Records | Share |
|---|---|---|---|
| 0 | Warehouse and Logistics | 175 | 16.2% |
| 1 | Production and Manufacturing | 292 | 27.0% |
| 2 | Sales/Service/Retail | 317 | 29.3% |
| 3 | Clerical and Administrative | 149 | 13.8% |
| 4 | General Services and Security | 150 | 13.9% |
| | **Total** | **1,083** | 100% |

---

## Step 2 — 80/20 Stratified Train-Test Split

The 1,083 records are divided into two groups:
- **Training set (866 records)** — the model sees these and learns from them
- **Test set (217 records)** — the model never sees these until evaluation

**Actual split result:**

| Occupational Category | Training | Test |
|---|---|---|
| Warehouse and Logistics | 140 | 35 |
| Production and Manufacturing | 234 | 58 |
| Sales/Service/Retail | 253 | 64 |
| Clerical and Administrative | 119 | 30 |
| General Services and Security | 120 | 30 |
| **Total** | **866** | **217** |

**Why 80/20?**
This proportion is the standard in the three classification studies the paper reviewed (Chihab et al. 2025, Imianvan et al. 2024, Darma et al. 2026). It gives the model enough data to learn from while keeping enough records aside for a meaningful performance test.

**Why stratified?**
The five categories are not evenly distributed. Stratified sampling guarantees that each category appears in both partitions in the same proportion as the full dataset, so no category ends up underrepresented or missing from the test set.

**Why split before TF-IDF?**
If TF-IDF is fitted on the full dataset before splitting, the vectorizer computes IDF weights using documents from the test set — the model absorbs information from records it is supposed to encounter for the first time during evaluation. Performance scores would be inflated and unreliable. Splitting first and fitting TF-IDF only on training data prevents this (data leakage prevention).

---

## Step 3 — Fit TF-IDF Vectorizer on Training Set Only

TF-IDF (Term Frequency – Inverse Document Frequency) converts text into numbers. It gives each word in a profile a score based on:

1. **How often that word appears in this specific profile** (Term Frequency)
2. **How rare that word is across all training profiles** (Inverse Document Frequency)

Words that appear in almost every profile (like "college" or "graduate") get low scores — they do not help distinguish one category from another. Words that appear in only a few profiles (like "forklift" or "welder") get high scores — they are strong signals for specific categories.

**Actual TF-IDF output:**

| | Value |
|---|---|
| Vocabulary size | 356 unique terms |
| Training matrix | 866 profiles × 356 words |
| Test matrix | 217 profiles × 356 words |

**fit_transform on training** — builds the 356-word vocabulary and computes IDF weights from 866 training records only, then converts them to vectors.

**transform on test** — applies the already-fixed vocabulary and IDF weights to the 217 test records. No new vocabulary is learned. This simulates exactly what happens at runtime when a new applicant's profile is vectorized.

---

## Step 4 — Train 3 Classifiers

All three classifiers receive the same 866 training vectors and the same 866 labels.

### Logistic Regression
Learns a weight for each of the 356 words per category. If "cashier" has a high weight for Sales/Service/Retail, profiles with a high "cashier" score are likely Sales/Service/Retail. Uses one-vs-rest — one binary classifier per category — and the category with the highest confidence wins.

### Random Forest
Builds 100 decision trees, each trained on a random sample of training records and a random subset of the 356 vocabulary terms. The final prediction is the majority vote across all 100 trees.

### Naïve Bayes
Counts how often each word appears in profiles belonging to each category, then uses those counts to compute the probability that a new profile belongs to each category. Works well for text classification even with limited training data.

**Why compare all three?**
The RRL shows that the same three algorithms rank differently depending on the dataset — Logistic Regression won on one, Random Forest on another, Naïve Bayes on a third. The PESO dataset has its own characteristics, so the winner cannot be assumed in advance.

---

## Step 5 — Evaluate Each Classifier on the Test Set

Each classifier predicts a category for each of the 217 test records and results are compared to actual categories.

### Logistic Regression

| Metric | Value |
|---|---|
| Accuracy | 0.7281 (72.8%) |
| Macro Precision | 0.7494 |
| Macro Recall | 0.7291 |
| **Macro F1-Score** | **0.7370** |
| Weighted F1-Score | 0.7264 |

**Confusion Matrix:**

| Actual \ Predicted | Warehouse | Production | Sales | Clerical | General |
|---|---|---|---|---|---|
| Warehouse and Logistics | **19** | 8 | 6 | 2 | 0 |
| Production and Manufacturing | 5 | **39** | 11 | 3 | 0 |
| Sales/Service/Retail | 4 | 7 | **51** | 2 | 0 |
| Clerical and Administrative | 0 | 2 | 6 | **21** | 1 |
| General Services and Security | 1 | 0 | 1 | 0 | **28** |

**Per-category breakdown:**

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Warehouse and Logistics | 0.6552 | 0.5429 | 0.5938 | 35 |
| Production and Manufacturing | 0.6964 | 0.6724 | 0.6842 | 58 |
| Sales/Service/Retail | 0.6800 | 0.7969 | 0.7338 | 64 |
| Clerical and Administrative | 0.7500 | 0.7000 | 0.7241 | 30 |
| General Services and Security | 0.9655 | 0.9333 | 0.9492 | 30 |

---

### Random Forest

| Metric | Value |
|---|---|
| Accuracy | 0.6590 (65.9%) |
| Macro Precision | 0.6847 |
| Macro Recall | 0.6641 |
| **Macro F1-Score** | **0.6679** |
| Weighted F1-Score | 0.6540 |

**Confusion Matrix:**

| Actual \ Predicted | Warehouse | Production | Sales | Clerical | General |
|---|---|---|---|---|---|
| Warehouse and Logistics | **14** | 12 | 5 | 3 | 1 |
| Production and Manufacturing | 5 | **34** | 16 | 2 | 1 |
| Sales/Service/Retail | 3 | 9 | **47** | 5 | 0 |
| Clerical and Administrative | 0 | 2 | 5 | **22** | 1 |
| General Services and Security | 0 | 2 | 2 | 0 | **26** |

**Per-category breakdown:**

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Warehouse and Logistics | 0.6364 | 0.4000 | 0.4912 | 35 |
| Production and Manufacturing | 0.5763 | 0.5862 | 0.5812 | 58 |
| Sales/Service/Retail | 0.6267 | 0.7344 | 0.6763 | 64 |
| Clerical and Administrative | 0.6875 | 0.7333 | 0.7097 | 30 |
| General Services and Security | 0.8966 | 0.8667 | 0.8814 | 30 |

---

### Naïve Bayes

| Metric | Value |
|---|---|
| Accuracy | 0.7051 (70.5%) |
| Macro Precision | 0.7680 |
| Macro Recall | 0.6912 |
| **Macro F1-Score** | **0.7098** |
| Weighted F1-Score | 0.6979 |

**Confusion Matrix:**

| Actual \ Predicted | Warehouse | Production | Sales | Clerical | General |
|---|---|---|---|---|---|
| Warehouse and Logistics | **15** | 12 | 7 | 1 | 0 |
| Production and Manufacturing | 2 | **35** | 18 | 3 | 0 |
| Sales/Service/Retail | 2 | 5 | **57** | 0 | 0 |
| Clerical and Administrative | 0 | 1 | 10 | **18** | 1 |
| General Services and Security | 0 | 0 | 2 | 0 | **28** |

**Per-category breakdown:**

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Warehouse and Logistics | 0.7895 | 0.4286 | 0.5556 | 35 |
| Production and Manufacturing | 0.6604 | 0.6034 | 0.6306 | 58 |
| Sales/Service/Retail | 0.6064 | 0.8906 | 0.7215 | 64 |
| Clerical and Administrative | 0.8182 | 0.6000 | 0.6923 | 30 |
| General Services and Security | 0.9655 | 0.9333 | 0.9492 | 30 |

---

## Step 6 — Compare Macro F1 and Select Best

| Classifier | Accuracy | Macro F1 | Weighted F1 |
|---|---|---|---|
| **Logistic Regression** | **0.7281** | **0.7370** | **0.7264** |
| Naïve Bayes | 0.7051 | 0.7098 | 0.6979 |
| Random Forest | 0.6590 | 0.6679 | 0.6540 |

**Winner: Logistic Regression** with Macro F1-Score of **0.7370**.

This is consistent with Sankarasetty et al. (2023) from the RRL, where Logistic Regression outperformed Random Forest and Naïve Bayes on a similar profile-based job recommendation dataset.

**Why Macro F1 and not Accuracy?**
Accuracy alone would also point to Logistic Regression here, but Macro F1 is the correct criterion because it equally weights all five categories. A model that fails on any one category — regardless of its size — is penalized just as heavily as failure on the largest category.

---

## Step 7 — Save the Pipeline

The fitted TF-IDF vectorizer and Logistic Regression classifier are saved together in `recommendation_pipeline.pkl`.

**Why save them together?**
The vectorizer and model are permanently paired. The model learned patterns from TF-IDF vectors built with a specific 356-word vocabulary and specific IDF weights. Using any other vectorizer at prediction time would produce mismatched term weights and the recommendations would be meaningless.

**What the Flask app does with this file at runtime:**
1. Staff selects or enters an applicant's profile (4 fields)
2. The 4 fields are cleaned and joined into one PROFILE_TEXT string
3. The saved TF-IDF vectorizer converts it to a 356-term vector
4. The saved Logistic Regression model runs `predict_proba()` → returns a probability score for all 5 categories
5. Each active job vacancy gets the score of its occupational category
6. Vacancies are ranked by score and displayed to PESO staff

---

## Output

| File | Contents |
|---|---|
| `recommendation_pipeline.pkl` | Dict: fitted TF-IDF vectorizer (356 terms), trained Logistic Regression model, model name, label map (0–4 → category name) |

This single file is everything the Flask application needs to make job recommendations.
