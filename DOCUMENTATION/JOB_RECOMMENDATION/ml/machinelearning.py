"""
Machine Learning Training Script — PESO CSJDM Job Recommendation System

What this script does:
    Takes the cleaned applicant profiles from preprocessing,
    converts them into numbers the computer can work with (TF-IDF),
    trains and compares three classification algorithms,
    picks the best one, and saves it so the web system can
    use it to recommend jobs without retraining.

Input  : ../preprocessing/preprocessed_dataset.csv
Output : recommendation_pipeline.pkl

How to run (from the ml/ folder):
    python machinelearning.py
"""

import os
import time
import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model         import LogisticRegression
from sklearn.ensemble             import RandomForestClassifier
from sklearn.naive_bayes          import MultinomialNB
from sklearn.model_selection      import train_test_split
from sklearn.metrics              import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

# ── PATHS ──────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH    = os.path.join(BASE_DIR, '..', 'preprocessing', 'preprocessed_dataset.csv')
OUTPUT_PATH         = os.path.join(BASE_DIR, 'recommendation_pipeline.pkl')
TFIDF_TRAIN_PATH    = os.path.join(BASE_DIR, 'tfidf_train_matrix.xlsx')
TFIDF_TEST_PATH     = os.path.join(BASE_DIR, 'tfidf_test_matrix.xlsx')

# ── OCCUPATIONAL CATEGORY LABELS ───────────────────────────────────────────────
CATEGORIES = {
    0: 'Warehouse and Logistics',
    1: 'Production and Manufacturing',
    2: 'Sales/Service/Retail',
    3: 'Clerical and Administrative',
    4: 'General Services and Security',
}

# ── DISPLAY HELPERS ────────────────────────────────────────────────────────────
def section(title):
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")

def line():
    print(f"  {'-' * 63}")


# ==============================================================================
# STEP 1 — LOAD THE PREPROCESSED DATASET
# ==============================================================================
section("STEP 1  |  LOAD THE PREPROCESSED DATASET")

print("""
  We start by loading the cleaned dataset produced by preprocess.py.
  Each row in this file represents one applicant and contains:

    PROFILE_TEXT  — a single text string combining the applicant's
                    education level, preferred position, skills,
                    and work experience (already cleaned)
    LABEL         — a number (0 to 4) representing which occupational
                    category that applicant was placed into
""")

df = pd.read_csv(INPUT_PATH)

print(f"  File loaded  : {INPUT_PATH}")
print(f"  Total records: {len(df):,}")

print(f"\n  How the records are spread across the 5 job categories:")
line()
print(f"  {'Label':<6} {'Occupational Category':<35} {'Records':>8} {'Share':>7}")
line()
for label, name in CATEGORIES.items():
    count = (df['LABEL'] == label).sum()
    pct   = count / len(df) * 100
    print(f"  {label:<6} {name:<35} {count:>8,} {pct:>6.1f}%")
line()

print(f"\n  Sample profile texts from the dataset:")
for _, row in df.sample(3, random_state=1).iterrows():
    print(f"\n  Category : {CATEGORIES[row['LABEL']]}")
    print(f"  Text     : {row['PROFILE_TEXT'][:110]}...")


# ==============================================================================
# STEP 2 — SPLIT INTO TRAINING SET AND TEST SET (80/20)
# ==============================================================================
section("STEP 2  |  SPLIT INTO TRAINING SET AND TEST SET  (80 / 20)")

print("""
  Before training, we divide the dataset into two groups:

    Training set (80%) — the algorithms study these records
                         and learn the patterns inside them.
    Test set     (20%) — kept completely hidden from the algorithms
                         during training. Used only at the end to
                         measure how well each algorithm performs
                         on records it has never seen before.

  We use STRATIFIED splitting — this means each job category keeps
  its same proportion in both halves. Without this, a category with
  few records might end up with zero records in the test set, making
  it impossible to fairly evaluate performance on that group.

  IMPORTANT: This split happens BEFORE TF-IDF conversion.
  If we converted text to numbers first, the conversion would
  accidentally use information from the test records, making the
  results look better than they really are (data leakage).
""")

X = df['PROFILE_TEXT']
y = df['LABEL']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"  Total records : {len(df):,}")
print(f"  Training set  : {len(X_train):,} records  (80%)")
print(f"  Test set      : {len(X_test):,}  records  (20%)")

print(f"\n  Category breakdown after split:")
line()
print(f"  {'Occupational Category':<35} {'Training':>9} {'Test':>6}")
line()
for label, name in CATEGORIES.items():
    tr = (y_train == label).sum()
    te = (y_test  == label).sum()
    print(f"  {name:<35} {tr:>9,} {te:>6,}")
line()


# ==============================================================================
# STEP 3 — CONVERT TEXT TO NUMBERS USING TF-IDF
# ==============================================================================
section("STEP 3  |  CONVERT PROFILE TEXT TO NUMBERS  (TF-IDF)")

print("""
  Algorithms cannot read text directly — they need numbers.
  TF-IDF (Term Frequency – Inverse Document Frequency) converts
  each applicant's profile text into a row of numbers.

  How it works:
    - Every unique word across all training profiles becomes a column.
    - Each applicant gets a score per word based on:
        * How often that word appears in THEIR profile (Term Frequency)
        * How rare that word is across ALL profiles (Inverse Doc Frequency)
    - Common words that appear in almost every profile (e.g. "graduate")
      get low scores — they don't help tell categories apart.
    - Rare words specific to a few profiles (e.g. "forklift", "welder")
      get high scores — they are strong signals for a specific category.

  Rule: TF-IDF is FITTED on the training set only, then APPLIED to both.
  This way the test set stays completely unseen during the learning phase.
""")

vectorizer = TfidfVectorizer(sublinear_tf=True)

print(f"  Converting {len(X_train):,} training profiles to number vectors...")
X_train_tfidf = vectorizer.fit_transform(X_train)

print(f"  Applying the same conversion rules to {len(X_test):,} test profiles...")
X_test_tfidf  = vectorizer.transform(X_test)

vocab = vectorizer.get_feature_names_out()
print(f"\n  Unique words in vocabulary : {len(vocab):,}")
print(f"  Training matrix size       : {X_train_tfidf.shape[0]:,} profiles × {X_train_tfidf.shape[1]:,} words")
print(f"  Test matrix size           : {X_test_tfidf.shape[0]:,}  profiles × {X_test_tfidf.shape[1]:,} words")
print(f"\n  Sample words from vocabulary (first 30):")
print(f"  {list(vocab[:30])}")

if os.path.exists(TFIDF_TRAIN_PATH) and os.path.exists(TFIDF_TEST_PATH):
    print(f"\n  TF-IDF Excel files already exist — skipping export.")
    print(f"  {TFIDF_TRAIN_PATH}")
    print(f"  {TFIDF_TEST_PATH}")
else:
    print(f"\n  Saving TF-IDF matrices to Excel...")

    # Training set
    train_label_df = df.loc[X_train.index].reset_index(drop=True)
    train_tfidf_df = pd.DataFrame(X_train_tfidf.toarray(), columns=vocab)
    train_export   = pd.concat([train_label_df, train_tfidf_df], axis=1)
    train_export.to_excel(TFIDF_TRAIN_PATH, index=False)
    print(f"  Saved training set : {TFIDF_TRAIN_PATH}  ({len(train_export):,} rows)")

    # Test set
    test_label_df = df.loc[X_test.index].reset_index(drop=True)
    test_tfidf_df = pd.DataFrame(X_test_tfidf.toarray(), columns=vocab)
    test_export   = pd.concat([test_label_df, test_tfidf_df], axis=1)
    test_export.to_excel(TFIDF_TEST_PATH, index=False)
    print(f"  Saved test set     : {TFIDF_TEST_PATH}  ({len(test_export):,} rows)")


# ==============================================================================
# STEP 4 — TRAIN ALL THREE CLASSIFIERS
# ==============================================================================
section("STEP 4  |  TRAIN THE THREE CLASSIFIERS")

print("""
  Three classification algorithms are trained on the same training set.
  All three see the exact same data so that any difference in results
  comes from the algorithm itself — not from different data.

  Logistic Regression
    Learns a weight for each word per category. A word like "cashier"
    gets a high weight for Sales/Service/Retail if it appears often
    in profiles that were placed in that category.

  Random Forest
    Builds 100 decision trees, each trained on a random portion of
    the data. The final answer is decided by majority vote across all
    100 trees — this makes it more stable than a single tree.

  Naïve Bayes
    Calculates the probability that each word belongs to each category
    based on how often it appeared there during training. Works well
    for text classification even with limited data.
""")

classifiers = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest'      : RandomForestClassifier(n_estimators=100, random_state=42),
    'Naive Bayes'        : MultinomialNB(),
}

trained = {}
for name, clf in classifiers.items():
    print(f"  Training {name}...", end='', flush=True)
    start = time.time()
    clf.fit(X_train_tfidf, y_train)
    elapsed = time.time() - start
    trained[name] = clf
    print(f"  done  ({elapsed:.2f} seconds)")

print(f"\n  All three algorithms finished training.")


# ==============================================================================
# STEP 5 — EVALUATE EACH CLASSIFIER ON THE TEST SET
# ==============================================================================
section("STEP 5  |  EVALUATE EACH CLASSIFIER ON THE TEST SET")

print("""
  Each classifier now predicts the job category for the 217 test
  profiles it has never seen before. We compare those predictions
  to the actual categories to measure performance.

  Metrics used:
    Accuracy       — overall percentage of correct predictions
    Macro F1-Score — average F1 across all 5 categories equally
                     (the main metric we use to pick the best model)
    Confusion Matrix — shows exactly where each classifier got it
                       right and where it mixed up categories
""")

results = {}

for name, clf in trained.items():

    y_pred      = clf.predict(X_test_tfidf)
    acc         = accuracy_score(y_test, y_pred)
    macro_prec  = precision_score(y_test, y_pred, average='macro',    zero_division=0)
    macro_rec   = recall_score   (y_test, y_pred, average='macro',    zero_division=0)
    macro_f1    = f1_score       (y_test, y_pred, average='macro',    zero_division=0)
    weighted_f1 = f1_score       (y_test, y_pred, average='weighted', zero_division=0)
    cm          = confusion_matrix(y_test, y_pred)

    results[name] = {
        'accuracy'   : acc,
        'macro_prec' : macro_prec,
        'macro_rec'  : macro_rec,
        'macro_f1'   : macro_f1,
        'weighted_f1': weighted_f1,
        'cm'         : cm,
        'clf'        : clf,
    }

    print(f"\n  [ {name} ]")
    line()
    print(f"  Accuracy          : {acc:.4f}  ({acc*100:.1f}% of test records correct)")
    print(f"  Macro Precision   : {macro_prec:.4f}")
    print(f"  Macro Recall      : {macro_rec:.4f}")
    print(f"  Macro F1-Score    : {macro_f1:.4f}   <- main selection criterion")
    print(f"  Weighted F1-Score : {weighted_f1:.4f}")
    line()

    print(f"\n  Confusion Matrix  (rows = Actual category | cols = Predicted category)")
    print(f"  Diagonal cells = correct predictions | Off-diagonal = mistakes")
    line()
    col_headers = [f"P{i}" for i in range(5)]
    print(f"  {'Actual \\ Predicted':<35} " + "  ".join(f"{h:>4}" for h in col_headers))
    line()
    for i, row_label in CATEGORIES.items():
        short   = row_label[:33]
        row_str = "  ".join(f"{v:>4}" for v in cm[i])
        print(f"  A{i} {short:<33} {row_str}")
    line()

    print(f"\n  Per-category breakdown:")
    print(classification_report(
        y_test, y_pred,
        target_names=[CATEGORIES[i] for i in range(5)],
        zero_division=0,
        digits=4,
    ))


# ==============================================================================
# STEP 6 — COMPARE MACRO F1-SCORES AND SELECT THE BEST CLASSIFIER
# ==============================================================================
section("STEP 6  |  COMPARE AND SELECT THE BEST CLASSIFIER")

print("""
  We compare all three classifiers using Macro F1-Score as the
  deciding metric — not Accuracy.

  Why Macro F1 and not Accuracy?
    Accuracy counts the total correct predictions regardless of category.
    A model that always predicts Sales/Service/Retail (the biggest group)
    would score high on accuracy but fail every applicant who belongs
    to Clerical, Warehouse, or other categories.

    Macro F1 scores each of the 5 categories separately and averages
    them with equal weight. A failure on any one category — big or small
    — lowers the score just as much as a failure on any other.
    This ensures the selected model works fairly across ALL categories.
""")

print(f"  {'Classifier':<25} {'Accuracy':>10} {'Macro F1':>10} {'Weighted F1':>13}")
line()
for name, res in results.items():
    print(f"  {name:<25} {res['accuracy']:>10.4f} {res['macro_f1']:>10.4f} {res['weighted_f1']:>13.4f}")
line()

best_name = max(results, key=lambda n: results[n]['macro_f1'])
best_f1   = results[best_name]['macro_f1']

print(f"\n  Winner : {best_name}")
print(f"  Macro F1-Score : {best_f1:.4f}")
print(f"\n  This algorithm will be saved and used by the web system.")


# ==============================================================================
# STEP 7 — SAVE THE PIPELINE
# ==============================================================================
section("STEP 7  |  SAVE THE PIPELINE TO DISK")

print("""
  The TF-IDF vectorizer and the best-performing classifier are saved
  together into one file: recommendation_pipeline.pkl

  Why save them together?
    At recommendation time, the Flask web app needs to convert a
    new applicant's profile text into numbers the exact same way
    it was done during training. If we used a different converter,
    the numbers would not match what the model learned from,
    and the recommendations would be meaningless.

    Saving both as a pair guarantees they are always used together.

  What the Flask app does with this file at runtime:
    1. Staff selects or enters an applicant's profile
    2. The 4 fields are cleaned and joined into one text string
    3. The saved TF-IDF vectorizer converts it to a number vector
    4. The saved classifier runs predict_proba() on that vector
    5. Each active job vacancy gets the score of its category
    6. Vacancies are ranked by score and shown to PESO staff
""")

pipeline = {
    'vectorizer' : vectorizer,
    'model'      : results[best_name]['clf'],
    'model_name' : best_name,
    'label_map'  : CATEGORIES,
}

joblib.dump(pipeline, OUTPUT_PATH)

print(f"  Saved to : {OUTPUT_PATH}")
print(f"\n  Contents of the saved file:")
print(f"    vectorizer  — TF-IDF with vocabulary of {len(vocab):,} terms")
print(f"    model       — trained {best_name}")
print(f"    model_name  — '{best_name}'")
print(f"    label_map   — maps label numbers back to category names")


# ==============================================================================
# DONE
# ==============================================================================
section("TRAINING COMPLETE")

print(f"""
  Best algorithm    : {best_name}
  Macro F1-Score    : {best_f1:.4f}
  Pipeline saved at : {OUTPUT_PATH}
  Status            : Ready for job recommendation inference.
""")
print(f"{'=' * 65}\n")
