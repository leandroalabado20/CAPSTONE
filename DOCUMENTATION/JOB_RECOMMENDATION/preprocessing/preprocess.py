"""
Data Preprocessing Script — PLACEMENT_DATASET.xlsx
Produces a clean CSV ready for TF-IDF vectorization and classifier training.

Run from the preprocessing/ folder:
    python preprocess.py
Output: preprocessed_dataset.csv (same folder)
"""

import os
import re

import pandas as pd

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH  = os.path.join(BASE_DIR, '..', '..', 'PAPER', 'PLACEMENT_DATASET.xlsx')
OUTPUT_PATH = os.path.join(BASE_DIR, 'preprocessed_dataset.csv')

# ── OCCUPATIONAL CATEGORY MAPPING ─────────────────────────────────────────────
# Maps every POSITION value in the dataset to one of 5 occupational categories.
# Titles not in this dictionary are excluded from training (unrecognizable labels).

JOB_POSITION_MAPPING = {
    # ── Warehouse and Logistics ───────────────────────────────────────────────
    'BAGGER':                               'Warehouse and Logistics',
    'CHECKER':                              'Warehouse and Logistics',
    'DELIVERY HELPER':                      'Warehouse and Logistics',
    'FORKLIFT OPERATOR':                    'Warehouse and Logistics',
    'INVENTORY CLERK':                      'Warehouse and Logistics',
    'LOGISTICS COORDINATOR':                'Warehouse and Logistics',
    'RECEIVING CLERK':                      'Warehouse and Logistics',
    'STOCK CLERK':                          'Warehouse and Logistics',
    'STOREROOM CLERK':                      'Warehouse and Logistics',
    'WAREHOUSE CLERK':                      'Warehouse and Logistics',
    'WAREHOUSE HELPER':                     'Warehouse and Logistics',
    'WAREHOUSE INSPECTOR (GOV)':            'Warehouse and Logistics',

    # ── Production and Manufacturing ──────────────────────────────────────────
    'ASSISTANT COOK':                       'Production and Manufacturing',
    'BLASTER':                              'Production and Manufacturing',
    'ELECTRICIAN (GENERAL)':               'Production and Manufacturing',
    'FIBER PICKER':                         'Production and Manufacturing',
    'FISHERY HELPER':                       'Production and Manufacturing',
    'FISHERY LABORER':                      'Production and Manufacturing',
    'FOOD CHECKER':                         'Production and Manufacturing',
    'FOOD PREPARER':                        'Production and Manufacturing',
    'FRUIT PICKER':                         'Production and Manufacturing',
    'HEAD BUTCHER':                         'Production and Manufacturing',
    'INTERIOR DECORATOR':                   'Production and Manufacturing',
    'KITCHEN CREW':                         'Production and Manufacturing',
    'KITCHEN HELPER':                       'Production and Manufacturing',
    'LABORER':                              'Production and Manufacturing',
    'MACHINE TOOL MACHINE OPERATOR':        'Production and Manufacturing',
    'MAINTENANCE LABORER':                  'Production and Manufacturing',
    'MASON (GENERAL)':                      'Production and Manufacturing',
    'MECHANIC':                             'Production and Manufacturing',
    'MECHANIC HELPER':                      'Production and Manufacturing',
    'MECHANICAL HELPER':                    'Production and Manufacturing',
    'PRODUCTION HELPER':                    'Production and Manufacturing',
    'PRODUCTION WORKER':                    'Production and Manufacturing',
    'QUALITY ASSURANCE STAFF':              'Production and Manufacturing',
    'TIG WELDER':                           'Production and Manufacturing',
    'WELDER':                               'Production and Manufacturing',

    # ── Sales / Service / Retail ──────────────────────────────────────────────
    'CASHIER':                              'Sales/Service/Retail',
    'CUSTOMER SERVICE ASSISTANT':           'Sales/Service/Retail',
    'CUSTOMER SERVICE MANAGER':             'Sales/Service/Retail',
    'FOOD ATTENDANT':                       'Sales/Service/Retail',
    'FOOD SERVER':                          'Sales/Service/Retail',
    'FOOD SERVICE DISPATCHER':              'Sales/Service/Retail',
    'MARKETING ASSISTANT':                  'Sales/Service/Retail',
    'MARKETING STAFF':                      'Sales/Service/Retail',
    'MERCHANDISER':                         'Sales/Service/Retail',
    'PROMO SALESPERSON':                    'Sales/Service/Retail',
    'PROMO STAFF':                          'Sales/Service/Retail',
    'RESERVATION CLERK':                    'Sales/Service/Retail',
    'SALES & MARKETING ASSISTANT':          'Sales/Service/Retail',
    'SALES AND PROMOTION SUPERVISOR':       'Sales/Service/Retail',
    'SALES ASSOCIATE PROFESSIONAL':         'Sales/Service/Retail',
    'SALES CLERK':                          'Sales/Service/Retail',
    'SALES OFFICER':                        'Sales/Service/Retail',
    'SALES SUPERVISOR':                     'Sales/Service/Retail',
    'SALESMAN':                             'Sales/Service/Retail',
    'SERVICE CREW':                         'Sales/Service/Retail',
    'STORE HELPER':                         'Sales/Service/Retail',
    'STORE MANAGER':                        'Sales/Service/Retail',
    'STORE SALESPERSON':                    'Sales/Service/Retail',
    'STORE SUPERVISOR':                     'Sales/Service/Retail',
    'TECHNICAL SUPPORT STAFF':              'Sales/Service/Retail',

    # ── Clerical and Administrative ───────────────────────────────────────────
    'ACCOUNTING OFFICER':                   'Clerical and Administrative',
    'ACCOUNTING STAFF':                     'Clerical and Administrative',
    'ACCOUNTS OFFICER':                     'Clerical and Administrative',
    'ADMINISTRATIVE ASSISTANT':             'Clerical and Administrative',
    'AUDITING CLERK':                       'Clerical and Administrative',
    'DATA ENCODER':                         'Clerical and Administrative',
    'DOCUMENTATION STAFF':                  'Clerical and Administrative',
    'FIELD INTERVIEWER':                    'Clerical and Administrative',
    'FINANCIAL PLANNER':                    'Clerical and Administrative',
    'FINANCIAL/ACCOUNTS SPECIALIST':        'Clerical and Administrative',
    'HUMAN RESOURCE DEVELOPMENT CLERK':     'Clerical and Administrative',
    'OFFICE CLERK':                         'Clerical and Administrative',
    'SAFETY OFFICER':                       'Clerical and Administrative',
    'SECRETARY':                            'Clerical and Administrative',

    # ── General Services and Security ─────────────────────────────────────────
    'CAR DRIVER':                           'General Services and Security',
    'CLEANING SERVICES GENERAL MANAGER':    'General Services and Security',
    'CLEANING SERVICES MANAGER':            'General Services and Security',
    'COMPANY DRIVER':                       'General Services and Security',
    'DRIVER (GOV)':                         'General Services and Security',
    'HOUSEKEEPER (PRIVATE)':                'General Services and Security',
    'HOUSEKEEPING SERVICES ASSISTANT (GOV)':'General Services and Security',
    'JANITOR':                              'General Services and Security',
    'LADY GUARD':                           'General Services and Security',
    'SANITATION INSPECTOR I (GOV)':         'General Services and Security',
    'SECURITY GUARD':                       'General Services and Security',
    'UTILITY WORKER':                       'General Services and Security',
}

# Deterministic label order (0–4)
CATEGORY_ORDER = [
    'Warehouse and Logistics',       # 0
    'Production and Manufacturing',  # 1
    'Sales/Service/Retail',          # 2
    'Clerical and Administrative',   # 3
    'General Services and Security', # 4
]
LABEL_MAP = {cat: i for i, cat in enumerate(CATEGORY_ORDER)}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def strip_numeric_noise(text: str) -> str:
    """Remove duration prefixes and standalone numbers from WORK EXPERIENCE text.

    '5 mos as CASHIER' -> 'cashier'
    '2 years as DATA ENCODER, 12 mos as OFFICE CLERK' -> 'data encoder  office clerk'
    """
    text = re.sub(r'\b\d+\s*(?:mos?|years?)\s*as\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def clean_text(text: str) -> str:
    """Lowercase -> remove non-alphanumeric -> collapse whitespace."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


# ── STEP 1: LOAD DATASET ──────────────────────────────────────────────────────
print("=" * 60)
print("PESO CSJDM — Data Preprocessing Pipeline")
print("=" * 60)

print("\n[Step 1] Loading dataset...")
# header=2: first two rows are merged group/sub-group labels; row index 2 holds actual column names
df = pd.read_excel(INPUT_PATH, header=2)
# The Excel sheet has 3 columns all literally named POSITION (cols 8, 11, 15).
# Disambiguate immediately by index before pandas auto-suffixes (POSITION.1, etc.)
# propagate through the rest of the script:
#   col 8  — POSITION under "Referral for Wage Employment"  (all nulls)
#   col 11 — POSITION under "Placement as Reported by Employer"  ← the target label
#   col 15 — POSITION under "Found Job After LST"  (all nulls)
df.rename(columns={df.columns[11]: 'JOB POSITION'}, inplace=True)
print(f"  Records loaded : {len(df):,} records, {len(df.columns)} columns.")
#print("\n--- Step 1 Output ---")
#print(df.head())
#print(f"\nColumns: {list(df.columns)}")

# ── STEP 2: SELECT 5 RELEVANT COLUMNS ─────────────────────────────────────────
print("\n[Step 2] Selecting 5 relevant columns...")
KEEP = ['EDUC LEVEL', 'PREFERRED POSITION', 'SKILLS', 'WORK EXPERIENCE', 'JOB POSITION']
dropped = len(df.columns) - len(KEEP)
df = df[KEEP].copy()
print(f"  Retained: EDUC LEVEL, PREFERRED POSITION, SKILLS, WORK EXPERIENCE, JOB POSITION")
print(f"  Dropped {dropped} administrative columns.")

# ── STEP 3: FILL BLANK WORK EXPERIENCE ────────────────────────────────────────
print("\n[Step 3] Filling blank WORK EXPERIENCE entries...")
blank_count = df['WORK EXPERIENCE'].isna().sum()
df['WORK EXPERIENCE'] = df['WORK EXPERIENCE'].fillna('NO EXPERIENCE')
print(f"  Filled {blank_count:,} blank entries with 'NO EXPERIENCE'.")

# ── STEP 4: REMOVE EXACT DUPLICATES ───────────────────────────────────────────
print("\n[Step 4] Removing exact duplicate records...")
before = len(df)
df.drop_duplicates(inplace=True)
removed = before - len(df)
print(f"  Removed {removed} duplicate records. Remaining: {len(df):,}.")

# ── STEP 5: MAP JOB POSITION TO OCCUPATIONAL CATEGORY ─────────────────────────
print("\n[Step 5] Mapping Job Position to occupational category...")
df['OCCUPATIONAL CATEGORY'] = df['JOB POSITION'].map(JOB_POSITION_MAPPING)
excluded = df['OCCUPATIONAL CATEGORY'].isna().sum()
if excluded:
    unrecognized = df.loc[df['OCCUPATIONAL CATEGORY'].isna(), 'JOB POSITION'].unique()
    print(f"  Excluded {excluded} record(s) with unrecognized titles: {list(unrecognized)}")
df = df[df['OCCUPATIONAL CATEGORY'].notna()].copy()
print(f"  Remaining after exclusion: {len(df):,}.")

# ── STEP 6: LOWERCASE ─────────────────────────────────────────────────────────
print("\n[Step 6] Converting all text fields to lowercase...")
TEXT_COLS = ['EDUC LEVEL', 'PREFERRED POSITION', 'SKILLS', 'WORK EXPERIENCE']
for col in TEXT_COLS:
    df[col] = df[col].astype(str).str.lower()
print("  Done.")

# ── STEP 7: REMOVE SPECIAL CHARACTERS AND PUNCTUATION ─────────────────────────
print("\n[Step 7] Removing special characters and punctuation...")
for col in TEXT_COLS:
    df[col] = df[col].apply(lambda x: re.sub(r'[^a-z0-9\s]', ' ', x))
    df[col] = df[col].apply(lambda x: re.sub(r'\s+', ' ', x).strip())
print("  Done.")

# ── STEP 8: STRIP NUMERIC NOISE FROM WORK EXPERIENCE ──────────────────────────
print("\n[Step 8] Stripping numeric noise from WORK EXPERIENCE...")
df['WORK EXPERIENCE'] = df['WORK EXPERIENCE'].apply(strip_numeric_noise)
print("  Example: '5 mos as cashier' -> 'cashier'")
print("  Done.")

# ── STEP 9: CONCATENATE 4 FIELDS INTO 1 TEXT STRING ───────────────────────────
print("\n[Step 9] Concatenating 4 fields into PROFILE_TEXT...")
df['PROFILE_TEXT'] = (
    df['EDUC LEVEL']         + ' ' +
    df['PREFERRED POSITION'] + ' ' +
    df['SKILLS']             + ' ' +
    df['WORK EXPERIENCE']
)
df['PROFILE_TEXT'] = df['PROFILE_TEXT'].apply(lambda x: re.sub(r'\s+', ' ', x).strip())
print("  Done.")

# ── STEP 10: LABEL ENCODE OCCUPATIONAL CATEGORY ───────────────────────────────
print("\n[Step 10] Label-encoding occupational categories...")
df['LABEL'] = df['OCCUPATIONAL CATEGORY'].map(LABEL_MAP)
for cat, code in LABEL_MAP.items():
    count = (df['LABEL'] == code).sum()
    print(f"  {code}  ->  {cat!r}  ({count} records)")

# ── SAVE OUTPUT ────────────────────────────────────────────────────────────────
output_df = df[['PROFILE_TEXT', 'OCCUPATIONAL CATEGORY', 'LABEL']].copy()
output_df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

print("\n" + "=" * 60)
print(f"Output saved  : {OUTPUT_PATH}")
print(f"Final records : {len(output_df):,}")
print("Status        : Ready for TF-IDF vectorization.")
print("=" * 60)
