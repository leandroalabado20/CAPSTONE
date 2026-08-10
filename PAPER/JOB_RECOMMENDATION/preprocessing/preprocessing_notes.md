# Data Preprocessing — Full Reasoning Notes
**Dataset:** PLACEMENT_DATASET.xlsx (1,451 raw records × 44 columns)
**Pipeline output:** `preprocessed_dataset.csv` (PROFILE_TEXT, OCCUPATIONAL CATEGORY, LABEL)
**Last run:** 2026-08-06 | **Final clean records:** 1,083

---

## Why preprocessing is needed at all

The raw PLACEMENT_DATASET.xlsx is an administrative export from PEIS (Philippine Employment Information System). Its structure is built for government record-keeping, not for machine learning. Raw records contain 44 columns (most of them administrative identifiers), free-text entries with mixed formatting, 628 missing values in WORK EXPERIENCE, and 88 unique job titles many of which appear in only one or two records. A classifier fed this raw data would learn noise, not occupational patterns. Every step below exists to eliminate a specific source of noise or incompatibility before TF-IDF vectorization runs.

---

## Step 1 — Load the dataset

**What happens:** The Excel file is read into memory using `pandas.read_excel(header=2)`.

**Why `header=2`:** PLACEMENT_DATASET.xlsx has two merged group-label rows at the top (rows 0–1: "PESO TRANSACTIONS ONLY", "REFERRAL FOR WAGE EMPLOYMENT", etc.) before the actual column names appear on row index 2. Without `header=2`, pandas reads row 0 as the header and all real column names become `Unnamed: N`. Setting `header=2` skips the two group-label rows so the correct names — EDUC LEVEL, PREFERRED POSITION, SKILLS, WORK EXPERIENCE, and the three POSITION columns — are immediately available. Column index 11 (the placement position) is immediately renamed to `JOB POSITION` to resolve the duplicate name ambiguity before any further processing.

**Why this tool:** Excel cannot perform regex operations, programmatic imputation, or label encoding. Python with pandas handles all of these in one reproducible script. The Excel file itself is never modified — this preserves the original source data for audit purposes.

**What the raw data looks like:** 1,451 rows × 44 columns. Most columns are administrative: office name, area type, area class, employer identifiers, SRS ID, personal details (name, birthdate, address, contact numbers), and encoder metadata. None of these contribute to occupational classification.

---

## Step 2 — Select 5 relevant columns

**What happens:** 39 of 44 columns are dropped. Only these five are kept:

| Column | Role |
|---|---|
| EDUC LEVEL | Feature — highest education attained |
| PREFERRED POSITION | Feature — stated job preference |
| SKILLS | Feature — declared skills |
| WORK EXPERIENCE | Feature — prior role history |
| JOB POSITION | Target — the actual job position the applicant was referred to |

`JOB POSITION` is the renamed column — originally column index 11 in the raw file, renamed immediately on load to avoid ambiguity with two other columns also named `POSITION` (columns 8 and 15, both empty in this dataset).

**Why these five specifically:** PESO staff confirmed in interviews that these are the four attributes they consult when deciding who to refer to a vacancy. JOB POSITION is the confirmed placement outcome, making it the ground truth label. The other 39 columns — employer names, SRS IDs, dates, personal contact data — carry zero occupational signal and would add noise if included.

**Why not COURSE:** EDUC LEVEL already captures the education signal at the classification level (college graduate, vocational, high school). COURSE is often blank or inconsistently encoded across records, and its granularity (specific degree name) does not generalize well across the dataset.

---

## Step 3 — Fill blank WORK EXPERIENCE with "NO EXPERIENCE"

**What happens:** 628 records (43.3% of the 1,451 raw records) have a blank WORK EXPERIENCE field. These blanks are replaced with the literal string `"NO EXPERIENCE"`.

**Why not delete these records:** Deleting 628 records would cut the dataset nearly in half and disproportionately remove first-time job seekers, who are exactly the population PESO CSJDM serves most frequently. Their absence of work history is itself a meaningful signal — a person with no experience has a different occupational profile than someone who lists 5 mos as CASHIER.

**Why "NO EXPERIENCE" and not an empty string or a zero:** TF-IDF treats an empty field as contributing nothing to the document vector. If WORK EXPERIENCE is blank, the concatenated PROFILE_TEXT simply skips that field's contribution entirely, as if the column did not exist for that record. Inserting "NO EXPERIENCE" ensures that the absence of experience is a detectable, repeatable token in the vocabulary — the classifier can learn to associate it with entry-level occupational categories rather than treating it as missing data.

**Why not impute with the most common work experience value:** Work experience entries are role-specific free text. There is no meaningful "average" work experience to impute. The absence of prior work is not an unknown value — it is a known fact about the applicant, and "NO EXPERIENCE" encodes that fact faithfully.

---

## Step 4 — Remove exact duplicate records

**What happens:** 368 records where all five retained columns (EDUC LEVEL, PREFERRED POSITION, SKILLS, WORK EXPERIENCE, JOB POSITION) are identical were identified and removed, keeping one instance. This leaves **1,083 records**.

**Why:** If the same profile appears in both training and test data, the model's test performance is artificially inflated. The model will appear to generalize when it is actually recognizing a record it has already seen. Duplicates in PEIS export files can arise from data re-entry, system re-submissions, or administrative corrections that left both copies in the export. All must be removed before the train-test split.

**Why all five columns and not a subset:** Using only some columns for deduplication risks removing records that are legitimately different applicants with similar profiles but different placement outcomes. The duplicate condition must include JOB POSITION to avoid accidentally removing two different people who happen to have the same skills but were referred to different jobs.

---

## Step 5 — Map Job Position to occupational category

**What happens:** Each record's JOB POSITION value is looked up in a predefined mapping table. Each title is assigned to one of five categories. In this run, all 1,083 post-deduplication records matched a known title — zero records were excluded at this step.

| Category | Records | Example titles |
|---|---|---|
| Warehouse and Logistics | 175 | WAREHOUSE HELPER, FORKLIFT OPERATOR, INVENTORY CLERK, BAGGER |
| Production and Manufacturing | 292 | PRODUCTION WORKER, WELDER, MACHINE TOOL MACHINE OPERATOR, FISHERY LABORER |
| Sales/Service/Retail | 317 | CASHIER, SALES CLERK, SERVICE CREW, MERCHANDISER |
| Clerical and Administrative | 149 | OFFICE CLERK, DATA ENCODER, ADMINISTRATIVE ASSISTANT, ACCOUNTING STAFF |
| General Services and Security | 150 | SECURITY GUARD, JANITOR, COMPANY DRIVER, UTILITY WORKER |
| **Total** | **1,083** | |

**Why consolidate 88 titles into 5 categories:** The raw JOB POSITION column has 88 unique values distributed across 1,083 records — an average of roughly 14 records per title, but the actual distribution is highly skewed. Many titles appear in only 1 or 2 records. A classifier trained on 88 classes with 1–2 examples per class cannot generalize. Consolidating to 5 categories ensures each class contains enough records for a valid stratified 80/20 train-test split and for the model to learn a stable decision boundary.

**Why these 5 categories:** They reflect the actual labor market served by PESO CSJDM. The groupings are based on the nature of work performed, not on sector or industry alone. Kitchen roles (KITCHEN CREW, ASSISTANT COOK) are placed under Production and Manufacturing because they involve physical production of a food product in a structured environment, not face-to-face retail service. Drivers and janitors fall under General Services and Security because they provide facility-level support functions rather than direct production or sales activities.

**Why exclude unrecognized titles rather than create an "Other" category:** An "Other" class would absorb all remaining noise and produce a category with no coherent occupational signal. The classifier would learn nothing useful from it, and its presence would distort the probability outputs for the other four categories. If a title cannot be mapped to a meaningful category, the record carries no usable label and cannot contribute to training.

---

## Step 6 — Convert all text to lowercase

**What happens:** All four feature columns are converted to lowercase using `.str.lower()`.

**Why:** Text matching in TF-IDF is case-sensitive by default. "CASHIER", "Cashier", and "cashier" would be counted as three separate vocabulary terms, each with its own IDF weight, even though they represent the same word. Lowercasing collapses all surface variants to a single token. This reduces vocabulary size and ensures that the frequency signal from any term is not artificially split across multiple casing variants.

**Why do this before special character removal:** Lowercasing first ensures that the subsequent regex pattern (which targets only lowercase letters `a-z`) applies cleanly to all characters. Order matters: if special characters are removed first, some encoding artifacts may survive in uppercase form.

---

## Step 7 — Remove special characters and punctuation

**What happens:** All characters that are not lowercase letters, digits, or spaces are replaced with a space. Multiple consecutive spaces are collapsed into one.

**Why:** Punctuation marks, parentheses, slashes, and other symbols that appear in SKILLS and WORK EXPERIENCE entries do not carry occupational meaning. A comma separating "CASHIER, SALESPERSON" and a slash in "SALES & MARKETING ASSISTANT" are delimiters, not features. Leaving them in the text would cause TF-IDF to generate tokens like `"cashier,"` and `"marketing"` as separate terms from `"cashier"` and `"marketing"`, inflating vocabulary and diluting term frequency counts.

**Why keep digits at this stage:** Digits are stripped in Step 8 specifically from WORK EXPERIENCE, where their presence is meaningful as duration markers. In EDUC LEVEL and other fields, digits may appear in legitimate contexts (e.g., a course code). Removing digits globally in Step 7 and then re-applying regex in Step 8 would be redundant. The targeted approach in Step 8 handles numeric noise more precisely.

---

## Step 8 — Strip numeric noise from WORK EXPERIENCE

**What happens:** A regex pattern removes duration prefixes (`X mos as`, `X years as`) and any remaining standalone numeric tokens from the WORK EXPERIENCE field only.

Example transformations:
- `"5 mos as cashier"` → `"cashier"`
- `"2 years as data encoder, 12 mos as office clerk"` → `"data encoder  office clerk"`
- `"no experience"` → `"no experience"` (unchanged)

**Why target WORK EXPERIENCE specifically:** The format of WORK EXPERIENCE entries in the dataset is almost uniformly `"[number] mos as [role title]"`. The number (duration) carries no occupational category signal — whether someone worked 2 months or 47 months as a cashier, the relevant token for classification is `"cashier"`, not the duration. If the numeric token survives into TF-IDF, the vocabulary fills up with number strings (`"5"`, `"47"`, `"12"`) that appear across many records but predict no specific occupational category. They would receive high term frequency but contribute noise to the document vectors.

**Why not rely on TF-IDF's IDF weighting to suppress these numbers automatically:** TF-IDF downweights terms that appear in many documents, but it does not eliminate them. Different numbers appear across different records, so each number token actually receives a relatively high IDF value (it is rare per-document while being common across documents). The result is that numeric tokens carry measurable weight in the final vectors without adding useful classification signal. Explicit stripping before vectorization is cleaner and more defensible.

**Why apply this step after lowercasing and punctuation removal:** Steps 6 and 7 normalize the text so the regex in Step 8 operates on a clean, consistent string. If applied before lowercasing, the regex would need case-insensitive flags and would still risk missing edge cases from inconsistent formatting in the raw data.

---

## Step 9 — Concatenate 4 fields into one PROFILE_TEXT string

**What happens:** The four feature columns are joined into a single string per record:

```
PROFILE_TEXT = EDUC LEVEL + " " + PREFERRED POSITION + " " + SKILLS + " " + WORK EXPERIENCE
```

**Why concatenate rather than vectorize each field separately:** TF-IDF operates on documents. Each record needs to be a single document so that all profile terms contribute to one unified feature vector. If fields were vectorized separately and their vectors concatenated, they would need to be weighted relative to each other — a hyperparameter that has no natural value for this dataset. Treating the concatenated profile as a single document means TF-IDF assigns weights based on how discriminative each term is across the entire corpus of profiles, regardless of which field it came from.

**Why this field order (EDUC LEVEL first, WORK EXPERIENCE last):** The order affects nothing in TF-IDF because TF-IDF is a bag-of-words method — it counts term occurrences without regard to position. The order is set for readability of the intermediate output only.

**Why not include JOB POSITION in the concatenation:** JOB POSITION is the target label, not a feature. Including it in PROFILE_TEXT would cause data leakage — the classifier would learn to predict the label from itself, producing inflated performance metrics that would not hold on any real new applicant record (which, by definition, has no confirmed JOB POSITION yet).

---

## Step 10 — Label-encode the occupational category

**What happens:** Each occupational category string is replaced with an integer from 0 to 4:

| Integer | Category |
|---|---|
| 0 | Warehouse and Logistics |
| 1 | Production and Manufacturing |
| 2 | Sales/Service/Retail |
| 3 | Clerical and Administrative |
| 4 | General Services and Security |

**Why encode as integers:** scikit-learn classifiers (Logistic Regression, Random Forest, Naïve Bayes) require numeric targets. String category names cannot be passed directly as the `y` argument to `.fit()`. Integer encoding is the standard approach for multi-class classification targets.

**Why this specific order:** The order is arbitrary — no ordinal relationship exists between categories. The mapping is fixed in the script so that the encoding is deterministic and reproducible across every run. The deployed model stores this mapping to reverse-decode predictions (integer → category name) when displaying recommendations to PESO staff.

**Why label encoding and not one-hot encoding:** One-hot encoding is for features, not targets. Multi-class classifiers in scikit-learn expect a single integer label per record as the target, not a binary array. One-hot encoding applied to the target would require a multi-label setup, which does not apply here — every applicant belongs to exactly one occupational category.

---

## Output

The final CSV (`preprocessed_dataset.csv`) contains three columns:

| Column | Description |
|---|---|
| PROFILE_TEXT | Cleaned, concatenated profile string — input to TF-IDF |
| OCCUPATIONAL CATEGORY | Human-readable category name — for reference |
| LABEL | Integer label 0–4 — target for classifier training |

**Run summary (2026-08-06):**

| Stage | Count |
|---|---|
| Raw records loaded | 1,451 |
| Blank WORK EXPERIENCE filled | 628 |
| Exact duplicates removed | 368 |
| Records excluded (unrecognized title) | 0 |
| **Final clean records** | **1,083** |

**Label distribution:**

| Label | Category | Records |
|---|---|---|
| 0 | Warehouse and Logistics | 175 |
| 1 | Production and Manufacturing | 292 |
| 2 | Sales/Service/Retail | 317 |
| 3 | Clerical and Administrative | 149 |
| 4 | General Services and Security | 150 |

This file is the direct input to the TF-IDF vectorizer and classifier training script. No further preprocessing is required at the TF-IDF stage beyond what `TfidfVectorizer` handles internally (tokenization, IDF computation, L2 normalization of output vectors).
