"""
PESO CSJDM Web-Based Data-Driven Job Recommendation System
Flask Application Entry Point — Multi-Entity Version

Roles: admin | employer | jobseeker
Run:  python app.py
Default admin account: admin@peso.gov.ph  (password set during seeding)
"""

import os
import re
import json
import sqlite3
import joblib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash

# ── APP CONFIG ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)

# Set PESO_HTTPS=1 on an HTTPS host (e.g. PythonAnywhere); leave unset for local HTTP.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('PESO_HTTPS', '0') == '1'

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATABASE       = os.path.join(BASE_DIR, 'peso.db')
PIPELINE_PATH  = os.path.join(BASE_DIR, 'ml', 'recommendation_pipeline.pkl')

# ── ROLE CONSTANTS ────────────────────────────────────────────────────────────
ROLE_ADMIN     = 'admin'
ROLE_EMPLOYER  = 'employer'
ROLE_JOBSEEKER = 'jobseeker'

# ── DOMAIN CONSTANTS ──────────────────────────────────────────────────────────
CATEGORIES = {
    0: 'Warehouse and Logistics',
    1: 'Production and Manufacturing',
    2: 'Sales/Service/Retail',
    3: 'Clerical and Administrative',
    4: 'General Services and Security',
}
CATEGORY_LIST = list(CATEGORIES.values())

EDUC_LEVELS = [
    'Elementary Level', 'Elementary Graduate',
    'High School Level', 'High School Graduate',
    'Senior High School Level', 'Senior High School Graduate',
    'College Level', 'College Graduate',
    'Vocational', 'ALS',
]

APPLICANTS_PER_PAGE = 24
LIST_PER_PAGE = 20

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# ── EMPLOYER PROFILE CHOICES (PhilJobNet-aligned) ─────────────────────────────
EMPLOYER_SECTORS = ['Public', 'Private']
EMPLOYER_TYPES = {
    'Public': [
        'National Government Agency',
        'Local Government Unit',
        'Government-Owned and Controlled Corporation',
        'State/Local University College',
    ],
    'Private': [
        'Direct Hire',
        'Private Employment Agency',
        'Overseas Recruitment Agency',
    ],
}
WORKFORCE_SIZES = ['Micro (1–9)', 'Small (10–99)', 'Medium (100–199)', 'Large (200+)']
LOCATION_TYPES = ['Main', 'Branch']
SALARY_PERIODS = ['Daily', 'Weekly', 'Semi-monthly', 'Monthly']

CAT_ICONS = {
    'Warehouse and Logistics':       'bi-box-seam',
    'Production and Manufacturing':  'bi-gear-fill',
    'Sales/Service/Retail':          'bi-shop',
    'Clerical and Administrative':   'bi-file-earmark-text-fill',
    'General Services and Security': 'bi-shield-fill',
}

YOUTH_AGE_MIN  = 15
YOUTH_AGE_MAX  = 30
SENIOR_AGE_MIN = 60

PREFERRED_POSITIONS = [
    'Warehouse Helper', 'Stock Clerk', 'Inventory Clerk', 'Forklift Operator',
    'Delivery Driver / Courier', 'Packer / Sorter',
    'Production Worker', 'Machine Operator', 'Quality Control Inspector',
    'Assembler', 'Welder', 'Factory Worker',
    'Cashier', 'Sales Associate', 'Store Clerk', 'Customer Service Representative',
    'Barista', 'Waiter / Waitress', 'Service Crew', 'Food Service Worker',
    'Data Encoder', 'Office Clerk', 'Administrative Assistant',
    'Receptionist', 'Secretary', 'Bookkeeper', 'Payroll Clerk',
    'Security Guard', 'Janitor / Janitress', 'Utility Worker',
    'Maintenance Staff', 'Building Attendant', 'Messengerial Staff',
]

SKILLS_LIST = [
    'Customer Service', 'Cashiering', 'Sales / Marketing',
    'Inventory Management', 'Forklift Operation', 'Driving',
    'Machine Operation', 'Quality Control', 'Welding',
    'Packing / Sorting', 'Physical Labor', 'Food Preparation',
    'Data Encoding', 'Filing / Records Management', 'Bookkeeping',
    'Receptionist Duties', 'Cleaning / Sanitation', 'Security / Guard Duties',
    'Communication Skills', 'Computer Literacy', 'Microsoft Office',
    'Teamwork', 'Time Management', 'Basic Accounting',
]

WORK_EXPERIENCE_LIST = [
    'No work experience',
    'Cashier', 'Store Clerk', 'Service Crew', 'Sales Associate',
    'Food Service Worker', 'Barista', 'Waiter / Waitress',
    'Warehouse Helper', 'Packer / Sorter', 'Inventory Clerk',
    'Forklift Operator', 'Delivery Driver / Courier',
    'Production Worker', 'Machine Operator', 'Assembler',
    'Welder', 'Quality Control Inspector', 'Factory Worker',
    'Security Guard', 'Utility Worker', 'Janitor / Janitress',
    'Maintenance Staff', 'Building Attendant',
    'Data Encoder', 'Office Clerk', 'Administrative Assistant',
    'Receptionist', 'Bookkeeper', 'Payroll Clerk',
]

# ── APPLICANT PROFILE CHOICES (PhilJobNet / NSRP Form 1) ──────────────────────
SUFFIX_CHOICES       = ['', 'Jr.', 'Sr.', 'II', 'III', 'IV', 'V']
CIVIL_STATUS_CHOICES = ['Single', 'Married', 'Widowed', 'Separated', 'Annulled']
RELIGION_CHOICES     = ['Roman Catholic', 'Islam', 'Iglesia ni Cristo', 'Protestant',
                        'Born Again Christian', 'Seventh-day Adventist', 'Buddhist',
                        'Others']
DISABILITY_TYPES     = ['Visual', 'Hearing', 'Speech', 'Physical', 'Mental', 'Others']
LANGUAGE_CHOICES     = ['Mandarin', 'Tagalog', 'English']
EMPLOYED_TYPES       = ['Wage employed', 'Self-employed', 'Others']
UNEMPLOYED_REASONS   = ['New entrant/fresh graduate', 'Finished contract', 'Resigned',
                        'Retired', 'Terminated/Laid off due to calamity',
                        'Terminated/Laid off (local)', 'Terminated/Laid off (abroad)',
                        'Displaced POGO Worker', 'Others']
WORK_STATUS_CHOICES  = ['Permanent', 'Contractual', 'Probationary', 'Casual',
                        'Part-time', 'Seasonal']
OTHER_SKILLS_CHOICES = ['Auto Mechanic', 'Beautician', 'Carpentry Work', 'Computer Literate',
                        'Domestic Chores', 'Driving', 'Electrician', 'Embroidery',
                        'Gardening', 'Masonry', 'Painter/Artist', 'Painting Jobs',
                        'Photography', 'Sewing Dresses', 'Stenography', 'Tailoring']

BARANGAY_DISTRICT = {
    'POBLACION': 'District 1', 'POBLACION I': 'District 1',
    'FRANCISCO HOMES-GUIJO': 'District 1', 'FRANCISCO HOMES-MULAWIN': 'District 1',
    'FRANCISCO HOMES-NARRA': 'District 1', 'FRANCISCO HOMES-YAKAL': 'District 1',
    'GUMAOC EAST': 'District 1', 'GUMAOC WEST': 'District 1',
    'GUMAOC CENTRAL': 'District 1', 'GRACEVILLE': 'District 1',
    'GAYA-GAYA': 'District 1', 'SANTO CRISTO': 'District 1',
    'TUNGKONG MANGGA': 'District 1', 'DULONG BAYAN': 'District 1',
    'CIUDAD REAL': 'District 1', 'MAHARLIKA': 'District 1',
    'SAN MANUEL': 'District 1', 'KAYPIAN': 'District 1',
    'SAN ISIDRO': 'District 1', 'SAN ROQUE': 'District 1',
    'KAYBANBAN': 'District 1', 'PARADISE III': 'District 1',
    'MUZON': 'District 1', 'MUZON PROPER': 'District 1',
    'MUZON EAST': 'District 1', 'MUZON WEST': 'District 1',
    'MUZON SOUTH': 'District 1',
    'SAPANG PALAY': 'District 2', 'SAPANG PALAY PROPER': 'District 2',
    'MINUYAN PROPER': 'District 2', 'MINUYAN': 'District 2',
    'MINUYAN I': 'District 2', 'MINUYAN II': 'District 2',
    'MINUYAN III': 'District 2', 'MINUYAN IV': 'District 2',
    'MINUYAN V': 'District 2', 'BAGONG BUHAY': 'District 2',
    'BAGONG BUHAY I': 'District 2', 'BAGONG BUHAY II': 'District 2',
    'BAGONG BUHAY III': 'District 2', 'SAN MARTIN': 'District 2',
    'SAN MARTIN I': 'District 2', 'SAN MARTIN II': 'District 2',
    'SAN MARTIN III': 'District 2', 'SAN MARTIN IV': 'District 2',
    'SAN MARTIN DE PORRES': 'District 2', 'ST. MARTIN DE PORRES': 'District 2',
    'SANTA CRUZ': 'District 2', 'SANTA CRUZ I': 'District 2',
    'SANTA CRUZ II': 'District 2', 'SANTA CRUZ III': 'District 2',
    'SANTA CRUZ IV': 'District 2', 'SANTA CRUZ V': 'District 2',
    'FATIMA': 'District 2', 'FATIMA I': 'District 2',
    'FATIMA II': 'District 2', 'FATIMA III': 'District 2',
    'FATIMA IV': 'District 2', 'FATIMA V': 'District 2',
    'CITRUS': 'District 2', 'SAN PEDRO': 'District 2',
    'SAN RAFAEL': 'District 2', 'SAN RAFAEL I': 'District 2',
    'SAN RAFAEL II': 'District 2', 'SAN RAFAEL III': 'District 2',
    'SAN RAFAEL IV': 'District 2', 'SAN RAFAEL V': 'District 2',
    'ASSUMPTION': 'District 2', 'LAWANG PARI': 'District 2',
    'SANTO NIÑO': 'District 2', 'SANTO NIÑO I': 'District 2',
    'SANTO NIÑO II': 'District 2',
}


def barangay_to_district(raw):
    return BARANGAY_DISTRICT.get(re.sub(r'\s+', ' ', str(raw)).strip().upper(), '')


def find_duplicate_applicant(db, first_name, last_name, birthdate, exclude_id=None):
    """Look for an existing (non-archived) applicant with the same name and
    birthdate — a strong signal it's the same person re-registering."""
    q = '''
        SELECT * FROM applicants
        WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(?))
          AND LOWER(TRIM(last_name))  = LOWER(TRIM(?))
          AND birthdate = ?
          AND is_archived = 0
    '''
    params = [first_name, last_name, birthdate]
    if exclude_id is not None:
        q += ' AND id != ?'
        params.append(exclude_id)
    return db.execute(q, params).fetchone()

# ── DATABASE ──────────────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    DEFAULT 'admin',
            is_active     INTEGER DEFAULT 1,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS applicants (
            id                 INTEGER  PRIMARY KEY AUTOINCREMENT,
            first_name         TEXT     NOT NULL,
            last_name          TEXT     NOT NULL,
            sex                TEXT,
            age                INTEGER,
            barangay           TEXT,
            district           TEXT,
            employment_status  TEXT     DEFAULT 'Unemployed',
            is_pwd             INTEGER  DEFAULT 0,
            educ_level         TEXT     NOT NULL,
            preferred_position TEXT     NOT NULL,
            skills             TEXT     NOT NULL,
            work_experience    TEXT,
            birthdate          DATE,
            contact_number     TEXT,
            user_id            INTEGER  REFERENCES users(id),
            created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_archived        INTEGER  DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS job_vacancies (
            id                    INTEGER  PRIMARY KEY AUTOINCREMENT,
            employer_name         TEXT     NOT NULL,
            job_title             TEXT     NOT NULL,
            occupational_category TEXT     NOT NULL,
            is_local              INTEGER  DEFAULT 1,
            is_active             INTEGER  DEFAULT 1,
            employer_id           INTEGER  REFERENCES users(id),
            created_at            DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS employers (
            id             INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER  UNIQUE NOT NULL,
            company_name   TEXT     NOT NULL,
            contact_person TEXT     NOT NULL,
            phone          TEXT,
            address        TEXT,
            is_approved    INTEGER  DEFAULT 0,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id               INTEGER  PRIMARY KEY AUTOINCREMENT,
            applicant_id     INTEGER  NOT NULL,
            vacancy_id       INTEGER  NOT NULL,
            suitability_score REAL    NOT NULL,
            rank             INTEGER,
            recommended_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            generated_by     INTEGER,
            status           TEXT     DEFAULT 'pending',
            FOREIGN KEY (applicant_id) REFERENCES applicants(id),
            FOREIGN KEY (vacancy_id)   REFERENCES job_vacancies(id),
            FOREIGN KEY (generated_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS referrals (
            id           INTEGER  PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER  NOT NULL,
            vacancy_id   INTEGER  NOT NULL,
            referred_by  INTEGER  NOT NULL,
            referred_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            status       TEXT     DEFAULT 'referred',
            suitability_score REAL,
            notes        TEXT,
            FOREIGN KEY (applicant_id) REFERENCES applicants(id),
            FOREIGN KEY (vacancy_id)   REFERENCES job_vacancies(id),
            FOREIGN KEY (referred_by)  REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS login_logs (
            id         INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            username   TEXT,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            outcome    TEXT
        );
    ''')

    # ── Migrate older applicants table ─────────────────────────────────────────
    acols = [r[1] for r in db.execute("PRAGMA table_info(applicants)").fetchall()]
    if 'age' not in acols:
        db.executescript('''
            CREATE TABLE applicants_new (
                id                 INTEGER  PRIMARY KEY AUTOINCREMENT,
                first_name         TEXT     NOT NULL,
                last_name          TEXT     NOT NULL,
                sex                TEXT,
                age                INTEGER,
                barangay           TEXT,
                district           TEXT,
                employment_status  TEXT     DEFAULT 'Unemployed',
                is_pwd             INTEGER  DEFAULT 0,
                educ_level         TEXT     NOT NULL,
                preferred_position TEXT     NOT NULL,
                skills             TEXT     NOT NULL,
                work_experience    TEXT,
                user_id            INTEGER  REFERENCES users(id),
                created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_archived        INTEGER  DEFAULT 0
            );
            INSERT INTO applicants_new
                (id, first_name, last_name, sex, barangay, district,
                 employment_status, is_pwd, educ_level, preferred_position,
                 skills, work_experience, created_at, is_archived)
            SELECT id, first_name, last_name, sex, barangay, district,
                 employment_status, is_pwd, educ_level, preferred_position,
                 skills, work_experience, created_at, is_archived
            FROM applicants;
            DROP TABLE applicants;
            ALTER TABLE applicants_new RENAME TO applicants;
        ''')

    # ── Column-level migrations ────────────────────────────────────────────────
    acols = [r[1] for r in db.execute("PRAGMA table_info(applicants)").fetchall()]
    if 'user_id' not in acols:
        db.execute('ALTER TABLE applicants ADD COLUMN user_id INTEGER REFERENCES users(id)')
    if 'birthdate' not in acols:
        db.execute('ALTER TABLE applicants ADD COLUMN birthdate DATE')
    if 'contact_number' not in acols:
        db.execute('ALTER TABLE applicants ADD COLUMN contact_number TEXT')
    # PhilJobNet / NSRP applicant profile fields
    for col, ddl in [
        ('middle_name', 'TEXT'), ('suffix', 'TEXT'),
        ('civil_status', 'TEXT'), ('address_line', 'TEXT'), ('city', 'TEXT'),
        ('province', 'TEXT'), ('height_cm', 'TEXT'), ('religion', 'TEXT'),
        ('tin', 'TEXT'), ('landline', 'TEXT'), ('disability', 'TEXT'),
        ('is_4ps', 'INTEGER DEFAULT 0'), ('household_id', 'TEXT'),
        ('is_wodp', 'INTEGER DEFAULT 0'), ('is_dswd_foodstamp', 'INTEGER DEFAULT 0'),
        ('is_caregiver', 'INTEGER DEFAULT 0'),
        ('is_ofw', 'INTEGER DEFAULT 0'), ('ofw_country', 'TEXT'),
        ('is_former_ofw', 'INTEGER DEFAULT 0'), ('former_ofw_country', 'TEXT'),
        ('ofw_return_date', 'TEXT'),
        ('employed_type', 'TEXT'), ('unemployed_reason', 'TEXT'),
        ('job_search_months', 'INTEGER'),
        ('pref_work_local', 'TEXT'), ('pref_work_overseas', 'TEXT'),
        # JSON-encoded repeatable sections
        ('languages', 'TEXT'), ('education', 'TEXT'), ('trainings', 'TEXT'),
        ('eligibilities', 'TEXT'), ('work_history', 'TEXT'), ('other_skills', 'TEXT'),
        ('certified', 'INTEGER DEFAULT 0'), ('certified_at', 'DATETIME'),
    ]:
        if col not in acols:
            db.execute(f'ALTER TABLE applicants ADD COLUMN {col} {ddl}')

    vcols = [r[1] for r in db.execute("PRAGMA table_info(job_vacancies)").fetchall()]
    if 'employer_id' not in vcols:
        db.execute('ALTER TABLE job_vacancies ADD COLUMN employer_id INTEGER REFERENCES users(id)')
    for col, ddl in [
        ('application_deadline', 'DATE'),
        ('req_gender',           "TEXT DEFAULT 'Any'"),
        ('req_age_min',          'INTEGER'),
        ('req_age_max',          'INTEGER'),
        ('req_education',        'TEXT'),
        ('req_documents',        'TEXT'),
        ('req_experience_months', 'INTEGER'),
        ('salary_min',           'INTEGER'),
        ('salary_max',           'INTEGER'),
        ('salary_period',        'TEXT'),
        ('job_location',         'TEXT'),
        ('req_skills',           'TEXT'),
    ]:
        if col not in vcols:
            db.execute(f'ALTER TABLE job_vacancies ADD COLUMN {col} {ddl}')
    # Drop obsolete free-text requirement columns (replaced by matchable fields)
    for dead in ('req_physical', 'req_experience', 'req_other'):
        if dead in vcols:
            try:
                db.execute(f'ALTER TABLE job_vacancies DROP COLUMN {dead}')
            except sqlite3.OperationalError:
                pass  # older SQLite without DROP COLUMN support — harmless to keep

    rcols = [r[1] for r in db.execute("PRAGMA table_info(referrals)").fetchall()]
    if 'suitability_score' not in rcols:
        db.execute('ALTER TABLE referrals ADD COLUMN suitability_score REAL')

    ecols = [r[1] for r in db.execute("PRAGMA table_info(employers)").fetchall()]
    for col, ddl in [
        ('tin',               'TEXT'),
        ('trade_name',        'TEXT'),
        ('location_type',     'TEXT'),
        ('employer_sector',   'TEXT'),
        ('employer_type',     'TEXT'),
        ('total_workforce',   'TEXT'),
        ('line_of_business',  'TEXT'),
        ('address_line',      'TEXT'),
        ('barangay',          'TEXT'),
        ('city',              'TEXT'),
        ('province',          'TEXT'),
        ('position',          'TEXT'),
        ('telephone',         'TEXT'),
        ('mobile',            'TEXT'),
        ('fax',               'TEXT'),
        ('profile_email',     'TEXT'),
        ('certified',         'INTEGER DEFAULT 0'),
        ('certified_at',      'DATETIME'),
        ('profile_completed', 'INTEGER DEFAULT 0'),
        ('approval_requested', 'INTEGER DEFAULT 0'),
    ]:
        if col not in ecols:
            db.execute(f'ALTER TABLE employers ADD COLUMN {col} {ddl}')

    ucols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
    if 'role' not in ucols:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'staff'")
    # Merge staff role into admin
    db.execute("UPDATE users SET role='admin' WHERE role='staff'")

    # Drop the obsolete username column (login is by email now) — rebuild users table
    if 'username' in [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]:
        db.executescript('''
            PRAGMA foreign_keys=OFF;
            CREATE TABLE users_new (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name     TEXT    NOT NULL,
                email         TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                role          TEXT    DEFAULT 'admin',
                is_active     INTEGER DEFAULT 1,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users_new (id, full_name, email, password_hash, role, is_active, created_at)
                SELECT id, full_name, email, password_hash, role, is_active, created_at FROM users;
            DROP TABLE users;
            ALTER TABLE users_new RENAME TO users;
            PRAGMA foreign_keys=ON;
        ''')

    # ── Seed default admin ─────────────────────────────────────────────────────
    existing = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if existing == 0:
        db.execute(
            'INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)',
            ('Administrator', 'admin@peso.gov.ph',
             generate_password_hash('admin123'), ROLE_ADMIN)
        )
    else:
        # If no admin exists at all, promote the first user to admin
        has_admin = db.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
        if not has_admin:
            first = db.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
            if first:
                db.execute("UPDATE users SET role='admin' WHERE id=?", (first['id'],))

    db.commit()
    db.close()

# ── ML PIPELINE ───────────────────────────────────────────────────────────────
pipeline = None

def load_pipeline():
    global pipeline
    if os.path.exists(PIPELINE_PATH):
        try:
            pipeline = joblib.load(PIPELINE_PATH)
            model = pipeline.get('model')
            if model is not None and not hasattr(model, 'multi_class'):
                model.multi_class = 'auto'
        except Exception as e:
            import traceback
            app.logger.error(f"ML pipeline load failed: {e}\n{traceback.format_exc()}")
            pipeline = None
    else:
        app.logger.error(f"ML pipeline file not found at: {PIPELINE_PATH}")

def _strip_numeric_noise(text):
    text = re.sub(r'\b\d+\s*(?:mos?|years?)\s*as\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def _clean_profile(educ_level, preferred_position, skills, work_experience):
    if not work_experience or not work_experience.strip():
        work_experience = 'NO EXPERIENCE'
    fields = {
        'educ':   educ_level,
        'pos':    preferred_position,
        'skills': skills,
        'exp':    work_experience,
    }
    fields = {k: v.lower() for k, v in fields.items()}
    fields = {k: re.sub(r'[^a-z0-9\s]', ' ', v) for k, v in fields.items()}
    fields = {k: re.sub(r'\s+', ' ', v).strip() for k, v in fields.items()}
    fields['exp'] = _strip_numeric_noise(fields['exp'])
    return re.sub(r'\s+', ' ',
                  f'{fields["educ"]} {fields["pos"]} {fields["skills"]} {fields["exp"]}').strip()

# A vacancy is open when active and its optional deadline (PH date) has not passed
OPEN_VACANCY_SQL = ("is_active=1 AND (application_deadline IS NULL OR application_deadline='' "
                    "OR application_deadline >= date('now','+8 hours'))")
EXPIRED_SQL = ("(application_deadline IS NOT NULL AND application_deadline<>'' "
               "AND application_deadline < date('now','+8 hours'))")

# Levels that can be ranked; Vocational / ALS are not comparable so they are skipped
EDUC_RANK = {
    'Elementary Level': 1, 'Elementary Graduate': 2,
    'High School Level': 3, 'High School Graduate': 4,
    'Senior High School Level': 5, 'Senior High School Graduate': 6,
    'College Level': 7, 'College Graduate': 8,
}
REQ_EDUC_CHOICES = list(EDUC_RANK.keys())

def _g(v, key):
    try:
        return v[key]
    except (KeyError, IndexError, TypeError):
        return None

def parse_vacancy_requirements(f):
    """Read requirement/deadline fields from a form. Returns (values dict, error or None)."""
    def num(name):
        raw = (f.get(name) or '').strip()
        return int(raw) if raw.isdigit() else None
    gender = f.get('req_gender', 'Any')
    if gender not in ('Any', 'Male', 'Female'):
        gender = 'Any'
    edu = f.get('req_education', '').strip()
    period = f.get('salary_period', '').strip()
    vals = {
        'application_deadline':   (f.get('application_deadline') or '').strip() or None,
        'req_gender':             gender,
        'req_age_min':            num('req_age_min'),
        'req_age_max':            num('req_age_max'),
        'req_education':          edu if edu in EDUC_RANK else None,
        'req_experience_months': num('req_experience_months'),
        'req_documents':          f.get('req_documents', '').strip() or None,
        'salary_min':             num('salary_min'),
        'salary_max':             num('salary_max'),
        'salary_period':          period if period in SALARY_PERIODS else None,
        'job_location':           (f.get('job_location') or '').strip() or None,
        'req_skills':             ','.join(f.getlist('req_skills')) or None,
    }
    if vals['salary_min'] and vals['salary_max'] and vals['salary_min'] > vals['salary_max']:
        return vals, 'Minimum salary cannot be greater than maximum salary.'
    if vals['req_age_min'] and vals['req_age_max'] and vals['req_age_min'] > vals['req_age_max']:
        return vals, 'Minimum age cannot be greater than maximum age.'
    if vals['application_deadline']:
        try:
            datetime.strptime(vals['application_deadline'], '%Y-%m-%d')
        except ValueError:
            return vals, 'Application deadline is not a valid date.'
    return vals, None

REQ_COLS = ['application_deadline', 'req_gender', 'req_age_min', 'req_age_max',
            'req_education', 'req_experience_months', 'req_documents',
            'salary_min', 'salary_max', 'salary_period', 'job_location', 'req_skills']

def salary_text(v):
    """Human-readable salary for a vacancy row/dict, e.g. '₱18,000–₱22,000 / month'."""
    lo, hi, per = _g(v, 'salary_min'), _g(v, 'salary_max'), _g(v, 'salary_period')
    if not lo and not hi:
        return ''
    unit = {'Daily': 'day', 'Weekly': 'week',
            'Semi-monthly': 'half-month', 'Monthly': 'month'}.get(per, 'month')
    fmt = lambda n: '₱{:,}'.format(int(n))
    if lo and hi:
        amt = f'{fmt(lo)}–{fmt(hi)}'
    elif lo:
        amt = f'{fmt(lo)}+'
    else:
        amt = f'up to {fmt(hi)}'
    return f'{amt} / {unit}'

app.jinja_env.globals['salary_text'] = salary_text

def req_summary(v):
    """Short human-readable requirement chips for a vacancy row/dict."""
    out = []
    g = _g(v, 'req_gender')
    if g in ('Male', 'Female'):
        out.append(g)
    lo, hi = _g(v, 'req_age_min'), _g(v, 'req_age_max')
    if lo and hi:
        out.append(f'{lo}\u2013{hi} yrs old')
    elif lo:
        out.append(f'{lo}+ yrs old')
    elif hi:
        out.append(f'Up to {hi} yrs old')
    if _g(v, 'req_education'):
        out.append(f"{_g(v, 'req_education')} or higher")
    m = _g(v, 'req_experience_months')
    if m:
        out.append(f'{m}+ mos. experience')
    req_s = _g(v, 'req_skills')
    if req_s:
        skills = [s.strip() for s in req_s.split(',') if s.strip()]
        if skills:
            out.append('Skills: ' + ', '.join(skills))
    return out

def _total_exp_months(ap):
    """Total months of work experience from an applicant's Work Experience JSON."""
    raw = _g(ap, 'work_history')
    if not raw:
        return 0
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return 0
    total = 0
    for e in (data or []):
        mo = str(e.get('months', '')).strip()
        if mo.isdigit():
            total += int(mo)
    return total

def req_warnings(v, ap):
    """Ways the applicant profile does not meet the vacancy's checkable requirements."""
    if not ap:
        return []
    w = []
    g, sex = _g(v, 'req_gender'), (_g(ap, 'sex') or '')
    if g in ('Male', 'Female') and sex and sex != g:
        w.append(f'Requires {g.lower()} applicants')
    age = _g(ap, 'age')
    lo, hi = _g(v, 'req_age_min'), _g(v, 'req_age_max')
    if age is not None:
        if lo and age < lo:
            w.append(f'Minimum age is {lo}')
        if hi and age > hi:
            w.append(f'Maximum age is {hi}')
    need, have = _g(v, 'req_education'), (_g(ap, 'educ_level') or '')
    if need in EDUC_RANK and have in EDUC_RANK and EDUC_RANK[have] < EDUC_RANK[need]:
        w.append(f'Requires {need} or higher')
    need_m = _g(v, 'req_experience_months')
    if need_m and _total_exp_months(ap) < need_m:
        w.append(f'Requires at least {need_m} months of work experience')
    req_s = _g(v, 'req_skills')
    if req_s:
        req_set = {s.strip().lower() for s in req_s.split(',') if s.strip()}
        have_set = {s.strip().lower() for s in (_g(ap, 'skills') or '').split(',') if s.strip()}
        if req_set and not req_set.intersection(have_set):
            w.append('None of the required skills match your profile')
    return w

def _vacancy_location(v):
    """Location string for a vacancy: the employer-specified job location when given,
    otherwise CSJDM if flagged local, else the employer's city/province (when joined
    into the row as e_city/e_province)."""
    explicit = (_g(v, 'job_location') or '').strip()
    if explicit:
        return explicit
    if _g(v, 'is_local'):
        return 'City of San Jose del Monte'
    parts = [p for p in (_g(v, 'e_city'), _g(v, 'e_province')) if p]
    return ', '.join(parts)

def _location_matches(v, ap):
    """True if the applicant's preferred local work location matches the vacancy's."""
    if not ap:
        return False
    pref = (_g(ap, 'pref_work_local') or '').strip().lower()
    if not pref:
        return False
    loc = _vacancy_location(v).lower()
    if loc and (pref in loc or loc in pref):
        return True
    if _g(v, 'is_local') and any(k in pref for k in ('san jose del monte', 'csjdm', 'sjdm')):
        return True
    return False

app.jinja_env.globals['req_summary'] = req_summary
app.jinja_env.globals['req_warnings'] = req_warnings

def get_recommendations(educ_level, preferred_position, skills, work_experience, vacancies,
                        applicant=None):
    """Two-layer hybrid recommender.
    Layer 1 (ML): rank the 5 occupational categories by predicted suitability.
    Layer 2 (rule-based): within each category, order the individual vacancies by
    how well the applicant meets their stated requirements (fewest unmet first).
    Layer 2 only reorders — it never hides or blocks a vacancy (soft-gate)."""
    if pipeline is None:
        return []
    vec   = pipeline['vectorizer']
    model = pipeline['model']
    text  = _clean_profile(educ_level, preferred_position, skills, work_experience)
    proba = model.predict_proba(vec.transform([text]))[0]
    cat_scores = sorted(
        [(CATEGORIES[i], round(float(proba[i]), 4)) for i in range(len(CATEGORIES))],
        key=lambda x: x[1], reverse=True,
    )
    vac_by_cat = {}
    for v in vacancies:
        unmet = len(req_warnings(v, applicant)) if applicant is not None else 0
        vac_by_cat.setdefault(v['occupational_category'], []).append({
            'id':         v['id'],
            'title':      v['job_title'],
            'employer':   v['employer_name'],
            'info':       v,
            'req_unmet':  unmet,
            'qualified':  unmet == 0,
            'location':   _vacancy_location(v),
            'loc_match':  _location_matches(v, applicant),
        })
    # Layer 2: within each category, best requirement-fit first, then preferred-location matches
    for cat_vacs in vac_by_cat.values():
        cat_vacs.sort(key=lambda x: (x['req_unmet'], 0 if x['loc_match'] else 1))
    results = []
    for rank, (cat_name, score) in enumerate(cat_scores, 1):
        results.append({
            'rank':              rank,
            'category':          cat_name,
            'icon':              CAT_ICONS.get(cat_name, 'bi-briefcase'),
            'suitability_score': score,
            'suitability_pct':   f'{score * 100:.1f}%',
            'vacancies':         vac_by_cat.get(cat_name, []),
        })
    return results

# ── AUTH HELPERS ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(_role_home())
            return f(*args, **kwargs)
        return decorated
    return decorator

def admin_required(f):
    return role_required(ROLE_ADMIN)(f)

def employer_required(f):
    return role_required(ROLE_EMPLOYER)(f)

def jobseeker_required(f):
    return role_required(ROLE_JOBSEEKER)(f)

def _role_home():
    role = session.get('role', ROLE_ADMIN)
    if role == ROLE_JOBSEEKER:
        return url_for('jobseeker_dashboard')
    if role == ROLE_EMPLOYER:
        return url_for('employer_dashboard')
    return url_for('home')

def current_user():
    if 'user_id' in session:
        return get_db().execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return None

# ── CONTEXT PROCESSOR ─────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    pending_employers_count = 0
    employer_approved = False
    role = session.get('role')
    if role == ROLE_ADMIN:
        try:
            pending_employers_count = get_db().execute(
                "SELECT COUNT(*) FROM employers WHERE is_approved=0 AND approval_requested=1"
            ).fetchone()[0]
        except Exception:
            pass
    elif role == ROLE_EMPLOYER:
        try:
            row = get_db().execute(
                'SELECT is_approved FROM employers WHERE user_id=?', (session.get('user_id'),)
            ).fetchone()
            employer_approved = bool(row and row['is_approved'])
        except Exception:
            pass
    return {
        'pipeline_loaded':         pipeline is not None,
        'session_role':            role or '',
        'pending_employers_count': pending_employers_count,
        'employer_approved':       employer_approved,
    }

# ── TEMPLATE FILTERS ──────────────────────────────────────────────────────────
_PHT = timedelta(hours=8)

def _now_ph():
    """Current Philippine time as a naive datetime (UTC+8)."""
    return datetime.now(timezone.utc).replace(tzinfo=None) + _PHT

def _today_ph():
    return _now_ph().strftime('%Y-%m-%d')

@app.template_filter('friendly_dt')
def friendly_dt(value):
    if not value:
        return ''
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(str(value), fmt) + _PHT
            return dt.strftime('%b %d, %Y · %I:%M %p').replace(' 0', ' ')
        except ValueError:
            continue
    return str(value)

@app.template_filter('friendly_date')
def friendly_date(value):
    if not value:
        return ''
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(str(value), fmt)
            if fmt != '%Y-%m-%d':
                dt += _PHT
            return dt.strftime('%b %d, %Y').replace(' 0', ' ')
        except ValueError:
            continue
    return str(value)

# ── PUBLIC ROUTES ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(_role_home())
    return render_template('landing.html')

@app.route('/jobs')
def public_jobs():
    db = get_db()
    search   = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    conds, params = [OPEN_VACANCY_SQL], []
    if search:
        conds.append('(job_title LIKE ? OR employer_name LIKE ?)')
        like = f'%{search}%'
        params += [like, like]
    if category:
        conds.append('occupational_category=?')
        params.append(category)
    vacancies = db.execute(
        f'SELECT * FROM job_vacancies WHERE {" AND ".join(conds)} ORDER BY created_at DESC',
        params
    ).fetchall()
    return render_template('public/jobs.html', vacancies=vacancies,
                           search=search, category=category,
                           categories=CATEGORY_LIST)

@app.route('/jobs/<int:vid>')
def public_job_detail(vid):
    db = get_db()
    v = db.execute(f'''
        SELECT jv.*, {EXPIRED_SQL} AS expired,
               e.company_name AS e_company, e.line_of_business,
               e.employer_sector, e.employer_type,
               e.address_line, e.barangay, e.city, e.province
        FROM job_vacancies jv
        LEFT JOIN employers e ON e.user_id = jv.employer_id
        WHERE jv.id=?
    ''', (vid,)).fetchone()
    if not v or not v['is_active']:
        flash('That job is no longer available.', 'danger')
        return redirect(url_for('public_jobs'))
    is_jobseeker = session.get('role') == ROLE_JOBSEEKER
    applied, profile_ok = False, True
    if is_jobseeker:
        ap = _get_my_applicant()
        if ap:
            profile_ok = bool(ap['educ_level'] and ap['preferred_position'] and ap['skills'])
            applied = bool(db.execute(
                "SELECT 1 FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status!='cancelled'",
                (ap['id'], vid)).fetchone())
    # Back link reflects where the visitor came from
    src = request.args.get('src', '')
    if is_jobseeker and src == 'rec':
        back_url, back_label = url_for('jobseeker_recommendations', generate=1), 'Back to recommendations'
    elif is_jobseeker and src == 'jobs':
        back_url, back_label = url_for('jobseeker_jobs'), 'Back to jobs'
    else:
        back_url, back_label = url_for('public_jobs'), 'Back to all jobs'
    return render_template('public/job_detail.html', v=v, is_jobseeker=is_jobseeker,
                           logged_in=('user_id' in session), applied=applied, profile_ok=profile_ok,
                           back_url=back_url, back_label=back_label)

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(_role_home())
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        ip       = request.remote_addr
        db       = get_db()
        user     = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        log_name = email
        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                           (user['id'], log_name, ip, 'denied_inactive'))
                db.commit()
                flash('Your account is deactivated. Contact an administrator.', 'danger')
            else:
                session.clear()
                session['user_id']   = user['id']
                session['full_name'] = user['full_name']
                session['role']      = user['role'] or ROLE_ADMIN
                db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                           (user['id'], log_name, ip, 'success'))
                db.commit()
                # Employer must be approved before accessing portal
                if session['role'] == ROLE_EMPLOYER:
                    emp = db.execute('SELECT is_approved FROM employers WHERE user_id=?',
                                     (user['id'],)).fetchone()
                    if not emp or not emp['is_approved']:
                        return redirect(url_for('employer_profile'))
                return redirect(_role_home())
        else:
            uid = user['id'] if user else None
            db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                       (uid, log_name, ip, 'failed'))
            db.commit()
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(_role_home())
    role = request.values.get('role', '')
    if request.method == 'POST':
        f         = request.form
        full_name = f.get('full_name', '').strip()
        email     = f.get('email', '').strip()
        confirm   = f.get('confirm_email', '').strip()
        pw        = f.get('password', '')
        role      = f.get('role', '').strip()

        errs = []
        if not all([full_name, email, pw]):
            errs.append('All required fields must be filled.')
        if role not in (ROLE_JOBSEEKER, ROLE_EMPLOYER):
            errs.append('Please choose whether you are a jobseeker or an employer.')
        if email and not EMAIL_RE.match(email):
            errs.append('Please enter a valid email address.')
        if email.lower() != confirm.lower():
            errs.append('Email addresses do not match.')
        if len(pw) < 8:
            errs.append('Password must be at least 8 characters.')
        if errs:
            for e in errs:
                flash(e, 'danger')
            return render_template('auth/signup.html', form=f, role=role)
        db = get_db()
        try:
            cur = db.execute(
                'INSERT INTO users (full_name, email, password_hash, role) VALUES (?,?,?,?)',
                (full_name, email, generate_password_hash(pw), role)
            )
            uid = cur.lastrowid
            if role == ROLE_JOBSEEKER:
                parts = full_name.split()
                first, last = parts[0], ' '.join(parts[1:])
                # Profile details (education, skills, etc.) are completed later
                db.execute(
                    'INSERT INTO applicants (first_name, last_name, employment_status, '
                    'educ_level, preferred_position, skills, user_id) VALUES (?,?,?,?,?,?,?)',
                    (first, last, 'Unemployed', '', '', '', uid)
                )
                msg = 'Account created! Log in and complete your profile to get job recommendations.'
            else:
                # Company details are encoded later via the Company Profile page
                db.execute(
                    'INSERT INTO employers (user_id, company_name, contact_person, profile_completed) '
                    'VALUES (?,?,?,0)',
                    (uid, '', '')
                )
                msg = ('Account created! Log in to encode your company profile — '
                       'PESO admin will review and approve it before you can post vacancies.')
            db.commit()
            flash(msg, 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            db.rollback()
            flash('That email is already registered.', 'danger')
    return render_template('auth/signup.html', form={}, role=role)

@app.route('/settings/password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = current_user()
    role = session.get('role')
    # Render inside the user's own portal layout, and send Cancel back where they came from
    layout = {ROLE_EMPLOYER: 'base_employer.html',
              ROLE_JOBSEEKER: 'base_jobseeker.html'}.get(role, 'base.html')
    cancel_url = {ROLE_EMPLOYER: url_for('employer_account'),
                  ROLE_JOBSEEKER: url_for('jobseeker_account')}.get(role, url_for('home'))
    if request.method == 'POST':
        cur  = request.form.get('current_password', '')
        new  = request.form.get('new_password', '')
        conf = request.form.get('confirm_password', '')
        if not check_password_hash(user['password_hash'], cur):
            flash('Current password is incorrect.', 'danger')
        elif new != conf:
            flash('New passwords do not match.', 'danger')
        elif len(new) < 8:
            flash('Password must be at least 8 characters.', 'danger')
        else:
            get_db().execute('UPDATE users SET password_hash = ? WHERE id = ?',
                             (generate_password_hash(new), user['id']))
            get_db().commit()
            flash('Password changed successfully.', 'success')
            return redirect(_role_home())
    return render_template('settings/password.html', user=user,
                           layout=layout, cancel_url=cancel_url)

# ── JOBSEEKER PORTAL ──────────────────────────────────────────────────────────
def _get_my_applicant():
    return get_db().execute(
        'SELECT * FROM applicants WHERE user_id=?', (session['user_id'],)
    ).fetchone()

def _active_referral(applicant_id):
    """The applicant's current active (not-withdrawn) referral, if any.
    An applicant may hold only one active referral at a time."""
    return get_db().execute(
        "SELECT r.id, r.vacancy_id, jv.job_title "
        "FROM referrals r JOIN job_vacancies jv ON r.vacancy_id = jv.id "
        "WHERE r.applicant_id=? AND r.status != 'cancelled' "
        "ORDER BY r.referred_at DESC LIMIT 1", (applicant_id,)
    ).fetchone()

@app.route('/jobseeker/dashboard')
@jobseeker_required
def jobseeker_dashboard():
    db  = get_db()
    ap  = _get_my_applicant()
    top_rec = None
    referrals = []
    if ap:
        referrals = db.execute('''
            SELECT r.*, jv.job_title, jv.employer_name, jv.occupational_category
            FROM referrals r
            JOIN job_vacancies jv ON r.vacancy_id = jv.id
            WHERE r.applicant_id = ?
            ORDER BY r.referred_at DESC LIMIT 5
        ''', (ap['id'],)).fetchall()

        if pipeline and ap['educ_level'] and ap['preferred_position'] and ap['skills']:
            vacancies = db.execute(
                'SELECT id, employer_name, job_title, occupational_category '
                f'FROM job_vacancies WHERE {OPEN_VACANCY_SQL}'
            ).fetchall()
            recs = get_recommendations(
                ap['educ_level'], ap['preferred_position'],
                ap['skills'], ap['work_experience'] or '',
                [dict(v) for v in vacancies], applicant=ap
            )
            top_rec = recs[0] if recs else None

    active_vacancies = db.execute(
        'SELECT COUNT(*) FROM job_vacancies WHERE is_active=1'
    ).fetchone()[0]

    return render_template('jobseeker/dashboard.html',
                           ap=ap, top_rec=top_rec,
                           referrals=referrals,
                           active_vacancies=active_vacancies)

@app.route('/jobseeker/profile', methods=['GET', 'POST'])
@jobseeker_required
def jobseeker_profile():
    db = get_db()
    ap = _get_my_applicant()
    if not ap:
        flash('Profile not found. Contact PESO admin.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    if request.method == 'POST':
        f    = request.form
        brgy = f.get('barangay', '').strip()
        bd   = f.get('birthdate', '').strip()
        # Age is derived from date of birth; fall back to a typed age if no DOB
        age = None
        if bd:
            try:
                b     = datetime.strptime(bd, '%Y-%m-%d')
                today = _now_ph()
                age   = today.year - b.year - ((today.month, today.day) < (b.month, b.day))
            except ValueError:
                age = None
        if age is None:
            a = f.get('age', '').strip()
            age = int(a) if a.isdigit() else None

        def rows(prefix, keys):
            lists = [f.getlist(f'{prefix}_{k}[]') for k in keys]
            out = []
            for tup in zip(*lists):
                tup = [x.strip() for x in tup]
                if any(tup):
                    out.append(dict(zip(keys, tup)))
            return out

        education   = rows('edu',  ['level', 'school', 'course', 'year', 'awards'])
        trainings   = rows('trn',  ['course', 'institution', 'hours', 'certificate'])
        eligibils   = rows('elig', ['title', 'rating', 'date'])
        work_hist   = rows('we',   ['company', 'address', 'position', 'months', 'status'])

        languages = []
        for lang in LANGUAGE_CHOICES:
            key   = lang.lower()
            flags = {s: bool(f.get(f'lang_{key}_{s}')) for s in ('read', 'write', 'speak', 'understand')}
            if any(flags.values()):
                languages.append({'language': lang, **flags})

        disability = f.getlist('disability')
        dis_other  = f.get('disability_other', '').strip()
        if 'Others' in disability and dis_other:
            disability = [d for d in disability if d != 'Others'] + [dis_other]
        os_other     = f.get('other_skills_other', '').strip()
        other_skills = (f.getlist('other_skills') + ([os_other] if os_other else []))[:5]

        # ── derive the ML inputs from the structured data ──
        ml_educ, best = '', -1
        for e in education:
            r = EDUC_RANK.get(e.get('level', ''), 0)
            if e.get('level') and r >= best:
                best, ml_educ = r, e['level']
        if not ml_educ:
            ml_educ = f.get('educ_level', '').strip()
        ml_pref   = f.get('preferred_position', '').strip()
        skills_items = [s.strip() for s in f.get('skills', '').split(',') if s.strip()][:5]
        skills_in = ', '.join(skills_items)
        ml_skills = ', '.join([s for s in ([skills_in] + other_skills) if s])
        positions = [w['position'] for w in work_hist if w.get('position')]
        ml_workx  = ', '.join(positions)

        db.execute('''UPDATE applicants SET
            first_name=?, middle_name=?, last_name=?, suffix=?,
            sex=?, age=?, birthdate=?, civil_status=?,
            address_line=?, barangay=?, district=?, city=?, province=?,
            height_cm=?, religion=?, tin=?, landline=?, contact_number=?,
            is_pwd=?, disability=?,
            is_4ps=?, household_id=?, is_wodp=?, is_dswd_foodstamp=?, is_caregiver=?,
            is_ofw=?, ofw_country=?, is_former_ofw=?, former_ofw_country=?, ofw_return_date=?,
            employment_status=?, employed_type=?, unemployed_reason=?, job_search_months=?,
            preferred_position=?, pref_work_local=?, pref_work_overseas=?,
            languages=?, education=?, trainings=?, eligibilities=?, work_history=?, other_skills=?,
            educ_level=?, skills=?, work_experience=?,
            certified=?, certified_at=CURRENT_TIMESTAMP
            WHERE id=?''', (
            f.get('first_name', '').strip(), f.get('middle_name', '').strip(),
            f.get('last_name', '').strip(), f.get('suffix', '').strip(),
            f.get('sex', ''), age, bd, f.get('civil_status', '').strip(),
            f.get('address_line', '').strip(), brgy, barangay_to_district(brgy),
            f.get('city', '').strip(), f.get('province', '').strip(),
            f.get('height_cm', '').strip(), f.get('religion', '').strip(),
            f.get('tin', '').strip(), f.get('landline', '').strip(),
            f.get('contact_number', '').strip(),
            1 if disability else 0, json.dumps(disability),
            1 if f.get('is_4ps') else 0, f.get('household_id', '').strip(),
            1 if f.get('is_wodp') else 0, 1 if f.get('is_dswd_foodstamp') else 0,
            1 if f.get('is_caregiver') else 0,
            1 if f.get('is_ofw') else 0, f.get('ofw_country', '').strip(),
            1 if f.get('is_former_ofw') else 0, f.get('former_ofw_country', '').strip(),
            f.get('ofw_return_date', '').strip(),
            f.get('employment_status', 'Unemployed'), f.get('employed_type', '').strip(),
            f.get('unemployed_reason', '').strip(),
            int(f.get('job_search_months')) if f.get('job_search_months', '').strip().isdigit() else None,
            ml_pref, f.get('pref_work_local', '').strip(), f.get('pref_work_overseas', '').strip(),
            json.dumps(languages), json.dumps(education), json.dumps(trainings),
            json.dumps(eligibils), json.dumps(work_hist), json.dumps(other_skills),
            ml_educ, ml_skills, ml_workx,
            1 if f.get('certify') else 0,
            ap['id'],
        ))
        db.commit()
        flash('Profile saved.', 'success')
        return redirect(url_for('jobseeker_profile'))

    ap_d = dict(ap)
    for jcol in ('languages', 'education', 'trainings', 'eligibilities',
                 'work_history', 'other_skills', 'disability'):
        try:
            ap_d[jcol] = json.loads(ap_d.get(jcol) or '[]')
        except (ValueError, TypeError):
            ap_d[jcol] = []
    return render_template('jobseeker/profile.html', ap=ap_d, user=current_user(),
                           educ_levels=EDUC_LEVELS,
                           barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
                           barangay_district_map=BARANGAY_DISTRICT,
                           positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
                           suffixes=SUFFIX_CHOICES, civil_statuses=CIVIL_STATUS_CHOICES,
                           religions=RELIGION_CHOICES, disability_types=DISABILITY_TYPES,
                           languages_list=LANGUAGE_CHOICES, employed_types=EMPLOYED_TYPES,
                           unemployed_reasons=UNEMPLOYED_REASONS,
                           work_status_choices=WORK_STATUS_CHOICES,
                           other_skills_choices=OTHER_SKILLS_CHOICES)

@app.route('/jobseeker/account', methods=['GET', 'POST'])
@jobseeker_required
def jobseeker_account():
    db   = get_db()
    user = current_user()
    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        mail = request.form.get('email', '').strip()
        if not name or not mail:
            flash('Full name and email are required.', 'danger')
        elif not EMAIL_RE.match(mail):
            flash('Please enter a valid email address.', 'danger')
        else:
            try:
                db.execute('UPDATE users SET full_name=?, email=? WHERE id=?',
                           (name, mail, user['id']))
                db.commit()
                session['full_name'] = name
                flash('Account updated.', 'success')
                return redirect(url_for('jobseeker_account'))
            except sqlite3.IntegrityError:
                flash('That email is already in use by another account.', 'danger')
        user = {**dict(user), 'full_name': name, 'email': mail}
    return render_template('jobseeker/account.html', user=dict(user))

@app.route('/jobseeker/account/delete', methods=['POST'])
@jobseeker_required
def jobseeker_account_delete():
    db  = get_db()
    uid = session['user_id']
    ap  = _get_my_applicant()
    if ap:
        db.execute('DELETE FROM referrals WHERE applicant_id=?', (ap['id'],))
        db.execute('DELETE FROM recommendations WHERE applicant_id=?', (ap['id'],))
        db.execute('DELETE FROM applicants WHERE id=?', (ap['id'],))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute("DELETE FROM users WHERE id=? AND role='jobseeker'", (uid,))
    db.commit()
    session.clear()
    flash('Your account has been permanently deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/jobseeker/recommendations')
@jobseeker_required
def jobseeker_recommendations():
    db  = get_db()
    ap  = _get_my_applicant()
    results = []
    generated = False
    profile_ok = bool(ap and ap['educ_level'] and ap['preferred_position'] and ap['skills'])
    if profile_ok and request.args.get('generate') and pipeline:
        vacancies = db.execute(
            'SELECT jv.*, e.city AS e_city, e.province AS e_province '
            'FROM job_vacancies jv LEFT JOIN employers e ON e.user_id = jv.employer_id '
            f'WHERE {OPEN_VACANCY_SQL}'
        ).fetchall()
        results = get_recommendations(
            ap['educ_level'], ap['preferred_position'],
            ap['skills'], ap['work_experience'] or '',
            [dict(v) for v in vacancies], applicant=ap
        )
        generated = True
        # Keep only the latest generated set for this applicant
        db.execute('DELETE FROM recommendations WHERE applicant_id=?', (ap['id'],))
        for cat in results:
            for vac in cat['vacancies']:
                db.execute(
                    'INSERT INTO recommendations '
                    '(applicant_id,vacancy_id,suitability_score,rank,generated_by) VALUES (?,?,?,?,?)',
                    (ap['id'], vac['id'], cat['suitability_score'], cat['rank'], session['user_id'])
                )
        db.commit()
    applied_ids = set()
    active = None
    if ap:
        applied_ids = {r['vacancy_id'] for r in db.execute(
            "SELECT vacancy_id FROM referrals WHERE applicant_id=? AND status != 'cancelled'",
            (ap['id'],)
        ).fetchall()}
        active = _active_referral(ap['id'])
    return render_template('jobseeker/recommendations.html',
                           ap=ap, results=results, generated=generated,
                           profile_ok=profile_ok, applied_ids=applied_ids,
                           has_active_referral=bool(active), active_referral=active,
                           pipeline_loaded=pipeline is not None)

@app.route('/jobseeker/referrals')
@jobseeker_required
def jobseeker_referrals():
    db = get_db()
    ap = _get_my_applicant()
    my_referrals = []
    if ap:
        my_referrals = db.execute('''
            SELECT r.*, jv.job_title, jv.employer_name, jv.occupational_category
            FROM referrals r
            JOIN job_vacancies jv ON r.vacancy_id = jv.id
            WHERE r.applicant_id = ?
            ORDER BY r.referred_at DESC
        ''', (ap['id'],)).fetchall()
    return render_template('jobseeker/referrals.html', ap=ap, my_referrals=my_referrals)

@app.route('/jobseeker/jobs')
@jobseeker_required
def jobseeker_jobs():
    db       = get_db()
    ap       = _get_my_applicant()
    search   = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    conds, params = [OPEN_VACANCY_SQL], []
    if search:
        conds.append('(job_title LIKE ? OR employer_name LIKE ?)')
        like = f'%{search}%'
        params += [like, like]
    if category:
        conds.append('occupational_category=?')
        params.append(category)
    vacancies = db.execute(
        f'SELECT * FROM job_vacancies WHERE {" AND ".join(conds)} ORDER BY created_at DESC', params
    ).fetchall()
    applied_ids = set()
    if ap:
        applied_ids = {r['vacancy_id'] for r in db.execute(
            "SELECT vacancy_id FROM referrals WHERE applicant_id=? AND status != 'cancelled'",
            (ap['id'],)
        ).fetchall()}
    profile_ok = bool(ap and ap['educ_level'] and ap['preferred_position'] and ap['skills'])
    return render_template('jobseeker/jobs.html', ap=ap, vacancies=vacancies,
                           applied_ids=applied_ids, profile_ok=profile_ok,
                           search=search, category=category, categories=CATEGORY_LIST)

@app.route('/jobseeker/apply/<int:vid>/confirm')
@jobseeker_required
def jobseeker_apply_confirm(vid):
    db = get_db()
    ap = _get_my_applicant()
    if not ap:
        flash('Profile not found.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    if not ap['educ_level'] or not ap['preferred_position'] or not ap['skills']:
        flash('Please complete your profile before applying.', 'warning')
        return redirect(url_for('jobseeker_profile'))
    jv = db.execute(
        f'SELECT * FROM job_vacancies WHERE id=? AND {OPEN_VACANCY_SQL}', (vid,)
    ).fetchone()
    if not jv:
        flash('That job is no longer available or its deadline has passed.', 'danger')
        return redirect(url_for('jobseeker_recommendations') + '?generate=1')
    existing = db.execute(
        "SELECT id FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status != 'cancelled'",
        (ap['id'], vid)
    ).fetchone()
    if existing:
        flash(f'You have already applied for "{jv["job_title"]}".', 'info')
        return redirect(url_for('referral_slip', rid=existing['id']))
    active = _active_referral(ap['id'])
    if active:
        flash(f'You already have an active referral for "{active["job_title"]}". '
              'Withdraw it from My Applications before applying to another job.', 'warning')
        return redirect(url_for('jobseeker_referrals'))
    score = None
    if pipeline:
        recs = get_recommendations(
            ap['educ_level'], ap['preferred_position'],
            ap['skills'], ap['work_experience'] or '', [dict(jv)], applicant=ap
        )
        for cat in recs:
            if cat['category'] == jv['occupational_category']:
                score = cat['suitability_score']
                break
    return render_template('jobseeker/apply_confirm.html', ap=ap, v=jv,
                           score=score, warnings=req_warnings(jv, ap))

@app.route('/jobseeker/apply', methods=['POST'])
@jobseeker_required
def jobseeker_apply():
    ap = _get_my_applicant()
    if not ap:
        flash('Profile not found.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    if not ap['educ_level'] or not ap['preferred_position'] or not ap['skills']:
        flash('Please complete your profile before applying.', 'warning')
        return redirect(url_for('jobseeker_profile'))
    db = get_db()
    vacancy_id = request.form.get('vacancy_id', type=int)
    jv = db.execute(
        f'SELECT * FROM job_vacancies WHERE id=? AND {OPEN_VACANCY_SQL}',
        (vacancy_id,)
    ).fetchone() if vacancy_id else None
    back = url_for('jobseeker_recommendations') + '?generate=1'
    if not jv:
        flash('That job is no longer available or its deadline has passed.', 'danger')
        return redirect(back)
    existing = db.execute(
        "SELECT id FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status != 'cancelled'",
        (ap['id'], vacancy_id)
    ).fetchone()
    if existing:
        flash(f'You have already applied for "{jv["job_title"]}".', 'info')
        return redirect(url_for('referral_slip', rid=existing['id']))
    active = _active_referral(ap['id'])
    if active:
        flash(f'You already have an active referral for "{active["job_title"]}". '
              'Withdraw it from My Applications before applying to another job.', 'warning')
        return redirect(url_for('jobseeker_referrals'))
    # Capture the ML suitability score for this vacancy's category (soft-gate signal)
    score = None
    if pipeline:
        recs = get_recommendations(
            ap['educ_level'], ap['preferred_position'],
            ap['skills'], ap['work_experience'] or '', [dict(jv)]
        )
        for cat in recs:
            if cat['category'] == jv['occupational_category']:
                score = cat['suitability_score']
                break
    cur = db.execute(
        'INSERT INTO referrals (applicant_id, vacancy_id, referred_by, status, suitability_score) '
        'VALUES (?,?,?,?,?)',
        (ap['id'], vacancy_id, session['user_id'], 'referred', score)
    )
    db.commit()
    rid = cur.lastrowid
    flash(f'Application submitted for "{jv["job_title"]}" at {jv["employer_name"]}!', 'success')
    return redirect(url_for('referral_slip', rid=rid))

@app.route('/jobseeker/referrals/<int:rid>/cancel', methods=['POST'])
@jobseeker_required
def jobseeker_cancel_referral(rid):
    db = get_db()
    ap = _get_my_applicant()
    if not ap:
        flash('Profile not found.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    r = db.execute(
        'SELECT r.status, jv.job_title FROM referrals r '
        'JOIN job_vacancies jv ON r.vacancy_id = jv.id '
        'WHERE r.id=? AND r.applicant_id=?',
        (rid, ap['id'])
    ).fetchone()
    if not r:
        flash('Application not found.', 'danger')
        return redirect(url_for('jobseeker_referrals'))
    if r['status'] == 'cancelled':
        flash('That application is already cancelled.', 'info')
        return redirect(url_for('jobseeker_referrals'))
    db.execute("UPDATE referrals SET status='cancelled' WHERE id=?", (rid,))
    db.commit()
    flash(f'Application for "{r["job_title"]}" has been withdrawn.', 'success')
    return redirect(url_for('jobseeker_referrals'))

# ── EMPLOYER PORTAL ───────────────────────────────────────────────────────────
def _get_my_employer():
    return get_db().execute(
        'SELECT * FROM employers WHERE user_id=?', (session['user_id'],)
    ).fetchone()

def _emp_form(emp):
    """Employer row as a dict with NULL columns shown as empty strings, so the
    profile form renders blank fields (with their placeholders) instead of 'None'."""
    return {k: ('' if v is None else v) for k, v in dict(emp).items()}

@app.route('/employer/pending')
@login_required
def employer_pending():
    if session.get('role') != ROLE_EMPLOYER:
        return redirect(_role_home())
    emp = _get_my_employer()
    if emp and emp['is_approved']:
        return redirect(url_for('employer_dashboard'))
    return render_template('employer/pending.html', emp=emp)

@app.route('/employer/profile', methods=['GET', 'POST'])
@employer_required
def employer_profile():
    db  = get_db()
    emp = _get_my_employer()
    if not emp:
        flash('Employer record not found.', 'danger')
        return redirect(_role_home())
    tmpl_kwargs = dict(sectors=EMPLOYER_SECTORS, employer_types=EMPLOYER_TYPES,
                       workforce_sizes=WORKFORCE_SIZES, location_types=LOCATION_TYPES,
                       barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title))
    if request.method == 'POST':
        f        = request.form
        sector   = f.get('employer_sector', '').strip()
        emp_type = f.get('employer_type', '').strip()
        mail     = f.get('profile_email', '').strip()
        required = {
            'Business name':             f.get('company_name', '').strip(),
            'TIN':                       f.get('tin', '').strip(),
            'Location type':             f.get('location_type', '').strip(),
            'Employer sector':           sector,
            'Employer type':             emp_type,
            'Total work force':          f.get('total_workforce', '').strip(),
            'Line of business/industry': f.get('line_of_business', '').strip(),
            'Address':                   f.get('address_line', '').strip(),
            'Barangay':                  f.get('barangay', '').strip(),
            'City/Municipality':         f.get('city', '').strip(),
            'Province':                  f.get('province', '').strip(),
            'Contact person':            f.get('contact_person', '').strip(),
            'Position':                  f.get('position', '').strip(),
            'Mobile no.':                f.get('mobile', '').strip(),
            'Email address':             mail,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            err = 'Please fill in: ' + ', '.join(missing) + '.'
        elif sector not in EMPLOYER_TYPES or emp_type not in EMPLOYER_TYPES.get(sector, []):
            err = 'Please select a valid employer type for the chosen sector.'
        elif not EMAIL_RE.match(mail):
            err = 'Please enter a valid contact email address.'
        else:
            err = None
        if err:
            flash(err, 'danger')
            return render_template('employer/profile.html',
                                   emp={**_emp_form(emp), **f.to_dict()}, **tmpl_kwargs)
        db.execute('''
            UPDATE employers SET
              tin=?, company_name=?, trade_name=?, location_type=?, employer_sector=?,
              employer_type=?, total_workforce=?, line_of_business=?,
              address_line=?, barangay=?, city=?, province=?,
              contact_person=?, position=?, telephone=?, mobile=?, fax=?, profile_email=?,
              certified=1, certified_at=CURRENT_TIMESTAMP, profile_completed=1
            WHERE id=?
        ''', (
            required['TIN'], required['Business name'], f.get('trade_name', '').strip(),
            required['Location type'], sector, emp_type, required['Total work force'],
            required['Line of business/industry'], required['Address'], required['Barangay'],
            required['City/Municipality'], required['Province'], required['Contact person'],
            required['Position'], f.get('telephone', '').strip(), required['Mobile no.'],
            f.get('fax', '').strip(), mail, emp['id'],
        ))
        db.commit()
        flash('Company profile saved.', 'success')
        return redirect(url_for('employer_dashboard') if emp['is_approved']
                        else url_for('employer_profile'))
    return render_template('employer/profile.html', emp=_emp_form(emp), **tmpl_kwargs)

@app.route('/employer/request-approval', methods=['POST'])
@employer_required
def employer_request_approval():
    db  = get_db()
    emp = _get_my_employer()
    if not emp:
        return redirect(_role_home())
    if emp['is_approved']:
        return redirect(url_for('employer_dashboard'))
    if not emp['profile_completed']:
        flash('Please complete all company profile fields before requesting approval.', 'warning')
        return redirect(url_for('employer_profile'))
    db.execute('UPDATE employers SET approval_requested=1 WHERE id=?', (emp['id'],))
    db.commit()
    flash('Approval request sent. PESO admin will review your company profile.', 'success')
    return redirect(url_for('employer_profile'))

@app.route('/employer/account', methods=['GET', 'POST'])
@employer_required
def employer_account():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db   = get_db()
    user = current_user()
    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        mail = request.form.get('email', '').strip()
        if not name or not mail:
            flash('Full name and email are required.', 'danger')
        elif not EMAIL_RE.match(mail):
            flash('Please enter a valid email address.', 'danger')
        else:
            try:
                db.execute('UPDATE users SET full_name=?, email=? WHERE id=?',
                           (name, mail, user['id']))
                db.commit()
                session['full_name'] = name
                flash('Account updated.', 'success')
                return redirect(url_for('employer_account'))
            except sqlite3.IntegrityError:
                flash('That email is already in use by another account.', 'danger')
        user = {**dict(user), 'full_name': name, 'email': mail}
    return render_template('employer/account.html', user=dict(user))

@app.route('/employer/account/delete', methods=['POST'])
@employer_required
def employer_account_delete():
    db  = get_db()
    uid = session['user_id']
    vac_ids = [r['id'] for r in db.execute(
        'SELECT id FROM job_vacancies WHERE employer_id=?', (uid,)).fetchall()]
    for vid in vac_ids:
        db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
        db.execute('DELETE FROM referrals WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE employer_id=?', (uid,))
    db.execute('DELETE FROM employers WHERE user_id=?', (uid,))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute("DELETE FROM users WHERE id=? AND role='employer'", (uid,))
    db.commit()
    session.clear()
    flash('Your employer account has been permanently deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/employer/dashboard')
@employer_required
def employer_dashboard():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db  = get_db()
    uid = session['user_id']
    # Active = truly open (active and not past deadline); expired = active but deadline passed
    active_vac = db.execute(
        f'SELECT COUNT(*) FROM job_vacancies WHERE employer_id=? AND {OPEN_VACANCY_SQL}', (uid,)
    ).fetchone()[0]
    expired_vac = db.execute(
        f'SELECT COUNT(*) FROM job_vacancies WHERE employer_id=? AND is_active=1 AND {EXPIRED_SQL}', (uid,)
    ).fetchone()[0]
    total_referred = db.execute(
        'SELECT COUNT(*) FROM referrals r JOIN job_vacancies jv ON r.vacancy_id=jv.id '
        "WHERE jv.employer_id=? AND r.status!='cancelled'", (uid,)
    ).fetchone()[0]
    new_this_week = db.execute(
        'SELECT COUNT(*) FROM referrals r JOIN job_vacancies jv ON r.vacancy_id=jv.id '
        "WHERE jv.employer_id=? AND r.status!='cancelled' "
        "AND date(r.referred_at) >= date('now','+8 hours','-7 days')", (uid,)
    ).fetchone()[0]
    recent_referrals = db.execute('''
        SELECT r.id, r.status, r.referred_at, r.suitability_score,
               a.first_name, a.last_name, jv.job_title
        FROM referrals r
        JOIN applicants a ON r.applicant_id=a.id
        JOIN job_vacancies jv ON r.vacancy_id=jv.id
        WHERE jv.employer_id=?
        ORDER BY r.referred_at DESC LIMIT 5
    ''', (uid,)).fetchall()
    # Vacancies expiring tomorrow (one-day warning to renew the deadline)
    expiring_soon = db.execute('''
        SELECT jv.id, jv.job_title, jv.application_deadline
        FROM job_vacancies jv
        WHERE jv.employer_id=? AND jv.is_active=1
          AND jv.application_deadline = date('now','+8 hours','+1 day')
        ORDER BY jv.job_title
    ''', (uid,)).fetchall()
    return render_template('employer/dashboard.html', emp=emp,
                           active_vac=active_vac, expired_vac=expired_vac,
                           total_referred=total_referred, new_this_week=new_this_week,
                           recent_referrals=recent_referrals, expiring_soon=expiring_soon)

@app.route('/employer/vacancies')
@employer_required
def employer_vacancies():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db     = get_db()
    status = request.args.get('status', 'active')
    conds  = ['employer_id=?']
    params = [session['user_id']]
    if status == 'active':
        conds.append('is_active=1')
    elif status == 'inactive':
        conds.append('is_active=0')
    vacancies = db.execute(
        f'SELECT *, {EXPIRED_SQL} AS expired FROM job_vacancies WHERE {" AND ".join(conds)} ORDER BY created_at DESC',
        params
    ).fetchall()
    return render_template('employer/vacancies.html', emp=emp,
                           vacancies=vacancies, status=status,
                           categories=CATEGORY_LIST)

@app.route('/employer/vacancies/add', methods=['GET', 'POST'])
@employer_required
def employer_vacancy_add():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    if request.method == 'POST':
        f = request.form
        req, err = parse_vacancy_requirements(f)
        if not f.get('job_title') or not f.get('occupational_category'):
            err = 'Job title and occupational category are required.'
        elif not err and req['application_deadline'] and req['application_deadline'] < _today_ph():
            err = 'Application deadline cannot be in the past.'
        if err:
            flash(err, 'danger')
            return render_template('employer/vacancy_form.html', emp=emp,
                                   vacancy=f, categories=CATEGORY_LIST, action='add',
                                   educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                                   salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST)
        get_db().execute(
            'INSERT INTO job_vacancies (employer_name, job_title, occupational_category, '
            'is_local, employer_id, ' + ', '.join(REQ_COLS) + ') VALUES (?,?,?,?,?,' +
            ','.join('?' * len(REQ_COLS)) + ')',
            (emp['company_name'], f.get('job_title', '').strip(),
             f.get('occupational_category', ''),
             1 if f.get('is_local', '1') == '1' else 0,
             session['user_id'], *[req[c] for c in REQ_COLS])
        )
        get_db().commit()
        flash('Job vacancy posted.', 'success')
        return redirect(url_for('employer_vacancies'))
    return render_template('employer/vacancy_form.html', emp=emp,
                           vacancy=None, categories=CATEGORY_LIST, action='add',
                           educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                           salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST)

@app.route('/employer/vacancies/<int:vid>/edit', methods=['GET', 'POST'])
@employer_required
def employer_vacancy_edit(vid):
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db = get_db()
    v  = db.execute(
        'SELECT * FROM job_vacancies WHERE id=? AND employer_id=?',
        (vid, session['user_id'])
    ).fetchone()
    if not v:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('employer_vacancies'))
    if request.method == 'POST':
        f = request.form
        req, err = parse_vacancy_requirements(f)
        if (not err and req['application_deadline'] and req['application_deadline'] < _today_ph()
                and req['application_deadline'] != v['application_deadline']):
            err = 'Application deadline cannot be in the past.'
        if err:
            flash(err, 'danger')
            return render_template('employer/vacancy_form.html', emp=emp,
                                   vacancy={**dict(v), **f.to_dict()}, categories=CATEGORY_LIST,
                                   action='edit', educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                                   salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST)
        db.execute(
            'UPDATE job_vacancies SET job_title=?, occupational_category=?, is_local=?, ' +
            ', '.join(f'{c}=?' for c in REQ_COLS) + ' WHERE id=?',
            (f.get('job_title', '').strip(), f.get('occupational_category', ''),
             1 if f.get('is_local', '1') == '1' else 0, *[req[c] for c in REQ_COLS], vid)
        )
        db.commit()
        flash('Vacancy updated.', 'success')
        return redirect(url_for('employer_vacancies'))
    return render_template('employer/vacancy_form.html', emp=emp,
                           vacancy=dict(v), categories=CATEGORY_LIST, action='edit',
                           educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                           salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST)

@app.route('/employer/vacancies/<int:vid>/toggle', methods=['POST'])
@employer_required
def employer_vacancy_toggle(vid):
    db = get_db()
    v  = db.execute(
        'SELECT is_active FROM job_vacancies WHERE id=? AND employer_id=?',
        (vid, session['user_id'])
    ).fetchone()
    if v:
        db.execute('UPDATE job_vacancies SET is_active=? WHERE id=?',
                   (0 if v['is_active'] else 1, vid))
        db.commit()
        flash('Vacancy status updated.', 'success')
    return redirect(url_for('employer_vacancies'))

@app.route('/employer/referred')
@employer_required
def employer_referred():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db     = get_db()
    status = request.args.get('status', 'all')
    conds  = ['jv.employer_id=?']
    params = [session['user_id']]
    if status != 'all':
        conds.append('r.status=?')
        params.append(status)
    referrals = db.execute(f'''
        SELECT r.*, a.first_name, a.last_name, jv.job_title
        FROM referrals r
        JOIN applicants a ON r.applicant_id=a.id
        JOIN job_vacancies jv ON r.vacancy_id=jv.id
        WHERE {" AND ".join(conds)}
        ORDER BY r.referred_at DESC
    ''', params).fetchall()
    return render_template('employer/referred.html', emp=emp,
                           referrals=referrals, status=status)

@app.route('/employer/referred/<int:rid>')
@employer_required
def employer_referred_detail(rid):
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db = get_db()
    r = db.execute('''
        SELECT r.id AS referral_id, r.suitability_score AS score,
               r.status AS ref_status, r.referred_at AS ref_at,
               a.first_name, a.last_name, a.sex, a.age, a.barangay, a.district,
               a.employment_status, a.is_pwd, a.educ_level, a.preferred_position,
               a.skills, a.work_experience, a.work_history, a.contact_number,
               jv.job_title, jv.occupational_category,
               jv.req_gender, jv.req_age_min, jv.req_age_max, jv.req_education,
               jv.req_experience_months,
               u.email AS applicant_email
        FROM referrals r
        JOIN applicants a     ON r.applicant_id = a.id
        JOIN job_vacancies jv ON r.vacancy_id   = jv.id
        LEFT JOIN users u     ON a.user_id       = u.id
        WHERE r.id=? AND jv.employer_id=?
    ''', (rid, session['user_id'])).fetchone()
    if not r:
        flash('Referred applicant not found.', 'danger')
        return redirect(url_for('employer_referred'))
    return render_template('employer/referred_detail.html', r=r,
                           chips=req_summary(r), warnings=req_warnings(r, r))

# ── HOME / OVERVIEW (admin) ──────────────────────────────────────────────────
@app.route('/home')
@admin_required
def home():
    db = get_db()
    total_applicants = db.execute(
        'SELECT COUNT(*) FROM applicants WHERE is_archived=0'
    ).fetchone()[0]
    active_vacancies = db.execute(
        'SELECT COUNT(*) FROM job_vacancies WHERE is_active=1'
    ).fetchone()[0]
    total_employers = db.execute(
        'SELECT COUNT(*) FROM employers WHERE is_approved=1'
    ).fetchone()[0]
    total_recs = db.execute(
        'SELECT COUNT(*) FROM recommendations'
    ).fetchone()[0]
    total_referrals = db.execute(
        'SELECT COUNT(*) FROM referrals'
    ).fetchone()[0]
    pending_employers = db.execute(
        'SELECT COUNT(*) FROM employers WHERE is_approved=0'
    ).fetchone()[0]
    last_login_row = db.execute(
        "SELECT timestamp FROM login_logs "
        "WHERE user_id=? AND outcome='success' "
        "ORDER BY timestamp DESC LIMIT 1 OFFSET 1",
        (session['user_id'],)
    ).fetchone()
    last_login = last_login_row['timestamp'] if last_login_row else None
    recent_applicants = db.execute(
        'SELECT id, first_name, last_name, preferred_position, created_at '
        'FROM applicants WHERE is_archived=0 '
        'ORDER BY created_at DESC, id DESC LIMIT 5'
    ).fetchall()
    recent_referrals_rows = db.execute('''
        SELECT r.referred_at, r.status,
               a.first_name, a.last_name,
               jv.job_title, jv.employer_name
        FROM referrals r
        JOIN applicants a ON r.applicant_id=a.id
        JOIN job_vacancies jv ON r.vacancy_id=jv.id
        ORDER BY r.referred_at DESC LIMIT 5
    ''').fetchall()
    recent_recs = db.execute('''
        SELECT a.first_name, a.last_name,
               jv.job_title, jv.employer_name,
               rec.suitability_score
        FROM recommendations rec
        JOIN applicants a     ON rec.applicant_id = a.id
        JOIN job_vacancies jv ON rec.vacancy_id   = jv.id
        ORDER BY rec.recommended_at DESC, rec.id DESC LIMIT 5
    ''').fetchall()
    return render_template('home.html',
                           total_applicants=total_applicants,
                           active_vacancies=active_vacancies,
                           total_employers=total_employers,
                           total_recs=total_recs,
                           total_referrals=total_referrals,
                           pending_employers=pending_employers,
                           last_login=last_login,
                           recent_applicants=recent_applicants,
                           recent_referrals_rows=recent_referrals_rows,
                           recent_recs=recent_recs)

# ── ANALYTICS ─────────────────────────────────────────────────────────────────
@app.route('/analytics')
@admin_required
def analytics():
    return render_template('analytics.html')

@app.route('/api/analytics')
@admin_required
def api_analytics():
    db = get_db()
    date_from = request.args.get('date_from', '').strip()
    date_to   = request.args.get('date_to', '').strip()
    dp = []
    df_sql = ''
    if date_from:
        df_sql += ' AND date(created_at) >= ?'
        dp.append(date_from)
    if date_to:
        df_sql += ' AND date(created_at) <= ?'
        dp.append(date_to)

    total = db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0{df_sql}', dp).fetchone()[0]
    male  = db.execute(f"SELECT COUNT(*) FROM applicants WHERE is_archived=0{df_sql} AND sex='Male'", dp).fetchone()[0]
    fem   = db.execute(f"SELECT COUNT(*) FROM applicants WHERE is_archived=0{df_sql} AND sex='Female'", dp).fetchone()[0]
    youth = db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0{df_sql} AND age BETWEEN {YOUTH_AGE_MIN} AND {YOUTH_AGE_MAX}', dp).fetchone()[0]
    senior= db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0{df_sql} AND age >= {SENIOR_AGE_MIN}', dp).fetchone()[0]
    pwd   = db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0{df_sql} AND is_pwd=1', dp).fetchone()[0]

    educ_rows = db.execute(
        f"SELECT educ_level, COUNT(*) c FROM applicants WHERE is_archived=0{df_sql} AND educ_level != '' "
        'GROUP BY educ_level ORDER BY c DESC', dp
    ).fetchall()
    emp_rows = db.execute(
        f'SELECT employment_status, COUNT(*) c FROM applicants WHERE is_archived=0{df_sql} '
        'GROUP BY employment_status', dp
    ).fetchall()
    d1_rows = db.execute(
        f"SELECT barangay, COUNT(*) c FROM applicants "
        f"WHERE is_archived=0{df_sql} AND district='District 1' AND barangay!='' "
        "GROUP BY barangay ORDER BY c DESC", dp
    ).fetchall()
    d2_rows = db.execute(
        f"SELECT barangay, COUNT(*) c FROM applicants "
        f"WHERE is_archived=0{df_sql} AND district='District 2' AND barangay!='' "
        "GROUP BY barangay ORDER BY c DESC", dp
    ).fetchall()

    return jsonify({
        'jobseekers': {
            'total': total, 'male': male, 'female': fem,
            'youth': youth, 'senior': senior, 'pwd': pwd,
            'educ_labels':  [r['educ_level'] for r in educ_rows],
            'educ_values':  [r['c'] for r in educ_rows],
            'emp_labels':   [r['employment_status'] for r in emp_rows],
            'emp_values':   [r['c'] for r in emp_rows],
            'd1_labels':    [r['barangay'] for r in d1_rows],
            'd1_values':    [r['c'] for r in d1_rows],
            'd2_labels':    [r['barangay'] for r in d2_rows],
            'd2_values':    [r['c'] for r in d2_rows],
        }
    })

# ── APPLICANTS ────────────────────────────────────────────────────────────────
@app.route('/applicants')
@admin_required
def applicants_list():
    db = get_db()
    search    = request.args.get('search', '').strip()
    status    = request.args.get('status', 'all')
    district  = request.args.get('district', '')
    view      = request.args.get('view', 'card')
    page      = max(1, request.args.get('page', 1, type=int) or 1)
    per_page  = APPLICANTS_PER_PAGE

    where  = ['is_archived=0']
    params = []
    if search:
        where.append('(first_name LIKE ? OR last_name LIKE ? OR preferred_position LIKE ? OR skills LIKE ?)')
        like = f'%{search}%'
        params += [like, like, like, like]
    if status == 'incomplete':
        where.append("(skills='' OR educ_level='' OR preferred_position='')")
    elif status == 'employed':
        where.append("employment_status='Employed'")
    elif status == 'unemployed':
        where.append("employment_status='Unemployed'")
    if district in ('District 1', 'District 2'):
        where.append('district=?')
        params.append(district)
    where_sql = ' AND '.join(where)

    total  = db.execute(f'SELECT COUNT(*) FROM applicants WHERE {where_sql}', params).fetchone()[0]
    pages  = max(1, (total + per_page - 1) // per_page)
    page   = min(page, pages)
    offset = (page - 1) * per_page
    applicants = db.execute(
        f'SELECT * FROM applicants WHERE {where_sql} ORDER BY last_name, first_name LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()

    return render_template('applicants/list.html', applicants=applicants,
                           search=search, status=status,
                           district=district, view=view, page=page, pages=pages,
                           total=total)

@app.route('/applicants/<int:aid>')
@admin_required
def applicant_view(aid):
    ap = get_db().execute('''
        SELECT a.*, u.email
        FROM applicants a LEFT JOIN users u ON a.user_id = u.id
        WHERE a.id = ?
    ''', (aid,)).fetchone()
    if not ap:
        flash('Applicant not found.', 'danger')
        return redirect(url_for('applicants_list'))
    ap_d = dict(ap)
    for jcol in ('languages', 'education', 'trainings', 'eligibilities',
                 'work_history', 'other_skills', 'disability'):
        try:
            ap_d[jcol] = json.loads(ap_d.get(jcol) or '[]')
        except (ValueError, TypeError):
            ap_d[jcol] = []
    return render_template('applicants/view.html', ap=ap_d,
                           total_exp_months=_total_exp_months(ap))

@app.route('/applicants/<int:aid>/delete', methods=['POST'])
@admin_required
def applicant_delete(aid):
    db = get_db()
    ap = db.execute('SELECT first_name, last_name, user_id FROM applicants WHERE id=?', (aid,)).fetchone()
    if not ap:
        flash('Applicant not found.', 'danger')
        return redirect(url_for('applicants_list'))
    db.execute('DELETE FROM recommendations WHERE applicant_id=?', (aid,))
    db.execute('DELETE FROM referrals WHERE applicant_id=?', (aid,))
    db.execute('DELETE FROM applicants WHERE id=?', (aid,))
    # Remove the linked jobseeker login account, if any, so no orphan user remains
    if ap['user_id']:
        db.execute('DELETE FROM login_logs WHERE user_id=?', (ap['user_id'],))
        db.execute("DELETE FROM users WHERE id=? AND role='jobseeker'", (ap['user_id'],))
    db.commit()
    flash(f'Applicant {ap["first_name"]} {ap["last_name"]} has been permanently deleted.', 'success')
    return redirect(url_for('applicants_list'))

# ── REFERRALS (admin) ─────────────────────────────────────────────────────────
@app.route('/referrals')
@admin_required
def referrals_list():
    db     = get_db()
    status = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    conds, params = [], []
    if status != 'all':
        conds.append('r.status=?')
        params.append(status)
    if search:
        conds.append('(a.first_name LIKE ? OR a.last_name LIKE ? OR jv.job_title LIKE ?)')
        like = f'%{search}%'
        params += [like, like, like]
    where = ('WHERE ' + ' AND '.join(conds)) if conds else ''
    joins = ('FROM referrals r JOIN applicants a ON r.applicant_id=a.id '
             'JOIN job_vacancies jv ON r.vacancy_id=jv.id')
    total = db.execute(f'SELECT COUNT(*) {joins} {where}', params).fetchone()[0]
    page  = max(1, request.args.get('page', 1, type=int))
    pages = max(1, (total + LIST_PER_PAGE - 1) // LIST_PER_PAGE)
    page  = min(page, pages)
    referrals = db.execute(f'''
        SELECT r.*,
               a.first_name, a.last_name,
               jv.job_title, jv.employer_name, jv.occupational_category,
               u.full_name as referred_by_name
        {joins}
        LEFT JOIN users u     ON r.referred_by  = u.id
        {where}
        ORDER BY r.referred_at DESC
        LIMIT ? OFFSET ?
    ''', params + [LIST_PER_PAGE, (page - 1) * LIST_PER_PAGE]).fetchall()
    return render_template('admin/referrals.html', referrals=referrals,
                           status=status, search=search,
                           page=page, pages=pages, total=total)

@app.route('/referrals/<int:rid>/slip')
@login_required
def referral_slip(rid):
    db = get_db()
    r = db.execute('''
        SELECT r.*, a.first_name, a.last_name, a.sex, a.age, a.barangay,
               a.contact_number, a.educ_level, a.preferred_position, a.user_id AS applicant_user_id,
               jv.job_title, jv.employer_name, jv.occupational_category, jv.employer_id,
               jv.created_at AS posted_at, jv.application_deadline, jv.req_gender, jv.req_age_min,
               jv.req_age_max, jv.req_education, jv.req_experience_months, jv.req_documents,
               u.full_name AS accepted_by_name,
               e.contact_person AS e_contact, e.company_name AS e_company
        FROM referrals r
        JOIN applicants a     ON r.applicant_id = a.id
        JOIN job_vacancies jv ON r.vacancy_id   = jv.id
        JOIN users u          ON r.referred_by  = u.id
        LEFT JOIN employers e ON e.user_id       = jv.employer_id
        WHERE r.id=?
    ''', (rid,)).fetchone()
    role = session.get('role')
    allowed = bool(r) and (
        role == ROLE_ADMIN
        # Jobseekers can't view a slip once they've withdrawn the application
        or (role == ROLE_JOBSEEKER and r['applicant_user_id'] == session['user_id']
            and r['status'] != 'cancelled')
        or (role == ROLE_EMPLOYER and r['employer_id'] == session['user_id'])
    )
    if not allowed:
        flash('Referral slip not found.', 'danger')
        return redirect(_role_home())
    back_url = {
        ROLE_JOBSEEKER: url_for('jobseeker_referrals'),
        ROLE_EMPLOYER:  url_for('employer_referred'),
    }.get(role, url_for('referrals_list'))
    return render_template('referral_slip.html', r=r, back_url=back_url)

# ── VACANCIES ─────────────────────────────────────────────────────────────────
@app.route('/vacancies')
@admin_required
def vacancies_list():
    db     = get_db()
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'active')
    conds, params = [], []
    if status == 'active':
        conds.append('is_active=1')
    elif status == 'inactive':
        conds.append('is_active=0')
    if search:
        conds.append('(employer_name LIKE ? OR job_title LIKE ?)')
        like = f'%{search}%'
        params += [like, like]
    where = (' WHERE ' + ' AND '.join(conds)) if conds else ''
    total = db.execute(f'SELECT COUNT(*) FROM job_vacancies{where}', params).fetchone()[0]
    page  = max(1, request.args.get('page', 1, type=int))
    pages = max(1, (total + LIST_PER_PAGE - 1) // LIST_PER_PAGE)
    page  = min(page, pages)
    vacancies = db.execute(
        f'SELECT *, {EXPIRED_SQL} AS expired FROM job_vacancies{where} '
        'ORDER BY created_at DESC LIMIT ? OFFSET ?',
        params + [LIST_PER_PAGE, (page - 1) * LIST_PER_PAGE]
    ).fetchall()
    view = request.args.get('view', 'card')
    return render_template('vacancies/list.html', vacancies=vacancies,
                           search=search, status=status, view=view,
                           page=page, pages=pages, total=total)

@app.route('/vacancies/<int:vid>/toggle', methods=['POST'])
@admin_required
def vacancy_toggle(vid):
    db = get_db()
    v  = db.execute('SELECT is_active FROM job_vacancies WHERE id=?', (vid,)).fetchone()
    if v:
        db.execute('UPDATE job_vacancies SET is_active=? WHERE id=?',
                   (0 if v['is_active'] else 1, vid))
        db.commit()
        flash('Vacancy status updated.', 'success')
    return redirect(url_for('vacancies_list'))

@app.route('/vacancies/<int:vid>/delete', methods=['POST'])
@admin_required
def vacancy_delete(vid):
    db = get_db()
    v  = db.execute('SELECT job_title, employer_name FROM job_vacancies WHERE id=?', (vid,)).fetchone()
    if not v:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('vacancies_list'))
    db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM referrals WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE id=?', (vid,))
    db.commit()
    flash(f'Vacancy "{v["job_title"]}" ({v["employer_name"]}) has been permanently deleted.', 'success')
    return redirect(url_for('vacancies_list'))

# ── USERS ─────────────────────────────────────────────────────────────────────
@app.route('/users')
@admin_required
def users_list():
    view = request.args.get('view', 'card')
    users = get_db().execute(
        "SELECT * FROM users WHERE role='admin' ORDER BY full_name"
    ).fetchall()
    return render_template('users/list.html', users=users, view=view)

@app.route('/users/add', methods=['GET', 'POST'])
@admin_required
def user_add():
    if request.method == 'POST':
        f    = request.form
        name = f.get('full_name','').strip()
        mail = f.get('email','').strip()
        pw   = f.get('password','')
        conf = f.get('confirm_password','')
        errs = []
        if not all([name, mail, pw]):
            errs.append('All fields are required.')
        if mail and not EMAIL_RE.match(mail):
            errs.append('Please enter a valid email address.')
        if pw != conf:
            errs.append('Passwords do not match.')
        if len(pw) < 8:
            errs.append('Password must be at least 8 characters.')
        if errs:
            for e in errs:
                flash(e, 'danger')
        else:
            try:
                get_db().execute(
                    'INSERT INTO users (full_name,email,password_hash,role) VALUES (?,?,?,?)',
                    (name, mail, generate_password_hash(pw), ROLE_ADMIN)
                )
                get_db().commit()
                flash('User account created.', 'success')
                return redirect(url_for('users_list'))
            except sqlite3.IntegrityError:
                flash('That email is already registered.', 'danger')
        # Preserve what was typed so an error doesn't blank the form
        return render_template('users/form.html',
                               user={'full_name': f.get('full_name',''), 'email': f.get('email','')},
                               action='add')
    return render_template('users/form.html', user=None, action='add')

@app.route('/users/<int:uid>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(uid):
    db = get_db()
    u  = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        flash('User not found.', 'danger')
        return redirect(url_for('users_list'))
    if request.method == 'POST':
        f        = request.form
        name     = f.get('full_name','').strip()
        mail     = f.get('email','').strip()
        pw       = f.get('new_password','')
        new_role = f.get('role', u['role'])
        # Prevent removing the last admin
        if u['role'] == ROLE_ADMIN and new_role != ROLE_ADMIN:
            admin_count = get_db().execute(
                "SELECT COUNT(*) FROM users WHERE role='admin'"
            ).fetchone()[0]
            if admin_count <= 1:
                flash('Cannot remove admin role — at least one admin must exist.', 'danger')
                return render_template('users/form.html', user=dict(u), action='edit')
        try:
            if pw:
                if len(pw) < 8:
                    flash('Password must be at least 8 characters.', 'danger')
                    return render_template('users/form.html', user=dict(u), action='edit')
                db.execute('UPDATE users SET full_name=?,email=?,password_hash=?,role=? WHERE id=?',
                           (name, mail, generate_password_hash(pw), new_role, uid))
            else:
                db.execute('UPDATE users SET full_name=?,email=?,role=? WHERE id=?',
                           (name, mail, new_role, uid))
            db.commit()
            flash('User updated.', 'success')
            return redirect(url_for('users_list'))
        except sqlite3.IntegrityError:
            flash('That email is already registered.', 'danger')
    return render_template('users/form.html', user=dict(u), action='edit')

@app.route('/users/<int:uid>/delete', methods=['POST'])
@admin_required
def user_delete(uid):
    if uid == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users_list'))
    db = get_db()
    u  = db.execute('SELECT full_name, email FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        flash('User not found.', 'danger')
        return redirect(url_for('users_list'))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute('DELETE FROM users WHERE id=?', (uid,))
    db.commit()
    flash(f'Account for {u["full_name"]} ({u["email"]}) has been permanently deleted.', 'success')
    return redirect(url_for('users_list'))


@app.route('/users/login-history')
@admin_required
def login_history():
    logs = get_db().execute(
        'SELECT ll.*, u.full_name FROM login_logs ll '
        'LEFT JOIN users u ON ll.user_id=u.id '
        'ORDER BY ll.timestamp DESC LIMIT 200'
    ).fetchall()
    return render_template('users/login_history.html', logs=logs)

# ── ADMIN — EMPLOYER APPROVALS ────────────────────────────────────────────────
@app.route('/admin/employers')
@admin_required
def admin_employers():
    db     = get_db()
    status = request.args.get('status', 'pending')
    if status == 'pending':
        rows = db.execute(
            'SELECT e.*, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.id '
            'WHERE e.is_approved=0 AND e.approval_requested=1 ORDER BY e.created_at DESC'
        ).fetchall()
    elif status == 'approved':
        rows = db.execute(
            'SELECT e.*, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.id '
            'WHERE e.is_approved=1 ORDER BY e.created_at DESC'
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT e.*, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.id '
            'ORDER BY e.created_at DESC'
        ).fetchall()
    pending_count = db.execute(
        'SELECT COUNT(*) FROM employers WHERE is_approved=0 AND approval_requested=1'
    ).fetchone()[0]
    return render_template('admin/employers.html', employers=rows,
                           status=status, pending_count=pending_count)

@app.route('/admin/employers/<int:eid>/approve', methods=['POST'])
@admin_required
def admin_employer_approve(eid):
    db  = get_db()
    emp = db.execute('SELECT * FROM employers WHERE id=?', (eid,)).fetchone()
    if not emp:
        flash('Employer not found.', 'danger')
        return redirect(url_for('admin_employers'))
    if not emp['profile_completed']:
        flash('Cannot approve — this employer has not completed their company profile yet.', 'warning')
        return redirect(url_for('admin_employers'))
    db.execute('UPDATE employers SET is_approved=1 WHERE id=?', (eid,))
    db.execute('UPDATE users SET is_active=1 WHERE id=?', (emp['user_id'],))
    db.commit()
    flash(f'Employer "{emp["company_name"]}" approved. They can now post job vacancies.', 'success')
    return redirect(url_for('admin_employers'))

@app.route('/admin/employers/<int:eid>/reject', methods=['POST'])
@admin_required
def admin_employer_reject(eid):
    db  = get_db()
    emp = db.execute('SELECT * FROM employers WHERE id=?', (eid,)).fetchone()
    if not emp:
        flash('Employer not found.', 'danger')
        return redirect(url_for('admin_employers'))
    if emp['is_approved']:
        # Deactivate an already-approved employer
        db.execute('UPDATE employers SET is_approved=0, approval_requested=0 WHERE id=?', (eid,))
        db.execute('UPDATE users SET is_active=0 WHERE id=?', (emp['user_id'],))
        flash(f'Employer "{emp["company_name"]}" deactivated.', 'warning')
    else:
        # Reject a pending request — let them revise their profile and request again
        db.execute('UPDATE employers SET approval_requested=0 WHERE id=?', (eid,))
        flash(f'Approval request for "{emp["company_name"]}" rejected. '
              'They can revise their company profile and request approval again.', 'warning')
    db.commit()
    return redirect(url_for('admin_employers'))

@app.route('/admin/employers/<int:eid>/delete', methods=['POST'])
@admin_required
def admin_employer_delete(eid):
    db  = get_db()
    emp = db.execute('SELECT * FROM employers WHERE id=?', (eid,)).fetchone()
    if not emp:
        flash('Employer not found.', 'danger')
        return redirect(url_for('admin_employers'))
    uid = emp['user_id']
    # Remove the employer's vacancies and everything linked to them
    vac_ids = [r['id'] for r in db.execute(
        'SELECT id FROM job_vacancies WHERE employer_id=?', (uid,)
    ).fetchall()]
    for vid in vac_ids:
        db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
        db.execute('DELETE FROM referrals WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE employer_id=?', (uid,))
    db.execute('DELETE FROM employers WHERE id=?', (eid,))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute("DELETE FROM users WHERE id=? AND role='employer'", (uid,))
    db.commit()
    flash(f'Employer "{emp["company_name"]}" and all their postings have been permanently deleted.', 'success')
    return redirect(url_for('admin_employers'))

# ── AUTO-DEPLOY WEBHOOK (GitHub push -> git pull -> reload) ───────────────────
# Disabled unless DEPLOY_WEBHOOK_SECRET is set (only done on the hosted server).
# Optional: PESO_WSGI_FILE = path of the PythonAnywhere WSGI file to touch (reload).
@app.route('/_deploy', methods=['POST'])
def deploy_webhook():
    import hmac, hashlib, subprocess

    secret = os.environ.get('DEPLOY_WEBHOOK_SECRET', '')
    if not secret:
        return ('Not found', 404)

    body = request.get_data()
    expected = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.headers.get('X-Hub-Signature-256', '')):
        return ('Forbidden', 403)

    event = request.headers.get('X-GitHub-Event', '')
    if event == 'ping':
        return jsonify(ok=True, msg='pong')
    if event != 'push':
        return jsonify(ok=True, msg='ignored event')
    payload = request.get_json(silent=True) or {}
    if payload.get('ref') != 'refs/heads/main':
        return jsonify(ok=True, msg='ignored branch')

    repo_dir = os.path.dirname(BASE_DIR)
    try:
        result = subprocess.run(['git', 'pull', '--ff-only'], cwd=repo_dir,
                                capture_output=True, text=True, timeout=60)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500
    if result.returncode != 0:
        return jsonify(ok=False, output=(result.stdout + result.stderr)[-500:]), 500

    wsgi_file = os.environ.get('PESO_WSGI_FILE')
    if wsgi_file and os.path.exists(wsgi_file):
        os.utime(wsgi_file, None)   # touching the WSGI file reloads the app
    return jsonify(ok=True, output=result.stdout[-500:])

# ── STARTUP ───────────────────────────────────────────────────────────────────
init_db()
load_pipeline()

if __name__ == '__main__':
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("PESO CSJDM running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
