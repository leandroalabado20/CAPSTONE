"""
Job Recommendation Inference Script — PESO CSJDM Job Recommendation System

What this script does:
    Takes an applicant's four profile fields as input,
    cleans the text the same way preprocess.py does,
    converts it to a number vector using the saved TF-IDF vectorizer,
    runs the saved Logistic Regression classifier to get probability scores
    for each of the five occupational categories,
    then ranks a given list of active job vacancies by their suitability score
    and returns the ranked list.

Input  : 4 profile fields + list of active vacancies
Output : Ranked vacancy list with suitability scores

How to run (from the recommendation/ folder):
    python recommend.py
"""

import os
import re
import joblib

# ── PATHS ──────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PIPELINE_PATH = os.path.join(BASE_DIR, '..', 'ml', 'recommendation_pipeline.pkl')

# ── OCCUPATIONAL CATEGORY LABELS ───────────────────────────────────────────────
CATEGORIES = {
    0: 'Warehouse and Logistics',
    1: 'Production and Manufacturing',
    2: 'Sales/Service/Retail',
    3: 'Clerical and Administrative',
    4: 'General Services and Security',
}


# ==============================================================================
# TEXT CLEANING — must exactly replicate preprocess.py
# ==============================================================================

def strip_numeric_noise(text: str) -> str:
    """Remove duration prefixes and standalone numbers from WORK EXPERIENCE.

    '5 mos as cashier' -> 'cashier'
    '2 years as data encoder, 12 mos as office clerk' -> 'data encoder  office clerk'
    """
    text = re.sub(r'\b\d+\s*(?:mos?|years?)\s*as\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def clean_profile(educ_level: str,
                  preferred_position: str,
                  skills: str,
                  work_experience: str) -> str:
    """
    Clean and concatenate the four applicant profile fields into one PROFILE_TEXT
    string using the exact same steps applied in preprocess.py during training.

    Steps applied:
        1. Fill blank WORK EXPERIENCE with 'NO EXPERIENCE'
        2. Lowercase all four fields
        3. Remove special characters and punctuation
        4. Collapse whitespace
        5. Strip numeric noise from WORK EXPERIENCE
        6. Concatenate: EDUC LEVEL + PREFERRED POSITION + SKILLS + WORK EXPERIENCE
    """
    # Step 1 — fill blank WORK EXPERIENCE
    if not work_experience or not work_experience.strip():
        work_experience = 'NO EXPERIENCE'

    fields = {
        'educ_level'         : educ_level,
        'preferred_position' : preferred_position,
        'skills'             : skills,
        'work_experience'    : work_experience,
    }

    # Step 2 — lowercase
    fields = {k: v.lower() for k, v in fields.items()}

    # Step 3 & 4 — remove special characters, collapse whitespace
    fields = {k: re.sub(r'[^a-z0-9\s]', ' ', v) for k, v in fields.items()}
    fields = {k: re.sub(r'\s+', ' ', v).strip()  for k, v in fields.items()}

    # Step 5 — strip numeric noise from WORK EXPERIENCE only
    fields['work_experience'] = strip_numeric_noise(fields['work_experience'])

    # Step 6 — concatenate in the same order as preprocess.py
    profile_text = (
        fields['educ_level']         + ' ' +
        fields['preferred_position'] + ' ' +
        fields['skills']             + ' ' +
        fields['work_experience']
    )
    return re.sub(r'\s+', ' ', profile_text).strip()


# ==============================================================================
# LOAD PIPELINE
# ==============================================================================

def load_pipeline(path: str = PIPELINE_PATH) -> dict:
    """Load the saved TF-IDF vectorizer and Logistic Regression model from disk."""
    pipeline = joblib.load(path)
    return pipeline


# ==============================================================================
# RECOMMENDATION FUNCTION
# ==============================================================================

def recommend(educ_level: str,
              preferred_position: str,
              skills: str,
              work_experience: str,
              vacancies: list,
              pipeline: dict) -> list:
    """
    Generate a ranked list of job vacancies for a given applicant profile.

    Parameters
    ----------
    educ_level          : str  — applicant's highest education attained
    preferred_position  : str  — applicant's stated job preference
    skills              : str  — applicant's declared skills
    work_experience     : str  — applicant's prior role history
    vacancies           : list of dict — each dict must have:
                              'title'    : str  — job title
                              'employer' : str  — employer name
                              'category' : str  — occupational category name
    pipeline            : dict — loaded from recommendation_pipeline.pkl

    Returns
    -------
    list of dict — vacancies sorted by suitability_score descending, each with:
        'rank'             : int
        'title'            : str
        'employer'         : str
        'category'         : str
        'suitability_score': float (0.0 to 1.0)
        'suitability_pct'  : str  (e.g. '82.4%')
    """
    vectorizer = pipeline['vectorizer']
    model      = pipeline['model']

    # Step 1 — clean and concatenate profile fields
    profile_text = clean_profile(
        educ_level, preferred_position, skills, work_experience
    )

    # Step 2 — convert to TF-IDF vector
    profile_vector = vectorizer.transform([profile_text])

    # Step 3 — get probability scores for all 5 categories
    probabilities = model.predict_proba(profile_vector)[0]

    # Build category name → score mapping
    category_scores = {
        CATEGORIES[i]: round(float(probabilities[i]), 4)
        for i in range(len(CATEGORIES))
    }

    # Step 4 — assign score to each vacancy based on its occupational category
    scored = []
    for vacancy in vacancies:
        score = category_scores.get(vacancy['category'], 0.0)
        scored.append({
            'title'             : vacancy['title'],
            'employer'          : vacancy['employer'],
            'category'          : vacancy['category'],
            'suitability_score' : score,
            'suitability_pct'   : f"{score * 100:.1f}%",
        })

    # Step 5 — sort by score descending
    scored.sort(key=lambda x: x['suitability_score'], reverse=True)

    # Step 6 — assign rank, return top 5 only
    for i, item in enumerate(scored, start=1):
        item['rank'] = i

    return scored[:5]


# ==============================================================================
# DISPLAY HELPER
# ==============================================================================

def print_results(profile: dict, results: list, scores: dict):
    print("\n" + "=" * 65)
    print("  APPLICANT PROFILE")
    print("=" * 65)
    for k, v in profile.items():
        print(f"  {k:<22}: {v}")

    print("\n" + "=" * 65)
    print("  CATEGORY PROBABILITY SCORES")
    print("=" * 65)
    print(f"  {'Occupational Category':<35} {'Score':>8}")
    print(f"  {'-' * 45}")
    for cat, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:<35} {score * 100:>7.1f}%")

    print("\n" + "=" * 65)
    print("  RANKED JOB VACANCIES")
    print("=" * 65)
    print(f"  {'Rank':<6} {'Job Title':<30} {'Employer':<20} {'Score':>8}")
    print(f"  {'-' * 65}")
    for item in results:
        print(f"  {item['rank']:<6} {item['title']:<30} {item['employer']:<20} {item['suitability_pct']:>8}")
    print("=" * 65 + "\n")


# ==============================================================================
# DEMO RUN
# ==============================================================================

if __name__ == '__main__':

    print("\n" + "=" * 65)
    print("  PESO CSJDM — Job Recommendation Inference Demo")
    print("=" * 65)

    # Load the saved pipeline
    print("\n  Loading recommendation_pipeline.pkl ...")
    pipeline = load_pipeline()
    print(f"  Model loaded  : {pipeline['model_name']}")
    print(f"  Vocabulary    : {len(pipeline['vectorizer'].get_feature_names_out()):,} terms")

    # ── SAMPLE APPLICANT PROFILE ──────────────────────────────────────────────
    profile = {
        'EDUC LEVEL'         : 'College Graduate',
        'PREFERRED POSITION' : 'Sales Clerk',
        'SKILLS'             : 'Customer Service, Cashiering, Product Knowledge',
        'WORK EXPERIENCE'    : '1 year as Cashier',
    }

    # ── SAMPLE ACTIVE VACANCIES ───────────────────────────────────────────────
    # In the actual Flask app this list comes from the database.
    # Each vacancy must include its occupational category.
    vacancies = [
        {'title': 'Sales Clerk',       'employer': 'SM Supermarket',   'category': 'Sales/Service/Retail'},
        {'title': 'Cashier',           'employer': 'Puregold',         'category': 'Sales/Service/Retail'},
        {'title': 'Service Crew',      'employer': 'Jollibee',         'category': 'Sales/Service/Retail'},
        {'title': 'Office Clerk',      'employer': 'ABC Corporation',  'category': 'Clerical and Administrative'},
        {'title': 'Data Encoder',      'employer': 'XYZ Solutions',    'category': 'Clerical and Administrative'},
        {'title': 'Warehouse Helper',  'employer': 'LMN Logistics',    'category': 'Warehouse and Logistics'},
        {'title': 'Security Guard',    'employer': 'PQR Agency',       'category': 'General Services and Security'},
        {'title': 'Production Worker', 'employer': 'DEF Manufacturing','category': 'Production and Manufacturing'},
    ]

    # ── RUN RECOMMENDATION ────────────────────────────────────────────────────
    results = recommend(
        educ_level         = profile['EDUC LEVEL'],
        preferred_position = profile['PREFERRED POSITION'],
        skills             = profile['SKILLS'],
        work_experience    = profile['WORK EXPERIENCE'],
        vacancies          = vacancies,
        pipeline           = pipeline,
    )

    # Get category scores for display
    profile_text   = clean_profile(
        profile['EDUC LEVEL'],
        profile['PREFERRED POSITION'],
        profile['SKILLS'],
        profile['WORK EXPERIENCE'],
    )
    profile_vector = pipeline['vectorizer'].transform([profile_text])
    probabilities  = pipeline['model'].predict_proba(profile_vector)[0]
    category_scores = {CATEGORIES[i]: float(probabilities[i]) for i in range(len(CATEGORIES))}

    print_results(profile, results, category_scores)
