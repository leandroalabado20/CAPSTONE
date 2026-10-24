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
    make_response, Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g, send_from_directory, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── APP CONFIG ────────────────────────────────────────────────────────────────
app = Flask(__name__)
def _load_secret_key():
    """FLASK_SECRET_KEY if set; otherwise a random key saved once to instance/secret_key so logins survive restarts."""
    env = os.environ.get('FLASK_SECRET_KEY')
    if env:
        return env
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'secret_key')
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            key = fh.read().strip()
            if len(key) >= 32:
                return key
    except OSError:
        pass
    key = secrets.token_hex(32)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(key)
    except OSError:
        pass
    return key


app.secret_key = _load_secret_key()
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024      # reject oversized uploads early

# Set PESO_HTTPS=1 on an HTTPS host (e.g. PythonAnywhere); leave unset for local HTTP.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('PESO_HTTPS', '0') == '1'

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATABASE       = os.path.join(BASE_DIR, 'peso.db')
PIPELINE_PATH  = os.path.join(BASE_DIR, 'ml', 'recommendation_pipeline.pkl')
PHOTO_DIR      = os.path.join(BASE_DIR, 'uploads', 'photos')
PHOTO_MAX_BYTES = 2 * 1024 * 1024   # 2 MB
CERT_DIR       = os.path.join(BASE_DIR, 'uploads', 'certificates')
CERT_MAX_BYTES = 5 * 1024 * 1024    # 5 MB

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

ELIG_TYPES = [
    'Civil Service Eligibility',
    'Professional Regulation Commission (PRC) License',
    "Driver's License",
    'National Certificate (TESDA NC)',
]

EDUC_LEVELS = [
    'No Formal Education',
    'Elementary Level', 'Elementary Graduate',
    'High School Level', 'High School Graduate',
    'Senior High School Level', 'Senior High School Graduate',
    'Vocational', 'ALS (Alternative Learning System)',
    'College Level', 'College Undergraduate', 'College Graduate',
    "Post-Graduate (Master's / Doctorate Degree)",
]

APPLICANTS_PER_PAGE = 24
LIST_PER_PAGE = 20

MOBILE_RE = re.compile(r'^09\d{9}$')
TIN_RE    = re.compile(r'^\d{3}-\d{3}-\d{3}(-\d{3})?$')
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
    # Warehouse and Logistics
    'Warehouse Helper', 'Stock Clerk', 'Inventory Clerk', 'Forklift Operator',
    'Delivery Driver / Courier', 'Packer / Sorter', 'Logistics Coordinator',
    'Dispatcher', 'Supply Chain Officer', 'Shipping / Receiving Clerk',
    # Production and Manufacturing
    'Production Worker', 'Machine Operator', 'Quality Control Inspector',
    'Assembler', 'Welder', 'Factory Worker', 'Sewer / Seamstress',
    'Process Technician', 'Line Leader',
    # Sales / Service / Retail
    'Cashier', 'Sales Associate', 'Store Clerk', 'Customer Service Representative',
    'Barista', 'Waiter / Waitress', 'Service Crew', 'Food Service Worker',
    'Sales Representative', 'Telemarketer', 'Call Center Agent',
    'Account Executive', 'Brand Ambassador', 'Promoter',
    # Clerical and Administrative
    'Data Encoder', 'Office Clerk', 'Administrative Assistant',
    'Receptionist', 'Secretary', 'Bookkeeper', 'Payroll Clerk',
    'Billing Clerk', 'Document Controller', 'Executive Assistant',
    'Records Officer', 'Encoder / Data Analyst',
    # General Services and Security
    'Security Guard', 'Janitor / Janitress', 'Utility Worker',
    'Maintenance Staff', 'Building Attendant', 'Messengerial Staff',
    'Housekeeper', 'Caretaker', 'Groundskeeper',
    # IT / Technology
    'IT Support Technician', 'Computer Technician', 'Software Developer',
    'Web Developer', 'Graphic Designer', 'Network Administrator',
    'Data Analyst', 'Systems Analyst', 'Database Administrator',
    'Cybersecurity Analyst', 'UI/UX Designer', 'Programmer',
    'Technical Support Specialist', 'Mobile App Developer',
    # Healthcare
    'Nurse', 'Nursing Aide', 'Medical Technologist', 'Pharmacist',
    'Caregiver', 'Midwife', 'Dental Assistant', 'Radiologic Technologist',
    'Physical Therapist', 'Medical Records Clerk', 'Pharmacy Assistant',
    'Barangay Health Worker',
    # Education
    'Teacher', 'Instructor', 'Tutor', 'School Librarian',
    'Guidance Counselor', 'Teacher Aide', 'Day Care Worker',
    # Engineering
    'Civil Engineer', 'Electrical Engineer', 'Mechanical Engineer',
    'Industrial Engineer', 'Electronics Technician', 'Draftsman',
    'AutoCAD Operator', 'Project Engineer',
    # Finance / Accounting
    'Accountant', 'Auditor', 'Financial Analyst', 'Accounting Clerk',
    'Credit Investigator', 'Bank Teller', 'Insurance Agent',
    'Tax Compliance Officer', 'Accounts Payable Clerk',
    # Construction / Trades
    'Carpenter', 'Electrician', 'Plumber', 'Mason', 'Painter',
    'HVAC Technician', 'Tile Setter', 'Steel Fabricator',
    # Marketing / Creative
    'Marketing Officer', 'Social Media Manager', 'Content Writer',
    'Photographer', 'Videographer', 'Copywriter', 'Digital Marketing Specialist',
    # HR / Management
    'HR Officer', 'Recruitment Specialist', 'Training Officer',
    'Operations Supervisor', 'Team Leader', 'Branch Manager',
    'HR Assistant', 'Labor Relations Officer',
    # Hospitality / Tourism
    'Front Desk Officer', 'Hotel Receptionist', 'Event Coordinator',
    'Cook', 'Chef', 'Tour Guide', 'Housekeeping Attendant',
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

ALL_SKILLS_AC = sorted(set(SKILLS_LIST + [
    # Office / Admin
    'Microsoft Excel', 'Microsoft Word', 'Microsoft PowerPoint', 'Google Workspace',
    'Data Entry', 'Typing', 'Encoding', 'Records Management', 'Payroll Processing',
    'Scheduling', 'Email Correspondence', 'Office Administration',
    # IT / Technical
    'Programming', 'Web Development', 'HTML / CSS', 'JavaScript', 'Python',
    'Java', 'PHP', 'SQL', 'Database Management', 'Networking',
    'Graphic Design', 'Adobe Photoshop', 'Adobe Illustrator', 'Video Editing',
    'AutoCAD', 'Technical Support', 'Hardware Troubleshooting',
    'Software Installation', 'Cybersecurity', 'Social Media Management',
    # Sales / Marketing
    'Telemarketing', 'Account Management', 'Lead Generation',
    'Digital Marketing', 'Content Writing', 'Copywriting',
    'Product Demonstration', 'Negotiation',
    # Finance
    'Accounting', 'Auditing', 'Taxation', 'Financial Reporting',
    'Accounts Payable', 'Accounts Receivable', 'Bank Reconciliation',
    'Credit Analysis', 'Petty Cash Management',
    # Healthcare / Caregiving
    'Patient Care', 'Caregiving', 'First Aid', 'CPR',
    'Medical Transcription', 'Phlebotomy', 'Vital Signs Monitoring',
    # Trades / Manual
    'Carpentry', 'Electrical Works', 'Plumbing', 'Masonry',
    'Painting', 'HVAC', 'Tile Setting', 'Steel Fabrication',
    'Sewing / Dressmaking', 'Auto Mechanics',
    # Soft Skills
    'Leadership', 'Problem Solving', 'Critical Thinking',
    'Adaptability', 'Multitasking', 'Attention to Detail',
    'Customer Relations', 'Conflict Resolution', 'Report Writing',
    # From OTHER_SKILLS_CHOICES
    'Auto Mechanic', 'Beautician', 'Carpentry Work', 'Computer Literate',
    'Domestic Chores', 'Gardening', 'Electrician Work', 'Embroidery',
    'Masonry Work', 'Photography', 'Tailoring', 'Stenography',
]))

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


def barangay_to_district(raw, city=''):
    """District 1/2 exists only for City of San Jose del Monte; barangay names such as
    'Poblacion' repeat in other cities, so any other city gets no district."""
    if 'san jose del monte' not in str(city).lower():
        return ''
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
        q += ' AND applicant_id != ?'
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
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    DEFAULT 'admin',
            is_active     INTEGER DEFAULT 1,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS applicants (
            applicant_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
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
            user_id            INTEGER  REFERENCES users(user_id),
            created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_archived        INTEGER  DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS job_vacancies (
            vacancy_id            INTEGER  PRIMARY KEY AUTOINCREMENT,
            employer_name         TEXT     NOT NULL,
            job_title             TEXT     NOT NULL,
            occupational_category TEXT     NOT NULL,
            is_local              INTEGER  DEFAULT 1,
            is_active             INTEGER  DEFAULT 1,
            employer_id           INTEGER  REFERENCES users(user_id),
            created_at            DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS employers (
            employer_id    INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER  UNIQUE NOT NULL,
            company_name   TEXT     NOT NULL,
            contact_person TEXT     NOT NULL,
            phone          TEXT,
            address        TEXT,
            is_approved    INTEGER  DEFAULT 0,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id INTEGER  PRIMARY KEY AUTOINCREMENT,
            applicant_id     INTEGER  NOT NULL,
            vacancy_id       INTEGER  NOT NULL,
            suitability_score REAL    NOT NULL,
            rank             INTEGER,
            recommended_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            generated_by     INTEGER,
            status           TEXT     DEFAULT 'pending',
            FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id),
            FOREIGN KEY (vacancy_id)   REFERENCES job_vacancies(vacancy_id),
            FOREIGN KEY (generated_by) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id  INTEGER  PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER  NOT NULL,
            vacancy_id   INTEGER  NOT NULL,
            referred_by  INTEGER  NOT NULL,
            referred_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            status       TEXT     DEFAULT 'referred',
            suitability_score REAL,
            notes        TEXT,
            FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id),
            FOREIGN KEY (vacancy_id)   REFERENCES job_vacancies(vacancy_id),
            FOREIGN KEY (referred_by)  REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS login_logs (
            log_id     INTEGER  PRIMARY KEY AUTOINCREMENT,
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
                applicant_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
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
                user_id            INTEGER  REFERENCES users(user_id),
                created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_archived        INTEGER  DEFAULT 0
            );
            INSERT INTO applicants_new
                (applicant_id, first_name, last_name, sex, barangay, district,
                 employment_status, is_pwd, educ_level, preferred_position,
                 skills, work_experience, created_at, is_archived)
            SELECT applicant_id, first_name, last_name, sex, barangay, district,
                 employment_status, is_pwd, educ_level, preferred_position,
                 skills, work_experience, created_at, is_archived
            FROM applicants;
            DROP TABLE applicants;
            ALTER TABLE applicants_new RENAME TO applicants;
        ''')

    # ── Column-level migrations ────────────────────────────────────────────────
    acols = [r[1] for r in db.execute("PRAGMA table_info(applicants)").fetchall()]
    if 'user_id' not in acols:
        db.execute('ALTER TABLE applicants ADD COLUMN user_id INTEGER REFERENCES users(user_id)')
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
        ('photo', 'TEXT'),
    ]:
        if col not in acols:
            db.execute(f'ALTER TABLE applicants ADD COLUMN {col} {ddl}')

    vcols = [r[1] for r in db.execute("PRAGMA table_info(job_vacancies)").fetchall()]
    if 'employer_id' not in vcols:
        db.execute('ALTER TABLE job_vacancies ADD COLUMN employer_id INTEGER REFERENCES users(user_id)')
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
        ('requirements_deadline', 'DATE'),
        ('interview_date',       'DATE'),
        ('interview_time',       'TEXT'),
        ('interview_date_end',   'DATE'),
        ('interview_time_end',   'TEXT'),
        ('location_type',        'TEXT'),
        ('venue_address',        'TEXT'),
        ('max_applicants',       'INTEGER'),
    ]:
        if col not in vcols:
            db.execute(f'ALTER TABLE job_vacancies ADD COLUMN {col} {ddl}')
    db.execute("UPDATE job_vacancies SET location_type = CASE WHEN is_local=1 THEN 'local' ELSE 'ph' END WHERE location_type IS NULL OR location_type=''")
    # Drop obsolete free-text requirement columns (replaced by matchable fields)
    for dead in ('req_physical', 'req_experience', 'req_other'):
        if dead in vcols:
            try:
                db.execute(f'ALTER TABLE job_vacancies DROP COLUMN {dead}')
            except sqlite3.OperationalError:
                pass  # older SQLite without DROP COLUMN support — harmless to keep

    # An applicant may now hold several active referrals (capped in app code by
    # MAX_ACTIVE_REFERRALS); only the same applicant+vacancy pair must stay unique.
    db.execute("DROP INDEX IF EXISTS ux_referrals_one_active")
    try:
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_referrals_applicant_vacancy ON referrals(applicant_id, vacancy_id) WHERE status != 'cancelled'")
    except sqlite3.IntegrityError:
        pass   # existing duplicate data: leave the app-level check in place
    rcols = [r[1] for r in db.execute("PRAGMA table_info(referrals)").fetchall()]
    if 'suitability_score' not in rcols:
        db.execute('ALTER TABLE referrals ADD COLUMN suitability_score REAL')
    if 'reject_reason' not in rcols:
        db.execute('ALTER TABLE referrals ADD COLUMN reject_reason TEXT')
    db.execute('''CREATE TABLE IF NOT EXISTS notifications (
        notif_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        title      TEXT    NOT NULL,
        message    TEXT    NOT NULL,
        link       TEXT,
        is_read    INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')
    db.execute('CREATE INDEX IF NOT EXISTS ix_notifications_user ON notifications(user_id, is_read, notif_id)')

    reccols = [r[1] for r in db.execute("PRAGMA table_info(recommendations)").fetchall()]
    for col, ddl in [('generated_by', 'INTEGER'), ('status', "TEXT DEFAULT 'pending'")]:
        if col not in reccols:
            db.execute(f'ALTER TABLE recommendations ADD COLUMN {col} {ddl}')

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
                user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name     TEXT    NOT NULL,
                email         TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                role          TEXT    DEFAULT 'admin',
                is_active     INTEGER DEFAULT 1,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users_new (user_id, full_name, email, password_hash, role, is_active, created_at)
                SELECT user_id, full_name, email, password_hash, role, is_active, created_at FROM users;
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
            first = db.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 1").fetchone()
            if first:
                db.execute("UPDATE users SET role='admin' WHERE user_id=?", (first['user_id'],))

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
    'College Level': 7, 'College Undergraduate': 8, 'College Graduate': 9,
    "Post-Graduate (Master's / Doctorate Degree)": 10,
}
REQ_EDUC_CHOICES = EDUC_LEVELS     # employers pick from the same list jobseekers use

def edu_req_text(level):
    """'High School Graduate or higher' for rankable levels; Vocational / ALS / No Formal Education are shown as-is."""
    return f'{level} or higher' if level in EDUC_RANK else (level or '')

app.jinja_env.globals['edu_req_text'] = edu_req_text

def _g(v, key):
    try:
        return v[key]
    except (KeyError, IndexError, TypeError):
        return None

# ── Job location type (Local / Elsewhere in the Philippines / Overseas) ───────────────────
LOCATION_TYPES_V = {
    'local':    {'label': 'Local (CSJDM)',  'short': 'Local',        'css': 'bg-success-subtle text-success-emphasis'},
    'ph':       {'label': 'Outside CSJDM',  'short': 'Outside CSJDM', 'css': 'bg-info-subtle text-info-emphasis'},
    'overseas': {'label': 'Overseas',       'short': 'Overseas',     'css': 'bg-warning-subtle text-warning-emphasis'},
}

def loc_type(v):
    t = _g(v, 'location_type')
    if t in LOCATION_TYPES_V:
        return t
    return 'local' if _g(v, 'is_local') else 'ph'

def loc_info(v):
    return {'type': loc_type(v), **LOCATION_TYPES_V[loc_type(v)]}

app.jinja_env.globals['loc_info'] = loc_info

_OVERSEAS_WORDS = [
    'uae', 'united arab emirates', 'dubai', 'abu dhabi', 'sharjah', 'saudi', 'riyadh', 'jeddah', 'dammam', 'qatar', 'doha',
    'kuwait', 'bahrain', 'oman', 'muscat', 'singapore', 'japan', 'tokyo', 'osaka', 'korea', 'seoul', 'taiwan', 'taipei',
    'hong kong', 'macau', 'malaysia', 'kuala lumpur', 'brunei', 'thailand', 'vietnam', 'indonesia', 'china', 'usa', 'u s a',
    'united states', 'america', 'canada', 'australia', 'new zealand', 'united kingdom', 'uk', 'england', 'london', 'italy',
    'spain', 'germany', 'france', 'israel', 'lebanon', 'jordan', 'egypt', 'cyprus', 'greece', 'norway', 'ireland', 'overseas', 'abroad',
]
_PLACE_CACHE = {}

def _norm_place(x):
    import unicodedata
    x = unicodedata.normalize('NFKD', str(x or '')).encode('ascii', 'ignore').decode().lower()
    x = re.sub(r'\b(city of|municipality of)\b', ' ', x)
    x = re.sub(r'[^a-z0-9]+', ' ', x)
    return ' '.join(x.split())

def _place_index():
    if _PLACE_CACHE:
        return _PLACE_CACHE
    base = os.path.join(app.root_path, 'static', 'data', 'psgc')
    provinces, cities, csjdm_brgys = set(), set(), set()
    try:
        for p in json.load(open(os.path.join(base, 'provinces.json'), encoding='utf-8')):
            provinces.add(_norm_place(p['n']))
        for fn in os.listdir(base):
            if not fn.endswith('.json') or fn == 'provinces.json':
                continue
            data = json.load(open(os.path.join(base, fn), encoding='utf-8'))
            for city, brgys in data.items():
                cities.add(_norm_place(city))
                if 'san jose del monte' in _norm_place(city):
                    csjdm_brgys.update(_norm_place(b) for b in brgys)
    except (OSError, ValueError):
        pass
    cities.discard(''); provinces.discard('')
    _PLACE_CACHE.update(provinces=provinces, cities=cities, csjdm_brgys=csjdm_brgys)
    return _PLACE_CACHE

def detect_location_type(text):
    """Best-effort guess ('local' / 'ph' / 'overseas') from a free-text job location; None when unsure."""
    t = _norm_place(text)
    if not t:
        return None
    padded = f' {t} '
    has = lambda name: f' {name} ' in padded
    if any(has(w) for w in ('san jose del monte', 'sjdm', 'csjdm')):
        return 'local'
    if any(has(w) for w in _OVERSEAS_WORDS):
        return 'overseas'
    idx = _place_index()
    other_place = any(has(n) for n in idx['cities'] | idx['provinces'] if n not in ('san jose', 'del monte'))
    if any(has(b) for b in idx['csjdm_brgys']) and not other_place:
        return 'local'
    if other_place or any(has(w) for w in ('philippines', 'metro manila', 'ncr')):
        return 'ph'
    return None

def resolve_location_type(f):
    """Local / Outside CSJDM / Overseas, detected from the typed Job Location (blank = local)."""
    loc = (f.get('job_location') or '').strip()
    if not loc:
        return 'local'
    return detect_location_type(loc) or 'ph'


def auto_predict_category(job_title):
    """Predict occupational category from job title using the ML pipeline."""
    if pipeline is None:
        return 'General Services and Security'
    try:
        vec   = pipeline['vec']
        model = pipeline['model']
        idx   = int(model.predict(vec.transform([job_title.lower()]))[0])
        return CATEGORIES.get(idx, 'General Services and Security')
    except Exception:
        return 'General Services and Security'


def merge_required_skills(f):
    """Comma-separated skills typed by the employer, de-duplicated and capped at 3."""
    out, seen = [], set()
    for x in (f.get('req_skills_text') or '').split(','):
        x = ' '.join(x.split())[:40]
        if x and x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    return ','.join(out[:3]) or None


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
        'req_education':          edu if edu in EDUC_LEVELS else None,
        'req_experience_months': num('req_experience_months'),
        'req_documents':          f.get('req_documents', '').strip() or None,
        'salary_min':             num('salary_min'),
        'salary_max':             num('salary_max'),
        'salary_period':          period if period in SALARY_PERIODS else None,
        'job_location':           (f.get('job_location') or '').strip() or None,
        'req_skills':             merge_required_skills(f),
        'requirements_deadline':  (f.get('requirements_deadline') or '').strip() or None,
        'interview_date':         (f.get('interview_date') or '').strip() or None,
        'interview_time':         (f.get('interview_time') or '').strip() or None,
        'interview_date_end':     (f.get('interview_date_end') or '').strip() or None,
        'interview_time_end':     (f.get('interview_time_end') or '').strip() or None,
        'venue_address':          (f.get('venue_address') or '').strip()[:200] or None,
    }
    # Unified time range ("08:00|18:00") overrides the separate start/end fields
    rng = (f.get('interview_time_range') or '').strip()
    if '|' in rng:
        vals['interview_time'], vals['interview_time_end'] = [x.strip() or None for x in rng.split('|', 1)]
    if vals['salary_min'] and vals['salary_max'] and vals['salary_min'] > vals['salary_max']:
        return vals, 'Minimum salary cannot be greater than maximum salary.'
    if vals['req_age_min'] and vals['req_age_max'] and vals['req_age_min'] > vals['req_age_max']:
        return vals, 'Minimum age cannot be greater than maximum age.'
    if vals['application_deadline']:
        try:
            datetime.strptime(vals['application_deadline'], '%Y-%m-%d')
        except ValueError:
            return vals, 'Application deadline is not a valid date.'
    for key, label in (('requirements_deadline', 'Requirements deadline'), ('interview_date', 'Interview start date'),
                       ('interview_date_end', 'Interview end date')):
        if vals[key]:
            try:
                datetime.strptime(vals[key], '%Y-%m-%d')
            except ValueError:
                return vals, f'{label} is not a valid date.'
    for key in ('interview_time', 'interview_time_end'):
        if vals[key]:
            try:
                datetime.strptime(vals[key], '%H:%M')
            except ValueError:
                return vals, 'Interview time is not valid.'
    if not vals['interview_date']:
        # No interview period: ignore the (pre-filled) times and any end date
        vals['interview_time'] = vals['interview_time_end'] = vals['interview_date_end'] = None
    else:
        if vals['interview_date_end'] and vals['interview_date_end'] < vals['interview_date']:
            return vals, 'Interview end date cannot be before the start date.'
        if vals['interview_date_end'] == vals['interview_date']:
            vals['interview_date_end'] = None
        if vals['interview_time'] and vals['interview_time_end'] and vals['interview_time_end'] <= vals['interview_time']:
            return vals, 'Interview end time must be after the start time.'
        if not vals['venue_address']:
            return vals, 'Please enter the venue address for the interview.'
    return vals, None

REQ_COLS = ['application_deadline', 'req_gender', 'req_age_min', 'req_age_max',
            'req_education', 'req_experience_months', 'req_documents',
            'salary_min', 'salary_max', 'salary_period', 'job_location', 'req_skills',
            'requirements_deadline', 'interview_date', 'interview_time', 'interview_date_end', 'interview_time_end',
            'venue_address']

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

def interview_text(v):
    """e.g. 'Dec 22 \u2013 Dec 26, 2026 \u00b7 8:00 AM \u2013 6:00 PM' for a vacancy's interview period ('' when not set)."""
    def fmt_d(dt, year=True):
        return dt.strftime('%b %d, %Y' if year else '%b %d').replace(' 0', ' ')

    def fmt_t(x):
        return datetime.strptime(x, '%H:%M').strftime('%I:%M %p').lstrip('0')
    d1, d2 = _g(v, 'interview_date'), _g(v, 'interview_date_end')
    if not d1:
        return ''
    try:
        a1 = datetime.strptime(d1, '%Y-%m-%d')
        if d2 and d2 != d1:
            a2 = datetime.strptime(d2, '%Y-%m-%d')
            out = f"{fmt_d(a1, a1.year != a2.year)} \u2013 {fmt_d(a2)}"
        else:
            out = fmt_d(a1)
        t1, t2 = _g(v, 'interview_time'), _g(v, 'interview_time_end')
        if t1 and t2:
            out += f' \u00b7 {fmt_t(t1)} \u2013 {fmt_t(t2)}'
        elif t1:
            out += f' \u00b7 {fmt_t(t1)}'
    except ValueError:
        return ''
    return out

app.jinja_env.globals['interview_text'] = interview_text

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
        out.append(edu_req_text(_g(v, 'req_education')))
    m = _g(v, 'req_experience_months')
    if m:
        out.append(f'{m}+ mos. experience')
    req_s = _g(v, 'req_skills')
    if req_s:
        skills = [s.strip() for s in req_s.split(',') if s.strip()]
        if skills:
            out.append('Skills: ' + ', '.join(skills))
    return out

def _work_months(w):
    """Months worked for one Work Experience row, from its From/To dates (inclusive).
    The current-job flag means up to this month. Falls back to a legacy 'months' value."""
    today = datetime.now()
    cur = bool(w.get('current'))
    if cur:
        w['to_m'] = w['to_y'] = ''
    try:
        fy, fm = int(w.get('from_y')), int(w.get('from_m'))
        ty, tm = (today.year, today.month) if cur else (int(w.get('to_y')), int(w.get('to_m')))
    except (TypeError, ValueError):
        return w['months'] if str(w.get('months', '')).isdigit() else ''
    return str(max(0, (ty * 12 + tm) - (fy * 12 + fm) + 1))

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

def req_warnings(v, ap, viewer='jobseeker'):
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
            w.append("None of the required skills match the applicant's profile" if viewer == 'employer'
                     else 'None of the required skills match your profile')
    return w

def meets_hard_requirements(v, ap):
    """Mandatory education and experience. Unknown/unrankable education or no applicant -> not excluded."""
    if not ap:
        return True
    need, have = _g(v, 'req_education'), (_g(ap, 'educ_level') or '')
    if need in EDUC_RANK and have in EDUC_RANK and EDUC_RANK[have] < EDUC_RANK[need]:
        return False
    need_m = _g(v, 'req_experience_months')
    return not (need_m and _total_exp_months(ap) < need_m)

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

app.jinja_env.globals['vacancy_location'] = _vacancy_location

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
    # "Quezon City, Metro Manila" should match a vacancy located in "Quezon City"
    pref_city, loc_n = _norm_place(pref.split(',')[0]), _norm_place(loc)
    if pref_city and loc_n and (f' {pref_city} ' in f' {loc_n} '):
        return True
    if _g(v, 'is_local') and any(k in pref for k in ('san jose del monte', 'csjdm', 'sjdm')):
        return True
    return False

app.jinja_env.globals['req_summary'] = req_summary
app.jinja_env.globals['req_warnings'] = req_warnings

# Literature-backed weights for CB scoring (skills 40%, exp 25%, educ 20%, title 10%, location 5%)
# Gender and Age are constraint flags only — excluded from weighted average.
# Source: x0pa (2024), NextMantra (2026), Isinkaye et al. (2022), Yusuf et al. (2025)
#
# Vacancies scoring below this threshold are excluded from the recommendation list.
# 0.60 is a conservative high-precision threshold: ensures zero-skill mismatches
# (which floor at 0.50) are always filtered out. Only vacancies with actual
# skills or title relevance pass. Source: Isinkaye et al. (2022); PMC (2022).
# Additional rule: alternative vacancies (title_score == 0) are only shown when
# skills_score > 0 — education/age/location overlap alone is not a recommendation.
_CB_MIN_SCORE       = 0.50
_CB_TITLE_MATCH_MIN = 0.50   # minimum Jaccard title score to be a "position match"

_CB_WEIGHTS = {
    'skills':     0.45,
    'experience': 0.35,
    'education':  0.20,
}

_TITLE_STOP = {'the','a','an','of','and','for','in','at','to','or','as','is','on','by','with'}

def _token_set(text):
    """Lowercase word tokens from a free-text field, filtering common stop words."""
    return {w for w in re.split(r'[\s/\-,]+', (text or '').lower())
            if w and w not in _TITLE_STOP}

def _parse_other_skills(ap):
    """Parse other_skills — stored as a JSON array string — into a plain list."""
    raw = _g(ap, 'other_skills') or ''
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else [raw]
    except (ValueError, TypeError):
        return [s.strip() for s in raw.split(',') if s.strip()]

def _ap_skills_set(ap):
    """Skill tokens from the applicant's skills field."""
    return {s.strip().lower() for s in (_g(ap, 'skills') or '').split(',') if s.strip()}

def vacancy_content_score(v, ap):
    """Content-based match score using 3 literature-validated competency fields.
    Weights: Skills 50%, Work Experience 30%, Education 20%.
    Job title is a pre-filter (not scored). Location is a display indicator only.
    Gender and Age are hard eligibility filters (not scored).
    Returns (cb_score 0-1, filled_count, title_score, breakdown)."""
    filled = 0
    breakdown = {}
    weighted = {}

    # Gender — hard eligibility filter (not scored, tracked for display/warnings)
    req_g = _g(v, 'req_gender')
    if req_g and req_g != 'Any':
        s = 1.0 if (_g(ap, 'sex') or '') == req_g else 0.0
        breakdown['gender'] = s

    # Age — hard eligibility filter (not scored, tracked for display/warnings)
    lo, hi = _g(v, 'req_age_min'), _g(v, 'req_age_max')
    if lo or hi:
        age = _g(ap, 'age')
        s = 0.0 if age is None else (1.0 if (not lo or age >= lo) and (not hi or age <= hi) else 0.0)
        breakdown['age'] = s

    # Education — scored (weight: 20%)
    req_edu = _g(v, 'req_education')
    if req_edu:
        filled += 1
        have = (_g(ap, 'educ_level') or '')
        if req_edu in EDUC_RANK and have in EDUC_RANK:
            s = 1.0 if EDUC_RANK[have] >= EDUC_RANK[req_edu] else 0.0
        else:
            s = 1.0 if have == req_edu else 0.0
        breakdown['education'] = s
        weighted['education'] = s

    # Work experience — ratio scoring, partial credit (weight: 30%)
    req_mo = _g(v, 'req_experience_months')
    if req_mo:
        filled += 1
        have_mo = _total_exp_months(ap)
        s = 1.0 if have_mo >= req_mo else round(have_mo / req_mo, 4)
        breakdown['experience'] = s
        weighted['experience'] = s

    # Skills — Jaccard: |applicant ∩ required| / |required| (weight: 50%)
    req_s = _g(v, 'req_skills')
    if req_s:
        req_set = {sk.strip().lower() for sk in req_s.split(',') if sk.strip()}
        if req_set:
            filled += 1
            have_set = _ap_skills_set(ap)
            s = round(len(req_set & have_set) / len(req_set), 4)
            breakdown['skills'] = s
            weighted['skills'] = s

    # Job title vs preferred position — pre-filter only, not scored
    title_tok = _token_set(_g(v, 'job_title'))
    pref_tok  = _token_set(_g(ap, 'preferred_position'))
    union = title_tok | pref_tok
    title_score = round(len(title_tok & pref_tok) / len(union), 4) if union else 0.0
    breakdown['title'] = title_score

    # Location — display indicator only, not scored
    pref_local = (_g(ap, 'pref_work_local') or '').strip()
    pref_ovs   = (_g(ap, 'pref_work_overseas') or '').strip()
    if pref_local or pref_ovs:
        s = 1.0 if _location_matches(v, ap) else 0.0
        breakdown['location'] = s

    # Weighted average across the 3 competency fields only
    total_w = sum(_CB_WEIGHTS[k] for k in weighted)
    if total_w > 0:
        cb_score = round(sum(weighted[k] * _CB_WEIGHTS[k] for k in weighted) / total_w, 4)
    else:
        # No requirements set by employer — vacancy is open to anyone who passes the title filter
        cb_score = 1.0

    return cb_score, filled, title_score, breakdown


def get_recommendations(educ_level, preferred_position, skills, work_experience, vacancies,
                        applicant=None):
    """Hybrid recommender: ML category suitability (Layer 1) + content-based vacancy
    scoring (Layer 2) across 3 competency fields (Skills 50%, Experience 30%, Education 20%).
    Job title match is the primary filter — only vacancies matching preferred position are shown.
    Returns a flat list of vacancy dicts sorted by suitability_score descending."""
    if pipeline is None:
        return []
    vec   = pipeline['vectorizer']
    model = pipeline['model']
    text  = _clean_profile(educ_level, preferred_position, skills, work_experience)
    proba = model.predict_proba(vec.transform([text]))[0]
    cat_ml = {CATEGORIES[i]: round(float(proba[i]), 4) for i in range(len(CATEGORIES))}

    preferred = []   # vacancies matching the applicant's preferred position
    alternative = [] # vacancies that don't match the title but meet competency requirements

    for v in vacancies:
        ml_score = cat_ml.get(v['occupational_category'], 0.0)
        if applicant is not None:
            cb_score, filled, title_score, breakdown = vacancy_content_score(v, applicant)
        else:
            cb_score, filled, title_score, breakdown = 0.0, 0, 0.0, {}
        completeness = filled / 3
        final = round(cb_score, 4)
        is_position_match = title_score >= _CB_TITLE_MATCH_MIN

        # Hard disqualifier — gender or age mismatch: applicant cannot apply at all
        if breakdown.get('gender') == 0.0 or breakdown.get('age') == 0.0:
            continue
        # Minimum score threshold (only when vacancy has set competency requirements)
        if filled > 0 and final < _CB_MIN_SCORE:
            continue

        warns = req_warnings(v, applicant) if applicant is not None else []
        entry = {
            'vacancy_id':        v['vacancy_id'],
            'title':             v['job_title'],
            'employer':          v['employer_name'],
            'category':          v['occupational_category'],
            'icon':              CAT_ICONS.get(v['occupational_category'], 'bi-briefcase'),
            'info':              v,
            'suitability_score': final,
            'suitability_pct':   f'{final * 100:.1f}%',
            'ml_score':          ml_score,
            'cb_score':          cb_score,
            'completeness':      completeness,
            'breakdown':         breakdown,
            'warns_list':        warns,
            'req_unmet':         len(warns),
            'qualified':         len(warns) == 0,
            'hard_ok':           meets_hard_requirements(v, applicant),
            'location':          _vacancy_location(v),
            'loc_match':         _location_matches(v, applicant),
            'title_score':       title_score,
            'is_position_match': is_position_match,
            'is_alternative':    not is_position_match,
        }

        if is_position_match:
            preferred.append(entry)
        else:
            # Only include as alternative when it has at least skills overlap
            # — a vacancy that only matches on education alone is not meaningful
            if breakdown.get('skills', 0.0) > 0.0:
                alternative.append(entry)

    # Show preferred matches first; fall back to alternatives only when no preferred exist
    if preferred:
        results = preferred
    else:
        results = alternative

    results.sort(key=lambda x: -x['suitability_score'])
    return results, cat_ml

def explain_match(r, fields):
    """One-paragraph, human-readable reason for the score (rule-based, uses data already computed)."""
    bd, pct = r['breakdown'], round(r['suitability_score'] * 100)
    # title and location are pre-filter/display fields, not scored — exclude from explanation
    scored_keys = {'skills', 'experience', 'education'}
    label = {'skills': 'skills', 'experience': 'work experience', 'education': 'education'}
    band = 'Strong' if pct >= 80 else 'Moderate' if pct >= 50 else 'Low'
    strong = [label[k] for k, sc in bd.items() if sc >= 0.8 and k in scored_keys]
    weak = sorted(((k, sc) for k, sc in bd.items() if sc < 0.5 and k in scored_keys), key=lambda x: x[1])[:2]
    parts = [f'{band} match ({pct}%).']
    if r.get('is_alternative'):
        parts.append('Alternative position — does not match your preferred job title.')
    if strong:
        parts.append('Strongest fit: ' + ', '.join(strong[:3]) + '.')
    for k, sc in weak:
        f = next((x for x in fields if x['key'] == k), None)
        parts.append(f'Held back by {label[k]}' + (f' ({f["ap_val"]} vs {f["vac_val"]} required).' if f else '.'))
    return ' '.join(parts)

# ── AUTH HELPERS ──────────────────────────────────────────────────────────────
@app.before_request
def drop_stale_session():
    """If the logged-in account was deleted (or deactivated), clear the old session so the user is sent to the login page."""
    if 'user_id' in session and not (request.endpoint or '').startswith('static'):
        row = get_db().execute('SELECT is_active FROM users WHERE user_id=?', (session['user_id'],)).fetchone()
        if row is None or row['is_active'] == 0:
            session.clear()

@app.before_request
def csrf_same_origin_guard():
    """Reject cross-site form posts: a state-changing request must come from this same site.
    Browsers always send Origin (or at least Referer) on POST; SameSite=Lax cookies are the second layer."""
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        src = request.headers.get('Origin') or request.headers.get('Referer')
        if src:
            from urllib.parse import urlparse
            if urlparse(src).netloc != request.host:
                abort(403)


@app.after_request
def security_headers(resp):
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    resp.headers.setdefault('Referrer-Policy', 'same-origin')
    return resp


@app.errorhandler(413)
def too_large(_e):
    flash('That file is too large (limit 12 MB).', 'danger')
    return redirect(request.referrer or url_for('index'))


@app.errorhandler(403)
def forbidden(_e):
    flash('That request was blocked for your protection. Please try again from the page itself.', 'danger')
    return redirect(url_for('index'))


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
        return get_db().execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()
    return None

def add_notification(db, user_id, title, message, link=None):
    """Insert an in-app notification for one user (caller commits)."""
    db.execute('INSERT INTO notifications (user_id, title, message, link) VALUES (?,?,?,?)',
               (user_id, title, message, link))

@app.route('/jobseeker/notifications/<int:nid>/open')
@jobseeker_required
def jobseeker_notification_open(nid):
    db = get_db()
    row = db.execute('SELECT link FROM notifications WHERE notif_id=? AND user_id=?',
                     (nid, session['user_id'])).fetchone()
    if not row:
        return redirect(url_for('jobseeker_referrals'))
    db.execute('UPDATE notifications SET is_read=1 WHERE notif_id=?', (nid,))
    db.commit()
    return redirect(row['link'] or url_for('jobseeker_referrals'))

@app.route('/jobseeker/notifications/read-all', methods=['POST'])
@jobseeker_required
def jobseeker_notifications_read_all():
    db = get_db()
    db.execute('UPDATE notifications SET is_read=1 WHERE user_id=? AND is_read=0', (session['user_id'],))
    db.commit()
    return redirect(request.referrer or url_for('jobseeker_dashboard'))

# ── CONTEXT PROCESSOR ─────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    pending_employers_count = 0
    employer_approved = False
    user_photo = ''
    notif_unread, notif_items = 0, []
    role = session.get('role')
    if role == ROLE_ADMIN:
        try:
            pending_employers_count = get_db().execute(
                "SELECT COUNT(*) FROM employers WHERE is_approved=0 AND approval_requested=1"
            ).fetchone()[0]
        except Exception:
            pass
    elif role == ROLE_JOBSEEKER:
        try:
            row = get_db().execute(
                'SELECT photo FROM applicants WHERE user_id=?', (session.get('user_id'),)
            ).fetchone()
            user_photo = (row['photo'] if row else '') or ''
            notif_unread = get_db().execute(
                'SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0', (session.get('user_id'),)
            ).fetchone()[0]
            notif_items = get_db().execute(
                'SELECT * FROM notifications WHERE user_id=? ORDER BY notif_id DESC LIMIT 8',
                (session.get('user_id'),)
            ).fetchall()
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
        'user_photo':             user_photo,
        'notif_unread':           notif_unread,
        'notif_items':            notif_items,
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

@app.template_filter('monthyear')
def monthyear_filter(v):
    """'2026-03' -> 'March 2026'; anything else is returned unchanged."""
    try:
        return datetime.strptime(v, '%Y-%m').strftime('%B %Y')
    except (ValueError, TypeError):
        return v or ''

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

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/jobs')
def public_jobs():
    db = get_db()
    search   = request.args.get('search', '').strip()
    conds, params = [OPEN_VACANCY_SQL], []
    if search:
        conds.append('(job_title LIKE ? OR employer_name LIKE ?)')
        like = f'%{search}%'
        params += [like, like]
    vacancies = db.execute(
        f'SELECT * FROM job_vacancies WHERE {" AND ".join(conds)} ORDER BY created_at DESC',
        params
    ).fetchall()
    if session.get('role') == ROLE_JOBSEEKER:
        me = _get_my_applicant()
        if me:
            mine = {r['vacancy_id'] for r in db.execute(
                "SELECT vacancy_id FROM referrals WHERE applicant_id=? AND status != 'cancelled'",
                (me['applicant_id'],)).fetchall()}
            vacancies = [v for v in vacancies if v['vacancy_id'] in mine or meets_hard_requirements(v, me)]
    return render_template('public/jobs.html', vacancies=vacancies, search=search)

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
        WHERE jv.vacancy_id=?
    ''', (vid,)).fetchone()
    if not v or not v['is_active']:
        flash('That job is no longer available.', 'danger')
        return redirect(url_for('public_jobs'))
    is_jobseeker = session.get('role') == ROLE_JOBSEEKER
    applied, profile_ok, app_status, reject_reason = False, True, '', ''
    if is_jobseeker:
        ap = _get_my_applicant()
        if ap:
            profile_ok = bool(ap['educ_level'] and ap['preferred_position'] and ap['skills'])
            row = db.execute(
                "SELECT status, reject_reason FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status!='cancelled'",
                (ap['applicant_id'], vid)).fetchone()
            applied = bool(row)
            app_status = row['status'] if row else ''
            reject_reason = (row['reject_reason'] if row else '') or ''
    # Back link reflects where the visitor came from
    src = request.args.get('src', '')
    if is_jobseeker and src == 'rec':
        back_url, back_label = url_for('jobseeker_recommendations', generate=1), 'Back to recommendations'
    elif is_jobseeker and src == 'apps':
        back_url, back_label = url_for('jobseeker_referrals'), 'Back to my applications'
    elif is_jobseeker and src == 'jobs':
        back_url, back_label = url_for('jobseeker_jobs'), 'Back to jobs'
    else:
        back_url, back_label = url_for('public_jobs'), 'Back to all jobs'
    # Logged-in jobseekers stay inside their portal layout instead of the public one
    layout = 'base_jobseeker.html' if is_jobseeker else 'base_public.html'
    return render_template('public/job_detail.html', v=v, is_jobseeker=is_jobseeker, layout=layout,
                           logged_in=('user_id' in session), applied=applied, profile_ok=profile_ok,
                           app_status=app_status, reject_reason=reject_reason,
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
        # Throttle brute-force guessing: too many recent failures for this email or from this address
        recent_email = db.execute(
            "SELECT COUNT(*) FROM login_logs WHERE username=? AND outcome='failed' AND timestamp >= datetime('now','-15 minutes')",
            (email,)).fetchone()[0]
        recent_ip = db.execute(
            "SELECT COUNT(*) FROM login_logs WHERE ip_address=? AND outcome='failed' AND timestamp >= datetime('now','-15 minutes')",
            (ip,)).fetchone()[0]
        if recent_email >= 5 or recent_ip >= 20:
            flash('Too many failed sign-in attempts. Please wait 15 minutes and try again.', 'danger')
            return render_template('login.html'), 429
        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                           (user['user_id'], log_name, ip, 'denied_inactive'))
                db.commit()
                flash('Your account is deactivated. Contact an administrator.', 'danger')
            else:
                session.clear()
                session['user_id']   = user['user_id']
                session['full_name'] = user['full_name']
                session['role']      = user['role'] or ROLE_ADMIN
                db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                           (user['user_id'], log_name, ip, 'success'))
                db.commit()
                # Employer must be approved before accessing portal
                if session['role'] == ROLE_EMPLOYER:
                    emp = db.execute('SELECT is_approved FROM employers WHERE user_id=?',
                                     (user['user_id'],)).fetchone()
                    if not emp or not emp['is_approved']:
                        return redirect(url_for('employer_profile'))
                return redirect(_role_home())
        else:
            uid = user['user_id'] if user else None
            db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                       (uid, log_name, ip, 'failed'))
            db.commit()
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

# ── CACHE / BACK-BUTTON PROTECTION ────────────────────────────────────────────
@app.after_request
def no_cache_private_pages(resp):
    """Never let the browser cache app pages, so Back after logout can't show an old private page."""
    if request.endpoint != 'static':
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    return resp

@app.route('/api/session/check')
def session_check():
    """Used by the page guard when a page is shown from history (Back/Forward)."""
    return ('', 204) if 'user_id' in session else ('', 401)

@app.route('/logout')
def logout():
    session.clear()
    resp = redirect(url_for('index'))
    resp.headers['Clear-Site-Data'] = '"cache", "storage"'   # drop cached pages + session/local storage (drafts)
    return resp

def _registration_conflicts(email, first, last):
    """Field errors for a new account: email already used / same first+last name already registered.
    Comparisons are case-insensitive and ignore extra spaces."""
    errs = {}
    db = get_db()
    if email and db.execute('SELECT 1 FROM users WHERE lower(email) = lower(?)', (email,)).fetchone():
        errs['email'] = 'This email address is already registered.'
    if first and last:
        full = f'{first} {last}'.lower()
        rows = db.execute('SELECT full_name FROM users').fetchall()
        if any(' '.join((r['full_name'] or '').split()).lower() == full for r in rows):
            errs['name'] = 'An account with this name already exists.'
    return errs

@app.route('/api/register/check')
def register_check():
    """Live duplicate check used by the signup form (before the final submit)."""
    a = request.args
    first = ' '.join(a.get('first_name', '').split())
    last  = ' '.join(a.get('last_name', '').split())
    return jsonify(_registration_conflicts(a.get('email', '').strip(), first, last))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(_role_home())
    role = request.values.get('role', '')
    if request.method == 'POST':
        f         = request.form
        first     = ' '.join(f.get('first_name', '').split())
        last      = ' '.join(f.get('last_name', '').split())
        full_name = f'{first} {last}'.strip()
        email     = f.get('email', '').strip()
        confirm   = f.get('confirm_email', '').strip()
        pw        = f.get('password', '')
        role      = f.get('role', '').strip()

        errs = []
        if not all([first, last, email, pw]):
            errs.append('All required fields must be filled.')
        if role not in (ROLE_JOBSEEKER, ROLE_EMPLOYER):
            errs.append('Please choose whether you are a jobseeker or an employer.')
        if email and not EMAIL_RE.match(email):
            errs.append('Please enter a valid email address.')
        if email.lower() != confirm.lower():
            errs.append('Email addresses do not match.')
        if len(pw) < 8:
            errs.append('Password must be at least 8 characters.')
        field_errs = _registration_conflicts(email, first, last)
        if errs or field_errs:
            for e in errs:
                flash(e, 'danger')
            return render_template('auth/signup.html', form=f, role=role, errors=field_errs)
        db = get_db()
        try:
            cur = db.execute(
                'INSERT INTO users (full_name, email, password_hash, role) VALUES (?,?,?,?)',
                (full_name, email, generate_password_hash(pw), role)
            )
            uid = cur.lastrowid
            if role == ROLE_JOBSEEKER:
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
            return render_template('auth/signup.html', form=f, role=role,
                                   errors={'email': 'This email address is already registered.'})
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
            get_db().execute('UPDATE users SET password_hash = ? WHERE user_id = ?',
                             (generate_password_hash(new), user['user_id']))
            get_db().commit()
            flash('Password changed successfully.', 'success')
            return redirect(_role_home())
    return render_template('settings/password.html', user=user,
                           layout=layout, cancel_url=cancel_url)

# ── JOBSEEKER PORTAL ──────────────────────────────────────────────────────────
IDENTITY_LOCK_MSG = ("Access Locked: Please complete your basic profile details (Name, Birthday, "
                     "Mobile Number, Address, and Sex) in 'My Profile' first to unlock your job recommendations.")

def identity_complete(ap):
    """True only if every basic identity field is filled in: full name, birthday,
    mobile number, complete address (province, city, barangay, present address) and sex."""
    if not ap:
        return False
    keys = ('first_name', 'last_name', 'birthdate', 'contact_number',
            'province', 'city', 'barangay', 'address_line', 'sex')
    return all(str(ap[k] if k in ap.keys() else '' or '').strip() not in ('', 'None') for k in keys)

def _get_my_applicant():
    return get_db().execute(
        'SELECT * FROM applicants WHERE user_id=?', (session['user_id'],)
    ).fetchone()

def _save_profile_photo(file, applicant):
    """Validate and store an uploaded profile photo (JPEG/PNG, max 2 MB).
    Returns (filename, error). The file type is checked by its magic bytes,
    not just the extension."""
    data = file.read(PHOTO_MAX_BYTES + 1)
    if len(data) > PHOTO_MAX_BYTES:
        return None, 'Photo is too large (max 2 MB).'
    if data.startswith(b'\xff\xd8\xff'):
        ext = 'jpg'
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):
        ext = 'png'
    else:
        return None, 'Photo must be a JPEG or PNG image.'
    os.makedirs(PHOTO_DIR, exist_ok=True)
    name = f"ap{applicant['applicant_id']}_{secrets.token_hex(8)}.{ext}"
    with open(os.path.join(PHOTO_DIR, name), 'wb') as out:
        out.write(data)
    old = applicant['photo']
    if old:
        try:
            os.remove(os.path.join(PHOTO_DIR, os.path.basename(old)))
        except OSError:
            pass
    return name, None

def _save_certificate(file, applicant):
    """Validate and store a training certificate (PDF/JPEG/PNG, max 5 MB).
    Returns (stored_name, display_name, error); type is checked by magic bytes."""
    data = file.read(CERT_MAX_BYTES + 1)
    if len(data) > CERT_MAX_BYTES:
        return None, None, 'Certificate is too large (max 5 MB).'
    if data.startswith(b'%PDF-'):
        ext = 'pdf'
    elif data.startswith(b'\xff\xd8\xff'):
        ext = 'jpg'
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):
        ext = 'png'
    else:
        return None, None, 'Certificate must be a PDF, JPG or PNG file.'
    os.makedirs(CERT_DIR, exist_ok=True)
    name = f"cert{applicant['applicant_id']}_{secrets.token_hex(8)}.{ext}"
    with open(os.path.join(CERT_DIR, name), 'wb') as out:
        out.write(data)
    shown = secure_filename(os.path.basename(file.filename or '')) or f'certificate.{ext}'
    return name, shown[:80], None

@app.route('/certificates/<path:filename>')
@login_required
def certificate_file(filename):
    filename = os.path.basename(filename)
    role = session.get('role')
    if role == ROLE_JOBSEEKER:
        ap = _get_my_applicant()
        if not ap or not filename.startswith(f"cert{ap['applicant_id']}_"):
            abort(404)
    elif role == ROLE_EMPLOYER:
        # An employer may only open certificates of applicants who applied to one of their vacancies
        m = re.match(r'cert(\d+)_', filename)
        allowed = bool(m) and get_db().execute(
            "SELECT 1 FROM referrals r JOIN job_vacancies jv ON jv.vacancy_id=r.vacancy_id "
            "WHERE r.applicant_id=? AND jv.employer_id=? AND r.status != 'cancelled' LIMIT 1",
            (int(m.group(1)), session['user_id'])).fetchone()
        if not allowed:
            abort(404)
    elif role != ROLE_ADMIN:
        abort(404)
    return send_from_directory(CERT_DIR, filename)

@app.route('/photos/<path:filename>')
@login_required
def profile_photo(filename):
    return send_from_directory(PHOTO_DIR, os.path.basename(filename))

MAX_ACTIVE_REFERRALS = 3

def _active_referral_count(applicant_id):
    """Number of the applicant's active (not-withdrawn) referrals.
    An applicant may hold up to MAX_ACTIVE_REFERRALS at a time."""
    return get_db().execute(
        "SELECT COUNT(*) FROM referrals WHERE applicant_id=? AND status NOT IN ('cancelled','rejected')",
        (applicant_id,)
    ).fetchone()[0]

@app.route('/jobseeker/dashboard')
@jobseeker_required
def jobseeker_dashboard():
    db  = get_db()
    ap  = _get_my_applicant()
    referrals = []
    if ap:
        referrals = db.execute('''
            SELECT r.*, jv.job_title, jv.employer_name
            FROM referrals r
            JOIN job_vacancies jv ON r.vacancy_id = jv.vacancy_id
            WHERE r.applicant_id = ?
            ORDER BY r.referred_at DESC LIMIT 5
        ''', (ap['applicant_id'],)).fetchall()

    exp_months = _total_exp_months(ap) if ap else 0

    return render_template('jobseeker/dashboard.html',
                           ap=ap, identity_ok=identity_complete(ap),
                           referrals=referrals,
                           exp_months=exp_months)

@app.route('/jobseeker/profile/photo', methods=['POST'])
@jobseeker_required
def jobseeker_profile_photo():
    """Save a cropped profile photo right away (called by the crop modal)."""
    ap = _get_my_applicant()
    photo = request.files.get('photo')
    if not ap or not photo or not photo.filename:
        return jsonify(ok=False, error='No photo received.'), 400
    name, err = _save_profile_photo(photo, ap)
    if err:
        return jsonify(ok=False, error=err), 400
    db = get_db()
    db.execute('UPDATE applicants SET photo=? WHERE applicant_id=?', (name, ap['applicant_id']))
    db.commit()
    return jsonify(ok=True, url=url_for('profile_photo', filename=name))

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
        if not MOBILE_RE.match(f.get('contact_number', '').strip()):
            flash('Cellphone no. must be 11 digits starting with 09 (e.g. 09171234567).', 'danger')
            return redirect(url_for('jobseeker_profile'))
        if f.get('tin', '').strip() and not TIN_RE.match(f.get('tin', '').strip()):
            flash('TIN must be in the format 000-000-000-000.', 'danger')
            return redirect(url_for('jobseeker_profile'))
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
        # trainings: text fields + optional certificate upload (kept per row by position)
        try:
            old_trn = json.loads(ap['trainings'] or '[]')
        except (ValueError, TypeError):
            old_trn = []
        old_certs = {t.get('cert_file') for t in old_trn if t.get('cert_file')}
        cols = {k: f.getlist(f'trn_{k}[]') for k in ('course', 'institution', 'hours', 'certificate', 'cert_file')}
        uploads = request.files.getlist('trn_cert_upload[]')
        trainings = []
        for i in range(len(cols['course'])):
            cell = lambda k: (cols[k][i].strip() if i < len(cols[k]) else '')
            row = {k: cell(k) for k in ('course', 'institution', 'hours', 'certificate', 'cert_file')}
            if row['cert_file'] not in old_certs:     # only keep files this applicant already owns
                row['cert_file'] = row['certificate'] = ''
            up = uploads[i] if i < len(uploads) else None
            if up and up.filename:
                stored, shown, err = _save_certificate(up, ap)
                if err:
                    flash(f"{err} ({row['course'] or 'training'})", 'warning')
                else:
                    row['cert_file'], row['certificate'] = stored, shown
            if any(row.values()):
                trainings.append(row)
        new_certs = {t['cert_file'] for t in trainings if t['cert_file']}
        eligibils   = []
        for r in rows('elig', ['type', 'other', 'rating', 'date']):
            title = r['other'] if r['type'] == 'Others' else r['type']
            if title or r['rating'] or r['date']:
                eligibils.append({'title': title, 'rating': r['rating'], 'date': r['date']})
        work_hist   = rows('we',   ['company', 'address', 'position', 'from_m', 'from_y', 'to_m', 'to_y', 'current', 'months', 'status'])
        # A fresh graduate has no work history: drop anything submitted for it.
        if f.get('employment_status') != 'Employed' and f.get('unemployed_reason') == 'New entrant/fresh graduate':
            work_hist = []
        for w in work_hist:
            w['months'] = _work_months(w)

        languages = []
        for lang in LANGUAGE_CHOICES:
            key   = lang.lower()
            flags = {s: bool(f.get(f'lang_{key}_{s}')) for s in ('read', 'write', 'speak', 'understand')}
            if any(flags.values()):
                languages.append({'language': lang, **flags})
        # custom rows added with "+ Add Language": xlang_name_<n>, xlang_<skill>_<n>
        seen = {l.lower() for l in LANGUAGE_CHOICES}
        for k in sorted((k for k in f if k.startswith('xlang_name_')), key=lambda k: int(k.rsplit('_', 1)[1]) if k.rsplit('_', 1)[1].isdigit() else 0):
            n = k.rsplit('_', 1)[1]
            name = f.get(k, '').strip()[:60]
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            languages.append({'language': name,
                              **{s: bool(f.get(f'xlang_{s}_{n}')) for s in ('read', 'write', 'speak', 'understand')}})

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
        skills_items = [s.strip() for s in f.get('skills', '').split(',') if s.strip()][:3]
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
            WHERE applicant_id=?''', (
            f.get('first_name', '').strip(), f.get('middle_name', '').strip(),
            f.get('last_name', '').strip(), f.get('suffix', '').strip(),
            f.get('sex', ''), age, bd, f.get('civil_status', '').strip(),
            f.get('address_line', '').strip(), brgy, barangay_to_district(brgy, f.get('city', '')),
            f.get('city', '').strip(), f.get('province', '').strip(),
            f.get('height_cm', '').strip(), f.get('religion', '').strip(),
            f.get('tin', '').strip(), f.get('landline', '').strip(),
            f.get('contact_number', '').strip(),
            1 if disability else 0, json.dumps(disability),
            1 if f.get('is_4ps') else 0, f.get('household_id', '').strip(),
            1 if f.get('is_wodp') else 0, 1 if f.get('is_dswd_foodstamp') else 0,
            1 if f.get('is_caregiver') else 0,
            1 if f.get('ofw_status') == 'current' else 0,
            f.get('ofw_country', '').strip() if f.get('ofw_status') == 'current' else '',
            1 if f.get('ofw_status') == 'former' else 0,
            f.get('former_ofw_country', '').strip() if f.get('ofw_status') == 'former' else '',
            f.get('ofw_return_date', '').strip() if f.get('ofw_status') == 'former' else '',
            f.get('employment_status', 'Unemployed'), f.get('employed_type', '').strip(),
            f.get('unemployed_reason', '').strip(),
            int(f.get('job_search_months')) if f.get('job_search_months', '').strip().isdigit() else None,
            ml_pref, f.get('pref_work_local', '').strip(), f.get('pref_work_overseas', '').strip(),
            json.dumps(languages), json.dumps(education), json.dumps(trainings),
            json.dumps(eligibils), json.dumps(work_hist), json.dumps(other_skills),
            ml_educ, ml_skills, ml_workx,
            1 if f.get('certify') else 0,
            ap['applicant_id'],
        ))
        photo = request.files.get('photo')
        if photo and photo.filename:
            name, err = _save_profile_photo(photo, ap)
            if err:
                flash(err, 'warning')
            else:
                db.execute('UPDATE applicants SET photo=? WHERE applicant_id=?', (name, ap['applicant_id']))
        db.commit()
        for gone in old_certs - new_certs:          # certificates removed or replaced
            try:
                os.remove(os.path.join(CERT_DIR, os.path.basename(gone)))
            except OSError:
                pass
        flash('Profile saved.', 'success')
        return redirect(url_for('jobseeker_profile'))

    ap_d = dict(ap)
    for jcol in ('languages', 'education', 'trainings', 'eligibilities',
                 'work_history', 'other_skills', 'disability'):
        try:
            ap_d[jcol] = json.loads(ap_d.get(jcol) or '[]')
        except (ValueError, TypeError):
            ap_d[jcol] = []
    # Normalize old date_from/date_to format to separate from_m/from_y/to_m/to_y fields
    for w in ap_d.get('work_history', []):
        if 'date_from' in w and 'from_m' not in w:
            try:
                parts = str(w['date_from']).split('-')
                w['from_y'] = parts[0]
                w['from_m'] = str(int(parts[1]))
            except (IndexError, ValueError):
                pass
        if 'date_to' in w and 'to_m' not in w:
            try:
                parts = str(w['date_to']).split('-')
                w['to_y'] = parts[0]
                w['to_m'] = str(int(parts[1]))
            except (IndexError, ValueError):
                pass
    return render_template('jobseeker/profile.html', ap=ap_d, user=current_user(),
                           educ_levels=EDUC_LEVELS,
                           barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
                           barangay_district_map=BARANGAY_DISTRICT,
                           positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
                           all_skills_ac=ALL_SKILLS_AC,
                           suffixes=SUFFIX_CHOICES, civil_statuses=CIVIL_STATUS_CHOICES,
                           elig_types=ELIG_TYPES, religions=RELIGION_CHOICES, disability_types=DISABILITY_TYPES,
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
                db.execute('UPDATE users SET full_name=?, email=? WHERE user_id=?',
                           (name, mail, user['user_id']))
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
        db.execute('DELETE FROM referrals WHERE applicant_id=?', (ap['applicant_id'],))
        db.execute('DELETE FROM recommendations WHERE applicant_id=?', (ap['applicant_id'],))
        db.execute('DELETE FROM applicants WHERE applicant_id=?', (ap['applicant_id'],))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute("DELETE FROM users WHERE user_id=? AND role='jobseeker'", (uid,))
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
    cat_ml = {}
    cat_scores = []
    hidden_count = 0
    generated = False
    identity_ok = identity_complete(ap)
    profile_ok = bool(ap and ap['educ_level'] and ap['preferred_position'] and ap['skills'])
    if identity_ok and profile_ok and request.args.get('generate') and pipeline:
        vacancies = db.execute(
            'SELECT jv.*, e.city AS e_city, e.province AS e_province '
            'FROM job_vacancies jv LEFT JOIN employers e ON e.user_id = jv.employer_id '
            f'WHERE {OPEN_VACANCY_SQL}'
        ).fetchall()
        results, cat_ml = get_recommendations(
            ap['educ_level'], ap['preferred_position'],
            ap['skills'], ap['work_experience'] or '',
            [dict(v) for v in vacancies], applicant=ap
        )
        hidden_count = sum(1 for r in results if not r['hard_ok'])
        results = [r for r in results if r['hard_ok']]
        cat_scores = sorted(
            [{'name': name, 'score': score, 'icon': CAT_ICONS.get(name, 'bi-briefcase')}
             for name, score in cat_ml.items()],
            key=lambda x: x['score'], reverse=True
        )
        generated = True
        # Keep only the latest generated set for this applicant
        db.execute('DELETE FROM recommendations WHERE applicant_id=?', (ap['applicant_id'],))
        for rank, vac in enumerate(results, 1):
            db.execute(
                'INSERT INTO recommendations '
                '(applicant_id,vacancy_id,suitability_score,rank,generated_by) VALUES (?,?,?,?,?)',
                (ap['applicant_id'], vac['vacancy_id'], vac['suitability_score'], rank, session['user_id'])
            )
        db.commit()
    applied_ids = set()
    rejected_ids = set()
    active_count = 0
    if ap:
        applied_ids = {r['vacancy_id'] for r in db.execute(
            "SELECT vacancy_id FROM referrals WHERE applicant_id=? AND status != 'cancelled'",
            (ap['applicant_id'],)
        ).fetchall()}
        active_count = _active_referral_count(ap['applicant_id'])
        rejected_ids = {r['vacancy_id'] for r in db.execute(
            "SELECT vacancy_id FROM referrals WHERE applicant_id=? AND status='rejected'",
            (ap['applicant_id'],)).fetchall()}
    def _fmt_salary(info):
        try:
            lo = int(info.get('salary_min') or 0) or None
            hi = int(info.get('salary_max') or 0) or None
        except (ValueError, TypeError):
            lo = hi = None
        per = (info.get('salary_period') or 'month').lower()
        if lo and hi:   return f'₱{lo:,} – ₱{hi:,} / {per}'
        if lo:          return f'₱{lo:,}+ / {per}'
        if hi:          return f'Up to ₱{hi:,} / {per}'
        return None

    def _ap_skills_str():
        raw = [s.strip() for s in (ap['skills'] or '').split(',') if s.strip()]
        if not raw: return '—'
        return ', '.join(raw)

    def _build_fields(r):
        bd   = r.get('breakdown', {})
        info = r['info']
        out  = []
        if 'title' in bd:
            out.append({'key':'title','label':'Position',
                        'ap_val': ap['preferred_position'] or '—',
                        'vac_val': info.get('job_title') or '—',
                        'score': bd['title'],
                        'is_filter': True})
        if 'skills' in bd:
            vac_sk = [s.strip() for s in (info.get('req_skills') or '').split(',') if s.strip()]
            vac_str = ', '.join(vac_sk[:3]) + (f' +{len(vac_sk)-3} more' if len(vac_sk) > 3 else '')
            out.append({'key':'skills','label':'Skills',
                        'ap_val': _ap_skills_str(), 'vac_val': vac_str or '—',
                        'score': bd['skills']})
        if 'education' in bd:
            out.append({'key':'education','label':'Education',
                        'ap_val': ap['educ_level'] or '—',
                        'vac_val': info.get('req_education') or '—',
                        'score': bd['education']})
        if 'experience' in bd:
            have_mo = _total_exp_months(ap)
            req_mo  = info.get('req_experience_months') or 0
            out.append({'key':'experience','label':'Experience',
                        'ap_val':  f'{have_mo} mo.' if have_mo else 'No exp.',
                        'vac_val': f'{req_mo} mo. min.',
                        'score': bd['experience']})
        if 'location' in bd:
            ap_loc  = ((ap['pref_work_local'] or '') or (ap['pref_work_overseas'] or '') or '—').strip()
            out.append({'key':'location','label':'Location',
                        'ap_val': ap_loc, 'vac_val': _vacancy_location(info) or '—',
                        'score': bd['location']})
        if 'gender' in bd:
            out.append({'key':'gender','label':'Gender',
                        'ap_val': ap['sex'] or '—',
                        'vac_val': info.get('req_gender') or '—',
                        'score': bd['gender']})
        if 'age' in bd:
            lo_a, hi_a = info.get('req_age_min'), info.get('req_age_max')
            if lo_a and hi_a: vac_age = f'{lo_a}–{hi_a} yrs'
            elif lo_a:        vac_age = f'{lo_a}+ yrs'
            elif hi_a:        vac_age = f'Up to {hi_a} yrs'
            else:             vac_age = '—'
            out.append({'key':'age','label':'Age',
                        'ap_val': f'{ap["age"]} yrs' if ap['age'] else '—',
                        'vac_val': vac_age,
                        'score': bd['age']})
        return out

    fields_by_id = {r['vacancy_id']: (_build_fields(r) if ap else []) for r in results}
    vacancies_json = [
        {
            'vacancy_id':        r['vacancy_id'],
            'title':             r['title'],
            'employer':          r['employer'],
            'category':          r['category'],
            'icon':              r['icon'],
            'suitability_score': r['suitability_score'],
            'suitability_pct':   r['suitability_pct'],
            'fields':            fields_by_id[r['vacancy_id']],
            'explanation':       explain_match(r, fields_by_id[r['vacancy_id']]) if ap else '',
            'warns_list':        r.get('warns_list', []),
            'qualified':         r['qualified'],
            'req_unmet':         r['req_unmet'],
            'location':          r['location'],
            'title_score':       r['title_score'],
            'is_position_match': r['is_position_match'],
            'is_alternative':    r['is_alternative'],
            'salary':            _fmt_salary(r['info']),
            'deadline':          str(r['info'].get('application_deadline') or '') or None,
            'details_url':       url_for('public_job_detail', vid=r['vacancy_id'], src='rec'),
        }
        for r in results
    ]
    return render_template('jobseeker/recommendations.html',
                           ap=ap, results=results, generated=generated, hidden_count=hidden_count,
                           profile_ok=profile_ok, identity_ok=identity_ok,
                           identity_lock_msg=IDENTITY_LOCK_MSG, applied_ids=applied_ids, rejected_ids=rejected_ids,
                           at_referral_limit=active_count >= MAX_ACTIVE_REFERRALS,
                           active_referral_count=active_count,
                           max_active_referrals=MAX_ACTIVE_REFERRALS,
                           pipeline_loaded=pipeline is not None,
                           total_exp_months=_total_exp_months(ap) if ap else 0,
                           vacancies_json=vacancies_json,
                           cat_scores=cat_scores,
                           all_skills_display=', '.join(
                               dict.fromkeys(s.strip() for s in
                                   (ap['skills'] or '').split(',') +
                                   _parse_other_skills(ap)
                                   if s.strip())
                           ) if ap else '')

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
            JOIN job_vacancies jv ON r.vacancy_id = jv.vacancy_id
            WHERE r.applicant_id = ?
            ORDER BY r.referred_at DESC
        ''', (ap['applicant_id'],)).fetchall()
    return render_template('jobseeker/referrals.html', ap=ap, my_referrals=my_referrals)

@app.route('/jobseeker/jobs')
@jobseeker_required
def jobseeker_jobs():
    db       = get_db()
    ap       = _get_my_applicant()
    search   = request.args.get('search', '').strip()
    conds, params = [OPEN_VACANCY_SQL], []
    if search:
        conds.append('(job_title LIKE ? OR employer_name LIKE ?)')
        like = f'%{search}%'
        params += [like, like]
    vacancies = db.execute(
        f'SELECT * FROM job_vacancies WHERE {" AND ".join(conds)} ORDER BY created_at DESC', params
    ).fetchall()
    applied_ids = set()
    if ap:
        applied_ids = {r['vacancy_id'] for r in db.execute(
            "SELECT vacancy_id FROM referrals WHERE applicant_id=? AND status != 'cancelled'",
            (ap['applicant_id'],)
        ).fetchall()}
    vacancies = [v for v in vacancies if v['vacancy_id'] in applied_ids or meets_hard_requirements(v, ap)]
    profile_ok = bool(ap and ap['educ_level'] and ap['preferred_position'] and ap['skills'])
    return render_template('jobseeker/jobs.html', ap=ap, vacancies=vacancies,
                           applied_ids=applied_ids, profile_ok=profile_ok, search=search)

@app.route('/jobseeker/apply/<int:vid>/confirm')
@jobseeker_required
def jobseeker_apply_confirm(vid):
    db = get_db()
    ap = _get_my_applicant()
    if not ap:
        flash('Profile not found.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    if not identity_complete(ap) or not ap['educ_level'] or not ap['preferred_position'] or not ap['skills']:
        flash('Please complete your profile details before applying.', 'warning')
        return redirect(url_for('jobseeker_profile'))
    jv = db.execute(
        f'SELECT * FROM job_vacancies WHERE vacancy_id=? AND {OPEN_VACANCY_SQL}', (vid,)
    ).fetchone()
    if not jv:
        flash('That job is no longer available or its deadline has passed.', 'danger')
        return redirect(url_for('jobseeker_recommendations') + '?generate=1')
    existing = db.execute(
        "SELECT referral_id FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status != 'cancelled'",
        (ap['applicant_id'], vid)
    ).fetchone()
    if existing:
        flash(f'You have already applied for "{jv["job_title"]}".', 'info')
        return redirect(url_for('referral_slip', rid=existing['referral_id']))
    if _active_referral_count(ap['applicant_id']) >= MAX_ACTIVE_REFERRALS:
        flash(f'You already have {MAX_ACTIVE_REFERRALS} active applications. '
              'Withdraw one from My Applications before applying to another job.', 'warning')
        return redirect(url_for('jobseeker_referrals'))
    if not meets_hard_requirements(jv, ap):
        flash('You do not yet meet the required education or experience for this job.', 'warning')
        return redirect(url_for('jobseeker_recommendations'))
    score = None
    if pipeline:
        recs, _ = get_recommendations(
            ap['educ_level'], ap['preferred_position'],
            ap['skills'], ap['work_experience'] or '', [dict(jv)], applicant=ap
        )
        if recs:
            score = recs[0]['suitability_score']
    return render_template('jobseeker/apply_confirm.html', ap=ap, v=jv,
                           score=score, warnings=req_warnings(jv, ap))

@app.route('/jobseeker/apply', methods=['POST'])
@jobseeker_required
def jobseeker_apply():
    ap = _get_my_applicant()
    if not ap:
        flash('Profile not found.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    if not identity_complete(ap) or not ap['educ_level'] or not ap['preferred_position'] or not ap['skills']:
        flash('Please complete your profile details before applying.', 'warning')
        return redirect(url_for('jobseeker_profile'))
    db = get_db()
    vacancy_id = request.form.get('vacancy_id', type=int)
    jv = db.execute(
        f'SELECT * FROM job_vacancies WHERE vacancy_id=? AND {OPEN_VACANCY_SQL}',
        (vacancy_id,)
    ).fetchone() if vacancy_id else None
    back = url_for('jobseeker_recommendations') + '?generate=1'
    if not jv:
        flash('That job is no longer available or its deadline has passed.', 'danger')
        return redirect(back)
    existing = db.execute(
        "SELECT referral_id FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status != 'cancelled'",
        (ap['applicant_id'], vacancy_id)
    ).fetchone()
    if existing:
        flash(f'You have already applied for "{jv["job_title"]}".', 'info')
        return redirect(url_for('referral_slip', rid=existing['referral_id']))
    if _active_referral_count(ap['applicant_id']) >= MAX_ACTIVE_REFERRALS:
        flash(f'You already have {MAX_ACTIVE_REFERRALS} active applications. '
              'Withdraw one from My Applications before applying to another job.', 'warning')
        return redirect(url_for('jobseeker_referrals'))
    if not meets_hard_requirements(jv, ap):
        flash('You do not yet meet the required education or experience for this job.', 'warning')
        return redirect(url_for('jobseeker_recommendations'))
    score = None
    if pipeline:
        recs, _ = get_recommendations(
            ap['educ_level'], ap['preferred_position'],
            ap['skills'], ap['work_experience'] or '', [dict(jv)], applicant=ap
        )
        if recs:
            score = recs[0]['suitability_score']
    try:
        cur = db.execute(
            'INSERT INTO referrals (applicant_id, vacancy_id, referred_by, status, suitability_score) '
            'VALUES (?,?,?,?,?)',
            (ap['applicant_id'], vacancy_id, session['user_id'], 'referred', score)
        )
    except sqlite3.IntegrityError:
        # Double-click / two tabs: the database already holds this applicant's referral for this vacancy
        db.rollback()
        flash(f'You have already applied for "{jv["job_title"]}".', 'info')
        return redirect(url_for('jobseeker_referrals'))
    rid = cur.lastrowid
    db.commit()
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
        'JOIN job_vacancies jv ON r.vacancy_id = jv.vacancy_id '
        'WHERE r.referral_id=? AND r.applicant_id=?',
        (rid, ap['applicant_id'])
    ).fetchone()
    if not r:
        flash('Application not found.', 'danger')
        return redirect(url_for('jobseeker_referrals'))
    if r['status'] == 'cancelled':
        flash('That application is already cancelled.', 'info')
        return redirect(url_for('jobseeker_referrals'))
    if r['status'] == 'rejected':
        flash('This application was rejected by the employer and can no longer be changed.', 'warning')
        return redirect(url_for('jobseeker_referrals'))
    db.execute("UPDATE referrals SET status='cancelled' WHERE referral_id=?", (rid,))
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
        elif not TIN_RE.match(required['TIN']):
            err = 'TIN must be in the format 000-000-000-000.'
        elif not MOBILE_RE.match(required['Mobile no.']):
            err = 'Mobile no. must be 11 digits starting with 09 (e.g. 09171234567).'
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
            WHERE employer_id=?
        ''', (
            required['TIN'], required['Business name'], f.get('trade_name', '').strip(),
            required['Location type'], sector, emp_type, required['Total work force'],
            required['Line of business/industry'], required['Address'], required['Barangay'],
            required['City/Municipality'], required['Province'], required['Contact person'],
            required['Position'], f.get('telephone', '').strip(), required['Mobile no.'],
            f.get('fax', '').strip(), mail, emp['employer_id'],
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
    db.execute('UPDATE employers SET approval_requested=1 WHERE employer_id=?', (emp['employer_id'],))
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
                db.execute('UPDATE users SET full_name=?, email=? WHERE user_id=?',
                           (name, mail, user['user_id']))
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
    vac_ids = [r['vacancy_id'] for r in db.execute(
        'SELECT vacancy_id FROM job_vacancies WHERE employer_id=?', (uid,)).fetchall()]
    for vid in vac_ids:
        db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
        db.execute('DELETE FROM referrals WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE employer_id=?', (uid,))
    db.execute('DELETE FROM employers WHERE user_id=?', (uid,))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute("DELETE FROM users WHERE user_id=? AND role='employer'", (uid,))
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
        'SELECT COUNT(*) FROM referrals r JOIN job_vacancies jv ON r.vacancy_id=jv.vacancy_id '
        "WHERE jv.employer_id=? AND r.status!='cancelled'", (uid,)
    ).fetchone()[0]
    new_this_week = db.execute(
        'SELECT COUNT(*) FROM referrals r JOIN job_vacancies jv ON r.vacancy_id=jv.vacancy_id '
        "WHERE jv.employer_id=? AND r.status!='cancelled' "
        "AND date(r.referred_at) >= date('now','+8 hours','-7 days')", (uid,)
    ).fetchone()[0]
    recent_referrals = db.execute('''
        SELECT r.referral_id, r.status, r.referred_at, r.suitability_score,
               a.first_name, a.last_name, jv.job_title
        FROM referrals r
        JOIN applicants a ON r.applicant_id=a.applicant_id
        JOIN job_vacancies jv ON r.vacancy_id=jv.vacancy_id
        WHERE jv.employer_id=?
        ORDER BY r.referred_at DESC LIMIT 5
    ''', (uid,)).fetchall()
    # Vacancies expiring tomorrow (one-day warning to renew the deadline)
    expiring_soon = db.execute('''
        SELECT jv.vacancy_id, jv.job_title, jv.application_deadline
        FROM job_vacancies jv
        WHERE jv.employer_id=? AND jv.is_active=1
          AND jv.application_deadline = date('now','+8 hours','+1 day')
        ORDER BY jv.job_title
    ''', (uid,)).fetchall()
    # Per-vacancy applicant counts (open vacancies), upcoming interviews and "action needed" items
    today = _today_ph()
    open_vacs = []
    for v in db.execute(
        "SELECT jv.*, (SELECT COUNT(*) FROM referrals r WHERE r.vacancy_id=jv.vacancy_id AND r.status != 'cancelled') AS applicants "
        f"FROM job_vacancies jv WHERE jv.employer_id=? AND {OPEN_VACANCY_SQL} "
        "ORDER BY jv.created_at DESC", (uid,)).fetchall():
        v = dict(v)
        v['interview'] = interview_text(v)
        last_day = v['interview_date_end'] or v['interview_date']
        v['interview_upcoming'] = bool(last_day and last_day >= today)
        open_vacs.append(v)
    upcoming = sorted([v for v in open_vacs if v['interview_upcoming']], key=lambda v: v['interview_date'])
    actions = []
    if expiring_soon:
        n = len(expiring_soon)
        actions.append(dict(icon='bi-hourglass-split', tone='warning', url=url_for('employer_vacancies'),
                            text=f"{n} vacanc{'y expires' if n == 1 else 'ies expire'} tomorrow. Extend the deadline if you still need applicants."))
    if new_this_week:
        actions.append(dict(icon='bi-person-plus-fill', tone='primary', url=url_for('employer_referred'),
                            text=f"{new_this_week} new applicant{'' if new_this_week == 1 else 's'} in the last 7 days to review."))
    no_sched = [v for v in open_vacs if not v['interview_date']]
    if no_sched:
        n = len(no_sched)
        actions.append(dict(icon='bi-calendar-event', tone='secondary', url=url_for('employer_vacancies'),
                            text=f"{n} active vacanc{'y has' if n == 1 else 'ies have'} no interview schedule yet (shown to applicants as \"To be announced\")."))
    return render_template('employer/dashboard.html', emp=emp,
                           active_vac=active_vac, expired_vac=expired_vac,
                           total_referred=total_referred, new_this_week=new_this_week,
                           recent_referrals=recent_referrals, expiring_soon=expiring_soon,
                           open_vacs=open_vacs, upcoming=upcoming, actions=actions)

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
        f'SELECT *, {EXPIRED_SQL} AS expired, '
        "(SELECT COUNT(*) FROM referrals r WHERE r.vacancy_id=job_vacancies.vacancy_id AND r.status != 'cancelled') AS applicant_count "
        f'FROM job_vacancies WHERE {" AND ".join(conds)} ORDER BY created_at DESC',
        params
    ).fetchall()
    return render_template('employer/vacancies.html', emp=emp,
                           vacancies=vacancies, status=status,
                           categories=CATEGORY_LIST)

_PLACES_CACHE = []

@app.route('/api/places')
def places_list():
    """'City, Province' suggestions for location fields (from the bundled PSGC data)."""
    if not _PLACES_CACHE:
        base = os.path.join(app.root_path, 'static', 'data', 'psgc')
        try:
            names = {p['c']: p['n'] for p in json.load(open(os.path.join(base, 'provinces.json'), encoding='utf-8'))}
            out = []
            for fn in sorted(os.listdir(base)):
                if not fn.endswith('.json') or fn == 'provinces.json':
                    continue
                prov = 'Metro Manila' if fn == 'NCR.json' else names.get(fn[:-5], '')
                if not prov:
                    continue
                for city in json.load(open(os.path.join(base, fn), encoding='utf-8')):
                    nm = re.sub(r'^City of\s+', '', city).strip()
                    out.append(f'{nm}, {prov}')
            _PLACES_CACHE.extend(sorted(set(out)))
        except (OSError, ValueError):
            pass
    resp = jsonify(_PLACES_CACHE)
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp

@app.route('/api/location-hint')
@login_required
def location_hint():
    t = detect_location_type(request.args.get('q', ''))
    return jsonify(type=t, label=LOCATION_TYPES_V[t]['label'] if t else None)

@app.route('/employer/vacancies/add', methods=['GET', 'POST'])
@employer_required
def employer_vacancy_add():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    if request.method == 'POST':
        f = request.form
        req, err = parse_vacancy_requirements(f)
        ltype = resolve_location_type(f)
        job_title = f.get('job_title', '').strip()
        if err:
            pass
        elif not job_title:
            err = 'Job title is required.'
        elif not err and req['application_deadline'] and req['application_deadline'] < _today_ph():
            err = 'Application deadline cannot be in the past.'
        if err:
            flash(err, 'danger')
            return render_template('employer/vacancy_form.html', emp=emp,
                                   vacancy=f, action='add',
                                   educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                                   salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST,
                                   all_skills_ac=ALL_SKILLS_AC, positions=PREFERRED_POSITIONS)
        category = auto_predict_category(job_title)
        get_db().execute(
            'INSERT INTO job_vacancies (employer_name, job_title, occupational_category, '
            'is_local, location_type, employer_id, ' + ', '.join(REQ_COLS) + ') VALUES (?,?,?,?,?,?,' +
            ','.join('?' * len(REQ_COLS)) + ')',
            (emp['company_name'], job_title,
             category,
             1 if ltype == 'local' else 0, ltype,
             session['user_id'], *[req[c] for c in REQ_COLS])
        )
        get_db().commit()
        flash('Job vacancy posted.', 'success')
        return redirect(url_for('employer_vacancies'))
    return render_template('employer/vacancy_form.html', emp=emp,
                           vacancy=None, action='add',
                           educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                           salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST,
                           all_skills_ac=ALL_SKILLS_AC, positions=PREFERRED_POSITIONS)

@app.route('/employer/vacancies/<int:vid>/edit', methods=['GET', 'POST'])
@employer_required
def employer_vacancy_edit(vid):
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db = get_db()
    v  = db.execute(
        'SELECT * FROM job_vacancies WHERE vacancy_id=? AND employer_id=?',
        (vid, session['user_id'])
    ).fetchone()
    if not v:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('employer_vacancies'))
    if request.method == 'POST':
        f = request.form
        req, err = parse_vacancy_requirements(f)
        ltype = resolve_location_type(f)
        job_title = f.get('job_title', '').strip()
        if not err and not job_title:
            err = 'Job title is required.'
        if (not err and req['application_deadline'] and req['application_deadline'] < _today_ph()
                and req['application_deadline'] != v['application_deadline']):
            err = 'Application deadline cannot be in the past.'
        if err:
            flash(err, 'danger')
            return render_template('employer/vacancy_form.html', emp=emp,
                                   vacancy={**dict(v), **f.to_dict()},
                                   action='edit', educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                                   salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST,
                                   all_skills_ac=ALL_SKILLS_AC, positions=PREFERRED_POSITIONS)
        category = auto_predict_category(job_title)
        db.execute(
            'UPDATE job_vacancies SET job_title=?, occupational_category=?, is_local=?, location_type=?, ' +
            ', '.join(f'{c}=?' for c in REQ_COLS) + ' WHERE vacancy_id=?',
            (job_title, category,
             1 if ltype == 'local' else 0, ltype, *[req[c] for c in REQ_COLS], vid)
        )
        db.commit()
        flash('Vacancy updated.', 'success')
        return redirect(url_for('employer_vacancies'))
    return render_template('employer/vacancy_form.html', emp=emp,
                           vacancy=dict(v), action='edit',
                           educ_choices=REQ_EDUC_CHOICES, today=_today_ph(),
                           salary_periods=SALARY_PERIODS, skills_list=SKILLS_LIST,
                           all_skills_ac=ALL_SKILLS_AC, positions=PREFERRED_POSITIONS)

@app.route('/employer/vacancies/<int:vid>/toggle', methods=['POST'])
@employer_required
def employer_vacancy_toggle(vid):
    db = get_db()
    v  = db.execute(
        'SELECT is_active FROM job_vacancies WHERE vacancy_id=? AND employer_id=?',
        (vid, session['user_id'])
    ).fetchone()
    if v:
        db.execute('UPDATE job_vacancies SET is_active=? WHERE vacancy_id=?',
                   (0 if v['is_active'] else 1, vid))
        db.commit()
        flash('Vacancy status updated.', 'success')
    return redirect(url_for('employer_vacancies'))

@app.route('/employer/vacancies/<int:vid>/delete', methods=['POST'])
@employer_required
def employer_vacancy_delete(vid):
    db = get_db()
    v  = db.execute('SELECT job_title FROM job_vacancies WHERE vacancy_id=? AND employer_id=?',
                    (vid, session['user_id'])).fetchone()
    if not v:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('employer_vacancies'))
    db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM referrals WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE vacancy_id=?', (vid,))
    db.commit()
    flash(f'Vacancy "{v["job_title"]}" has been deleted.', 'success')
    return redirect(url_for('employer_vacancies'))

REJECT_REASONS = ['Requirements not matched', 'Position already filled', 'Incomplete requirements', 'Not qualified for the role', 'Other']

def fit_tier(score):
    """(key, label) for a 0-1 suitability score."""
    if score is None:
        return 'unknown', 'No score'
    if score >= 0.80:
        return 'strong', 'Strong fit'
    if score >= 0.50:
        return 'partial', 'Partial fit'
    return 'low', 'Low fit'

def fit_reason(v, ap):
    """Short reason chip for the worst mismatch (skills / position), or ''."""
    _, _, _, bd = vacancy_content_score(v, ap)
    if bd.get('skills') == 0:
        return 'No matching skills'
    if bd.get('title') == 0:
        return 'Different position'
    if bd.get('skills') is not None and bd['skills'] < 0.5:
        return 'Few matching skills'
    return ''

def employer_comparison(v, ap, score):
    """Requirement-vs-applicant rows for the employer's profile preview, missing items first.
    Returns (rows, summary, extra_skills, past_positions); row = (requirement, applicant_has, state)."""
    cb, _, title_score, bd = vacancy_content_score(v, ap)
    rows = []
    have_set = _ap_skills_set(ap)
    pos_state = 'ok' if title_score >= 0.5 else 'partial' if title_score > 0 else 'miss'
    rows.append(('Position: ' + (_g(v, 'job_title') or '-'), _g(ap, 'preferred_position') or '-', pos_state))
    req_raw = [x.strip() for x in (_g(v, 'req_skills') or '').split(',') if x.strip()]
    for sk in req_raw:
        hit = sk.lower() in have_set
        rows.append(('Skill: ' + sk, 'Has it' if hit else 'None listed', 'ok' if hit else 'miss'))
    need_edu = _g(v, 'req_education')
    if need_edu:
        have = _g(ap, 'educ_level') or '-'
        okay = have in EDUC_RANK and need_edu in EDUC_RANK and EDUC_RANK[have] >= EDUC_RANK[need_edu]
        rows.append(('Education: ' + need_edu, have, 'ok' if okay else 'miss'))
    need_m = _g(v, 'req_experience_months')
    if need_m:
        have_m = _total_exp_months(ap)
        rows.append((f'Experience: {need_m} mo.', f'{have_m} mo.', 'ok' if have_m >= need_m else 'miss'))
    if 'location' in bd:
        rows.append(('Location: ' + (_vacancy_location(v) or '-'),
                     ((_g(ap, 'pref_work_local') or _g(ap, 'pref_work_overseas')) or '-'),
                     'ok' if bd['location'] else 'miss'))
    order = {'miss': 0, 'partial': 1, 'ok': 2}
    rows.sort(key=lambda r: order[r[2]])
    missing_skills = [r[0] for r in rows if r[0].startswith('Skill:') and r[2] == 'miss']
    key, label = fit_tier(score)
    pct = f'{round(score * 100)}%' if score is not None else 'n/a'
    bits = []
    if req_raw and missing_skills:
        bits.append(f'{len(missing_skills)} of {len(req_raw)} required skills missing')
    if pos_state == 'miss':
        bits.append('preferred position is "' + (_g(ap, 'preferred_position') or 'not set') + '"')
    summary = f'{label} ({pct})' + (': ' + '; '.join(bits) + '.' if bits else '.')
    req_lower = {x.lower() for x in req_raw}
    extra = sorted(sk for sk in have_set if sk not in req_lower)[:8]
    try:
        past = [w.get('position') for w in json.loads(_g(ap, 'work_history') or '[]') if w.get('position')]
    except (ValueError, TypeError, AttributeError):
        past = []
    return rows, summary, extra, past

@app.route('/employer/referred')
@employer_required
def employer_referred():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db     = get_db()
    status = request.args.get('status', 'all')
    fit    = request.args.get('fit', 'all')
    conds  = ['jv.employer_id=?']
    params = [session['user_id']]
    if status != 'all':
        conds.append('r.status=?')
        params.append(status)
    rows = db.execute(f'''
        SELECT r.*, a.first_name, a.last_name, jv.job_title
        FROM referrals r
        JOIN applicants a ON r.applicant_id=a.applicant_id
        JOIN job_vacancies jv ON r.vacancy_id=jv.vacancy_id
        WHERE {" AND ".join(conds)}
        ORDER BY r.referred_at DESC
    ''', params).fetchall()
    referrals, counts = [], {'all': 0, 'strong': 0, 'partial': 0, 'low': 0, 'rejected': 0}
    for r in rows:
        d = dict(r)
        d['fit_key'], d['fit_label'] = fit_tier(d['suitability_score'])
        d['fit_reason'] = ''
        if d['fit_key'] in ('low', 'partial'):
            ap = db.execute('SELECT * FROM applicants WHERE applicant_id=?', (d['applicant_id'],)).fetchone()
            vac = db.execute('SELECT * FROM job_vacancies WHERE vacancy_id=?', (d['vacancy_id'],)).fetchone()
            if ap and vac:
                d['fit_reason'] = fit_reason(vac, ap)
        counts['all'] += 1
        if d['status'] == 'rejected':
            counts['rejected'] += 1
        elif d['fit_key'] in counts:
            counts[d['fit_key']] += 1
        referrals.append(d)
    if fit == 'rejected':
        referrals = [d for d in referrals if d['status'] == 'rejected']
    elif fit in ('strong', 'partial', 'low'):
        referrals = [d for d in referrals if d['fit_key'] == fit and d['status'] != 'rejected']
    # best fit first; rejected and withdrawn sink to the bottom
    referrals.sort(key=lambda d: (d['status'] in ('rejected', 'cancelled'), -(d['suitability_score'] or 0)))
    return render_template('employer/referred.html', emp=emp, referrals=referrals,
                           status=status, fit=fit, counts=counts, reject_reasons=REJECT_REASONS)

@app.route('/employer/referred/reject', methods=['POST'])
@employer_required
def employer_referred_reject():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    ids = [int(x) for x in request.form.getlist('ids') if x.isdigit()]
    reason = request.form.get('reason', '').strip()
    if reason not in REJECT_REASONS:
        reason = REJECT_REASONS[0]
    note = request.form.get('note', '').strip()[:200]
    if reason == 'Other' and note:
        reason = note
    back = request.form.get('fit', 'all')
    if not ids:
        flash('Select at least one applicant first.', 'warning')
        return redirect(url_for('employer_referred', fit=back))
    db = get_db()
    marks = ','.join('?' * len(ids))
    # who gets notified: only referrals that are about to change (still 'referred' and owned by this employer)
    targets = db.execute(
        "SELECT r.referral_id, a.user_id, jv.job_title FROM referrals r "
        "JOIN applicants a ON a.applicant_id=r.applicant_id "
        "JOIN job_vacancies jv ON jv.vacancy_id=r.vacancy_id "
        f"WHERE r.status='referred' AND r.referral_id IN ({marks}) AND jv.employer_id=?",
        ids + [session['user_id']]).fetchall()
    cur = db.execute(
        f"UPDATE referrals SET status='rejected', reject_reason=? WHERE status='referred' AND referral_id IN ({marks}) "
        "AND vacancy_id IN (SELECT vacancy_id FROM job_vacancies WHERE employer_id=?)",
        [reason] + ids + [session['user_id']])
    for t in targets:
        add_notification(db, t['user_id'], 'Application Update',
                         f'Your application for {t["job_title"]} was not selected. Reason: {reason}.',
                         url_for('jobseeker_referrals'))
    db.commit()
    flash(f'{cur.rowcount} applicant(s) marked as not selected.', 'success')
    return redirect(url_for('employer_referred', fit=back))

@app.route('/employer/referred/<int:rid>')
@employer_required
def employer_referred_detail(rid):
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_profile'))
    db = get_db()
    r = db.execute('''
        SELECT r.referral_id, r.suitability_score AS score,
               r.status AS ref_status, r.referred_at AS ref_at, r.reject_reason,
               a.first_name, a.last_name, a.sex, a.age, a.barangay, a.district,
               a.employment_status, a.is_pwd, a.educ_level, a.preferred_position,
               a.skills, a.work_experience, a.work_history, a.contact_number,
               jv.job_title, jv.occupational_category,
               jv.req_gender, jv.req_age_min, jv.req_age_max, jv.req_education,
               jv.req_experience_months, jv.req_skills,
               u.email AS applicant_email
        FROM referrals r
        JOIN applicants a     ON r.applicant_id = a.applicant_id
        JOIN job_vacancies jv ON r.vacancy_id   = jv.vacancy_id
        LEFT JOIN users u     ON a.user_id       = u.user_id
        WHERE r.referral_id=? AND jv.employer_id=?
    ''', (rid, session['user_id'])).fetchone()
    if not r:
        flash('Referred applicant not found.', 'danger')
        return redirect(url_for('employer_referred'))
    ids = db.execute('SELECT applicant_id, vacancy_id FROM referrals WHERE referral_id=?', (rid,)).fetchone()
    ap_full = db.execute('SELECT * FROM applicants WHERE applicant_id=?', (ids['applicant_id'],)).fetchone()
    vac_full = db.execute('SELECT * FROM job_vacancies WHERE vacancy_id=?', (ids['vacancy_id'],)).fetchone()
    cmp_rows, cmp_summary, extra_skills, past_positions = employer_comparison(vac_full, ap_full, r['score'])
    return render_template('employer/referred_detail.html', r=r,
                           chips=req_summary(r), warnings=req_warnings(r, r, viewer='employer'),
                           fit_key=fit_tier(r['score'])[0], cmp_rows=cmp_rows, cmp_summary=cmp_summary,
                           extra_skills=extra_skills, past_positions=past_positions)

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
        'SELECT applicant_id, first_name, last_name, preferred_position, created_at '
        'FROM applicants WHERE is_archived=0 '
        'ORDER BY created_at DESC, applicant_id DESC LIMIT 5'
    ).fetchall()
    recent_employers = db.execute(
        'SELECT employer_id, company_name, contact_person, line_of_business, is_approved, created_at '
        'FROM employers ORDER BY created_at DESC, employer_id DESC LIMIT 5'
    ).fetchall()
    recent_referrals_rows = db.execute('''
        SELECT r.referred_at, r.status,
               a.first_name, a.last_name,
               jv.job_title, jv.employer_name
        FROM referrals r
        JOIN applicants a ON r.applicant_id=a.applicant_id
        JOIN job_vacancies jv ON r.vacancy_id=jv.vacancy_id
        ORDER BY r.referred_at DESC LIMIT 5
    ''').fetchall()
    recent_recs = db.execute('''
        SELECT a.first_name, a.last_name,
               jv.job_title, jv.employer_name,
               rec.suitability_score
        FROM recommendations rec
        JOIN applicants a     ON rec.applicant_id = a.applicant_id
        JOIN job_vacancies jv ON rec.vacancy_id   = jv.vacancy_id
        ORDER BY rec.recommended_at DESC, rec.recommendation_id DESC LIMIT 5
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
                           recent_employers=recent_employers,
                           recent_referrals_rows=recent_referrals_rows,
                           recent_recs=recent_recs)

# ── ANALYTICS ─────────────────────────────────────────────────────────────────
@app.route('/analytics')
@admin_required
def analytics():
    return render_template('analytics.html')

def _analytics_data(date_from, date_to):
    db = get_db()
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
    # Barangay / district breakdown: spelling variants are merged, and anyone who is not in a CSJDM
    # barangay (other city, or no address yet) is counted in a third group so the totals add up.
    d1, d2, outside = {}, {}, {}
    for r in db.execute(
        f"SELECT barangay, city, province, district FROM applicants WHERE is_archived=0{df_sql}", dp
    ).fetchall():
        brgy = ' '.join((r['barangay'] or '').split())
        city = ' '.join((r['city'] or '').split())
        dist = r['district'] or (barangay_to_district(brgy, city) if brgy else '')
        target = d1 if dist == 'District 1' else d2 if dist == 'District 2' else None
        if target is not None and brgy:
            key, label = brgy.lower(), brgy
        else:
            place = city or ' '.join((r['province'] or '').split())
            target = outside
            key, label = (place.lower(), place) if place else ('', 'Not specified')
        entry = target.setdefault(key, [label, 0])
        entry[1] += 1
    def ranked(d):
        items = sorted(d.values(), key=lambda x: (-x[1], x[0].lower()))
        return [i[0] for i in items], [i[1] for i in items]
    d1_labels, d1_values = ranked(d1)
    d2_labels, d2_values = ranked(d2)
    o_labels, o_values = ranked(outside)

    # Registrations in the current month (Philippine time), independent of the date filter
    month = "strftime('%Y-%m', created_at, '+8 hours') = strftime('%Y-%m', 'now', '+8 hours')"
    new_month = {
        'total':  db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND {month}').fetchone()[0],
        'youth':  db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND {month} AND age BETWEEN {YOUTH_AGE_MIN} AND {YOUTH_AGE_MAX}').fetchone()[0],
        'senior': db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND {month} AND age >= {SENIOR_AGE_MIN}').fetchone()[0],
        'pwd':    db.execute(f'SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND {month} AND is_pwd=1').fetchone()[0],
    }
    return {
        'jobseekers': {
            'total': total, 'male': male, 'female': fem,
            'youth': youth, 'senior': senior, 'pwd': pwd, 'new_month': new_month,
            'educ_labels':  [r['educ_level'] for r in educ_rows],
            'educ_values':  [r['c'] for r in educ_rows],
            'emp_labels':   [r['employment_status'] for r in emp_rows],
            'emp_values':   [r['c'] for r in emp_rows],
            'd1_labels': d1_labels, 'd1_values': d1_values,
            'd2_labels': d2_labels, 'd2_values': d2_values,
            'o_labels':  o_labels,  'o_values':  o_values,
        }
    }

@app.route('/api/analytics')
@admin_required
def api_analytics():
    return jsonify(_analytics_data(request.args.get('date_from', '').strip(), request.args.get('date_to', '').strip()))

@app.route('/analytics/export')
@admin_required
def analytics_export():
    """CSV of the dashboard figures for the selected registration dates."""
    import csv
    import io
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    js = _analytics_data(date_from, date_to)['jobseekers']
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['PESO CSJDM - Analytical Dashboard'])
    w.writerow(['Registration dates', f'{date_from or "all"} to {date_to or "all"}'])
    w.writerow(['Generated', _now_ph().strftime('%Y-%m-%d %H:%M')])
    w.writerow([])
    w.writerow(['Summary', 'Count'])
    for label, key in (('Registered jobseekers', 'total'), ('Male', 'male'), ('Female', 'female'),
                       ('Youths', 'youth'), ('Senior citizens', 'senior'), ('Persons with disability', 'pwd')):
        w.writerow([label, js[key]])
    for title, labels, values in (('Educational attainment', js['educ_labels'], js['educ_values']),
                                  ('Employment status', js['emp_labels'], js['emp_values']),
                                  ('District 1 - jobseekers by barangay', js['d1_labels'], js['d1_values']),
                                  ('District 2 - jobseekers by barangay', js['d2_labels'], js['d2_values']),
                                  ('Outside CSJDM / no address', js['o_labels'], js['o_values'])):
        w.writerow([])
        w.writerow([title, 'Count'])
        for lbl, v in zip(labels, values):
            w.writerow([lbl, v])
    resp = make_response('\ufeff' + buf.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = f'attachment; filename=peso_analytics_{_now_ph().strftime("%Y%m%d")}.csv'
    return resp

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
        FROM applicants a LEFT JOIN users u ON a.user_id = u.user_id
        WHERE a.applicant_id = ?
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
    for w in ap_d.get('work_history', []):
        if 'date_from' in w and 'from_m' not in w:
            try:
                parts = str(w['date_from']).split('-')
                w['from_y'] = parts[0]
                w['from_m'] = str(int(parts[1]))
            except (IndexError, ValueError):
                pass
        if 'date_to' in w and 'to_m' not in w:
            try:
                parts = str(w['date_to']).split('-')
                w['to_y'] = parts[0]
                w['to_m'] = str(int(parts[1]))
            except (IndexError, ValueError):
                pass
    return render_template('applicants/view.html', ap=ap_d,
                           total_exp_months=_total_exp_months(ap))

@app.route('/applicants/<int:aid>/delete', methods=['POST'])
@admin_required
def applicant_delete(aid):
    db = get_db()
    ap = db.execute('SELECT first_name, last_name, user_id FROM applicants WHERE applicant_id=?', (aid,)).fetchone()
    if not ap:
        flash('Applicant not found.', 'danger')
        return redirect(url_for('applicants_list'))
    db.execute('DELETE FROM recommendations WHERE applicant_id=?', (aid,))
    db.execute('DELETE FROM referrals WHERE applicant_id=?', (aid,))
    db.execute('DELETE FROM applicants WHERE applicant_id=?', (aid,))
    # Remove the linked jobseeker login account, if any, so no orphan user remains
    if ap['user_id']:
        db.execute('DELETE FROM login_logs WHERE user_id=?', (ap['user_id'],))
        db.execute("DELETE FROM users WHERE user_id=? AND role='jobseeker'", (ap['user_id'],))
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
    joins = ('FROM referrals r JOIN applicants a ON r.applicant_id=a.applicant_id '
             'JOIN job_vacancies jv ON r.vacancy_id=jv.vacancy_id')
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
        LEFT JOIN users u     ON r.referred_by  = u.user_id
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
               jv.requirements_deadline, jv.interview_date, jv.interview_time, jv.interview_date_end, jv.interview_time_end,
               jv.venue_address,
               u.full_name AS accepted_by_name,
               e.contact_person AS e_contact, e.company_name AS e_company
        FROM referrals r
        JOIN applicants a     ON r.applicant_id = a.applicant_id
        JOIN job_vacancies jv ON r.vacancy_id   = jv.vacancy_id
        JOIN users u          ON r.referred_by  = u.user_id
        LEFT JOIN employers e ON e.user_id       = jv.employer_id
        WHERE r.referral_id=?
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
        ROLE_JOBSEEKER: url_for('jobseeker_recommendations', generate=1),
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
    v  = db.execute('SELECT is_active FROM job_vacancies WHERE vacancy_id=?', (vid,)).fetchone()
    if v:
        db.execute('UPDATE job_vacancies SET is_active=? WHERE vacancy_id=?',
                   (0 if v['is_active'] else 1, vid))
        db.commit()
        flash('Vacancy status updated.', 'success')
    return redirect(url_for('vacancies_list'))

@app.route('/vacancies/<int:vid>/delete', methods=['POST'])
@admin_required
def vacancy_delete(vid):
    db = get_db()
    v  = db.execute('SELECT job_title, employer_name FROM job_vacancies WHERE vacancy_id=?', (vid,)).fetchone()
    if not v:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('vacancies_list'))
    db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM referrals WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE vacancy_id=?', (vid,))
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
    u  = db.execute('SELECT * FROM users WHERE user_id=?', (uid,)).fetchone()
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
                db.execute('UPDATE users SET full_name=?,email=?,password_hash=?,role=? WHERE user_id=?',
                           (name, mail, generate_password_hash(pw), new_role, uid))
            else:
                db.execute('UPDATE users SET full_name=?,email=?,role=? WHERE user_id=?',
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
    u  = db.execute('SELECT full_name, email FROM users WHERE user_id=?', (uid,)).fetchone()
    if not u:
        flash('User not found.', 'danger')
        return redirect(url_for('users_list'))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute('DELETE FROM users WHERE user_id=?', (uid,))
    db.commit()
    flash(f'Account for {u["full_name"]} ({u["email"]}) has been permanently deleted.', 'success')
    return redirect(url_for('users_list'))


@app.route('/users/login-history')
@admin_required
def login_history():
    db = get_db()
    search = request.args.get('search', '').strip()
    outcome = request.args.get('outcome', 'all')
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    conds, params = [], []
    if search:
        like = f'%{search}%'
        conds.append('(ll.username LIKE ? OR u.full_name LIKE ? OR ll.ip_address LIKE ?)')
        params += [like, like, like]
    if outcome == 'success':
        conds.append("ll.outcome='success'")
    elif outcome == 'failed':
        conds.append("ll.outcome='failed'")
    elif outcome == 'denied':
        conds.append("ll.outcome='denied_inactive'")
    if date_from:
        conds.append("date(ll.timestamp, '+8 hours') >= ?")
        params.append(date_from)
    if date_to:
        conds.append("date(ll.timestamp, '+8 hours') <= ?")
        params.append(date_to)
    where = ('WHERE ' + ' AND '.join(conds)) if conds else ''
    base = f'FROM login_logs ll LEFT JOIN users u ON ll.user_id=u.user_id {where}'
    total = db.execute(f'SELECT COUNT(*) {base}', params).fetchone()[0]
    ok_count = db.execute(f"SELECT COUNT(*) {base}{' AND' if conds else ' WHERE'} ll.outcome='success'", params).fetchone()[0]
    page = max(1, request.args.get('page', 1, type=int))
    pages = max(1, (total + LIST_PER_PAGE - 1) // LIST_PER_PAGE)
    page = min(page, pages)
    logs = db.execute(
        f'SELECT ll.*, u.full_name {base} ORDER BY ll.timestamp DESC LIMIT ? OFFSET ?',
        params + [LIST_PER_PAGE, (page - 1) * LIST_PER_PAGE]
    ).fetchall()
    return render_template('users/login_history.html', logs=logs, search=search, outcome=outcome,
                           date_from=date_from, date_to=date_to, total=total, ok_count=ok_count,
                           bad_count=total - ok_count, page=page, pages=pages)

# ── ADMIN — EMPLOYER APPROVALS ────────────────────────────────────────────────
@app.route('/admin/employers')
@admin_required
def admin_employers():
    db     = get_db()
    status = request.args.get('status', 'pending')
    if status == 'pending':
        rows = db.execute(
            'SELECT e.*, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.user_id '
            'WHERE e.is_approved=0 AND e.approval_requested=1 ORDER BY e.created_at DESC'
        ).fetchall()
    elif status == 'approved':
        rows = db.execute(
            'SELECT e.*, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.user_id '
            'WHERE e.is_approved=1 ORDER BY e.created_at DESC'
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT e.*, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.user_id '
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
    emp = db.execute('SELECT * FROM employers WHERE employer_id=?', (eid,)).fetchone()
    if not emp:
        flash('Employer not found.', 'danger')
        return redirect(url_for('admin_employers'))
    if not emp['profile_completed']:
        flash('Cannot approve — this employer has not completed their company profile yet.', 'warning')
        return redirect(url_for('admin_employers'))
    db.execute('UPDATE employers SET is_approved=1 WHERE employer_id=?', (eid,))
    db.execute('UPDATE users SET is_active=1 WHERE user_id=?', (emp['user_id'],))
    db.commit()
    flash(f'Employer "{emp["company_name"]}" approved. They can now post job vacancies.', 'success')
    return redirect(url_for('admin_employers'))

@app.route('/admin/employers/<int:eid>/reject', methods=['POST'])
@admin_required
def admin_employer_reject(eid):
    db  = get_db()
    emp = db.execute('SELECT * FROM employers WHERE employer_id=?', (eid,)).fetchone()
    if not emp:
        flash('Employer not found.', 'danger')
        return redirect(url_for('admin_employers'))
    if emp['is_approved']:
        # Deactivate an already-approved employer
        db.execute('UPDATE employers SET is_approved=0, approval_requested=0 WHERE employer_id=?', (eid,))
        db.execute('UPDATE users SET is_active=0 WHERE user_id=?', (emp['user_id'],))
        flash(f'Employer "{emp["company_name"]}" deactivated.', 'warning')
    else:
        # Reject a pending request — let them revise their profile and request again
        db.execute('UPDATE employers SET approval_requested=0 WHERE employer_id=?', (eid,))
        flash(f'Approval request for "{emp["company_name"]}" rejected. '
              'They can revise their company profile and request approval again.', 'warning')
    db.commit()
    return redirect(url_for('admin_employers'))

@app.route('/admin/employers/<int:eid>/delete', methods=['POST'])
@admin_required
def admin_employer_delete(eid):
    db  = get_db()
    emp = db.execute('SELECT * FROM employers WHERE employer_id=?', (eid,)).fetchone()
    if not emp:
        flash('Employer not found.', 'danger')
        return redirect(url_for('admin_employers'))
    uid = emp['user_id']
    # Remove the employer's vacancies and everything linked to them
    vac_ids = [r['vacancy_id'] for r in db.execute(
        'SELECT vacancy_id FROM job_vacancies WHERE employer_id=?', (uid,)
    ).fetchall()]
    for vid in vac_ids:
        db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
        db.execute('DELETE FROM referrals WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE employer_id=?', (uid,))
    db.execute('DELETE FROM employers WHERE employer_id=?', (eid,))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute("DELETE FROM users WHERE user_id=? AND role='employer'", (uid,))
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
    app.run(debug=True, host='127.0.0.1', port=5000)
