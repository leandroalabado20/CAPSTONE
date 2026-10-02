"""
PESO CSJDM Web-Based Data-Driven Job Recommendation System
Flask Application Entry Point — Multi-Entity Version

Roles: admin | employer | jobseeker
Run:  python app.py
Default login: username=admin  password=admin123
"""

import os
import re
import json
import sqlite3
import joblib
import secrets
from datetime import datetime, timedelta
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
            username      TEXT    UNIQUE NOT NULL,
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
    if 'civil_status' in acols or 'age' not in acols:
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

    vcols = [r[1] for r in db.execute("PRAGMA table_info(job_vacancies)").fetchall()]
    if 'employer_id' not in vcols:
        db.execute('ALTER TABLE job_vacancies ADD COLUMN employer_id INTEGER REFERENCES users(id)')
    for col, ddl in [
        ('application_deadline', 'DATE'),
        ('req_gender',           "TEXT DEFAULT 'Any'"),
        ('req_age_min',          'INTEGER'),
        ('req_age_max',          'INTEGER'),
        ('req_education',        'TEXT'),
        ('req_physical',         'TEXT'),
        ('req_experience',       'TEXT'),
        ('req_other',            'TEXT'),
        ('req_documents',        'TEXT'),
    ]:
        if col not in vcols:
            db.execute(f'ALTER TABLE job_vacancies ADD COLUMN {col} {ddl}')

    rcols = [r[1] for r in db.execute("PRAGMA table_info(referrals)").fetchall()]
    if 'suitability_score' not in rcols:
        db.execute('ALTER TABLE referrals ADD COLUMN suitability_score REAL')

    ucols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
    if 'role' not in ucols:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'staff'")
    # Merge staff role into admin
    db.execute("UPDATE users SET role='admin' WHERE role='staff'")

    # ── Seed default admin ─────────────────────────────────────────────────────
    existing = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if existing == 0:
        db.execute(
            'INSERT INTO users (full_name, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?)',
            ('Administrator', 'admin', 'admin@peso.gov.ph',
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
    vals = {
        'application_deadline': (f.get('application_deadline') or '').strip() or None,
        'req_gender':     gender,
        'req_age_min':    num('req_age_min'),
        'req_age_max':    num('req_age_max'),
        'req_education':  edu if edu in EDUC_RANK else None,
        'req_physical':   f.get('req_physical', '').strip() or None,
        'req_experience': f.get('req_experience', '').strip() or None,
        'req_other':      f.get('req_other', '').strip() or None,
        'req_documents':  f.get('req_documents', '').strip() or None,
    }
    if vals['req_age_min'] and vals['req_age_max'] and vals['req_age_min'] > vals['req_age_max']:
        return vals, 'Minimum age cannot be greater than maximum age.'
    if vals['application_deadline']:
        try:
            datetime.strptime(vals['application_deadline'], '%Y-%m-%d')
        except ValueError:
            return vals, 'Application deadline is not a valid date.'
    return vals, None

REQ_COLS = ['application_deadline', 'req_gender', 'req_age_min', 'req_age_max',
            'req_education', 'req_physical', 'req_experience', 'req_other', 'req_documents']

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
    for k in ('req_physical', 'req_experience'):
        if _g(v, k):
            out.append(_g(v, k))
    return out

def req_warnings(v, ap):
    """Ways the applicant profile does not meet the vacancy's checkable requirements."""
    if not ap:
        return []
    w = []
    g, sex = _g(v, 'req_gender'), (ap['sex'] or '')
    if g in ('Male', 'Female') and sex and sex != g:
        w.append(f'Requires {g.lower()} applicants')
    age = ap['age']
    lo, hi = _g(v, 'req_age_min'), _g(v, 'req_age_max')
    if age is not None:
        if lo and age < lo:
            w.append(f'Minimum age is {lo}')
        if hi and age > hi:
            w.append(f'Maximum age is {hi}')
    need, have = _g(v, 'req_education'), (ap['educ_level'] or '')
    if need in EDUC_RANK and have in EDUC_RANK and EDUC_RANK[have] < EDUC_RANK[need]:
        w.append(f'Requires {need} or higher')
    return w

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
        })
    # Layer 2: stable-sort each category's vacancies so best requirement-fit rises
    for cat_vacs in vac_by_cat.values():
        cat_vacs.sort(key=lambda x: x['req_unmet'])
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
    if session.get('role') == ROLE_ADMIN:
        try:
            pending_employers_count = get_db().execute(
                "SELECT COUNT(*) FROM employers WHERE is_approved=0"
            ).fetchone()[0]
        except Exception:
            pass
    return {
        'pipeline_loaded':         pipeline is not None,
        'session_role':            session.get('role', ''),
        'pending_employers_count': pending_employers_count,
    }

# ── TEMPLATE FILTERS ──────────────────────────────────────────────────────────
_PHT = timedelta(hours=8)

def _today_ph():
    return (datetime.utcnow() + _PHT).strftime('%Y-%m-%d')

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

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(_role_home())
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip       = request.remote_addr
        db       = get_db()
        user     = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                           (user['id'], username, ip, 'denied_inactive'))
                db.commit()
                flash('Your account is deactivated. Contact an administrator.', 'danger')
            else:
                session.clear()
                session['user_id']   = user['id']
                session['username']  = user['username']
                session['full_name'] = user['full_name']
                session['role']      = user['role'] or ROLE_ADMIN
                db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                           (user['id'], username, ip, 'success'))
                db.commit()
                # Employer must be approved before accessing portal
                if session['role'] == ROLE_EMPLOYER:
                    emp = db.execute('SELECT is_approved FROM employers WHERE user_id=?',
                                     (user['id'],)).fetchone()
                    if not emp or not emp['is_approved']:
                        return redirect(url_for('employer_pending'))
                return redirect(_role_home())
        else:
            uid = user['id'] if user else None
            db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                       (uid, username, ip, 'failed'))
            db.commit()
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/register/jobseeker', methods=['GET', 'POST'])
def register_jobseeker():
    if 'user_id' in session:
        return redirect(_role_home())
    form_kwargs = dict(
        educ_levels=EDUC_LEVELS,
        barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
        barangay_district_map=BARANGAY_DISTRICT,
        positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
        work_exp_list=WORK_EXPERIENCE_LIST,
    )
    if request.method == 'POST':
        f         = request.form
        username  = f.get('username', '').strip()
        email     = f.get('email', '').strip()
        pw        = f.get('password', '')
        conf      = f.get('confirm_password', '')
        first     = f.get('first_name', '').strip()
        last      = f.get('last_name', '').strip()
        birthdate = f.get('birthdate', '').strip()
        contact   = f.get('contact_number', '').strip()

        errs = []
        if not all([username, email, pw, first, last, birthdate]):
            errs.append('All required fields must be filled.')
        if f.get('is_pwd') not in ('0', '1'):
            errs.append('Please indicate whether you are a Person with Disability (PWD).')
        if pw != conf:
            errs.append('Passwords do not match.')
        if len(pw) < 8:
            errs.append('Password must be at least 8 characters.')
        if errs:
            for e in errs:
                flash(e, 'danger')
            return render_template('auth/register_jobseeker.html', form=f, **form_kwargs)

        db = get_db()
        if f.get('confirm_duplicate') != '1':
            dup = find_duplicate_applicant(db, first, last, birthdate)
            if dup:
                msg = (f"A record for {dup['first_name']} {dup['last_name']} "
                       f"(born {dup['birthdate']}) already exists")
                if contact and dup['contact_number'] and contact == dup['contact_number']:
                    msg += ', with the same contact number'
                msg += '. If this is a different person, check the box below and submit again.'
                flash(msg, 'warning')
                return render_template('auth/register_jobseeker.html', form=f,
                                       duplicate_warning=True, **form_kwargs)
        try:
            db.execute(
                'INSERT INTO users (full_name, username, email, password_hash, role) VALUES (?,?,?,?,?)',
                (f'{first} {last}', username, email,
                 generate_password_hash(pw), ROLE_JOBSEEKER)
            )
            db.commit()
            uid = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            age = f.get('age', '').strip()
            educ       = f.get('educ_level', '')
            preferred  = f.get('preferred_position', '').strip()
            skills     = f.get('skills', '').strip()
            work_exp   = f.get('work_experience', '').strip()
            barangay   = f.get('barangay', '').strip()
            db.execute('''
                INSERT INTO applicants
                    (first_name, last_name, sex, age, barangay, district,
                     employment_status, is_pwd, educ_level, preferred_position,
                     skills, work_experience, birthdate, contact_number, user_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                first, last,
                f.get('sex', ''),
                int(age) if age.isdigit() else None,
                barangay,
                barangay_to_district(barangay),
                'Unemployed',
                1 if f.get('is_pwd') == '1' else 0,
                educ, preferred, skills, work_exp,
                birthdate, contact,
                uid,
            ))
            db.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('auth/register_jobseeker.html', form={}, **form_kwargs)

@app.route('/register/employer', methods=['GET', 'POST'])
def register_employer():
    if 'user_id' in session:
        return redirect(_role_home())
    if request.method == 'POST':
        f            = request.form
        username     = f.get('username', '').strip()
        email        = f.get('email', '').strip()
        pw           = f.get('password', '')
        conf         = f.get('confirm_password', '')
        company_name = f.get('company_name', '').strip()
        contact      = f.get('contact_person', '').strip()

        errs = []
        if not all([username, email, pw, company_name, contact]):
            errs.append('All required fields must be filled.')
        if pw != conf:
            errs.append('Passwords do not match.')
        if len(pw) < 8:
            errs.append('Password must be at least 8 characters.')
        if errs:
            for e in errs:
                flash(e, 'danger')
            return render_template('auth/register_employer.html', form=f,
                                   categories=CATEGORY_LIST)
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (full_name, username, email, password_hash, role) VALUES (?,?,?,?,?)',
                (company_name, username, email,
                 generate_password_hash(pw), ROLE_EMPLOYER)
            )
            db.commit()
            uid = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            db.execute(
                'INSERT INTO employers (user_id, company_name, contact_person, phone, address) '
                'VALUES (?,?,?,?,?)',
                (uid, company_name, contact,
                 f.get('phone', '').strip(), f.get('address', '').strip())
            )
            # Save initial vacancy as inactive — activates on approval
            job_title = f.get('job_title', '').strip()
            occ_cat   = f.get('occupational_category', '').strip()
            if job_title and occ_cat:
                db.execute(
                    'INSERT INTO job_vacancies '
                    '(employer_name, job_title, occupational_category, is_local, is_active, employer_id) '
                    'VALUES (?,?,?,?,0,?)',
                    (company_name, job_title, occ_cat,
                     1 if f.get('is_local', '1') == '1' else 0, uid)
                )
            db.commit()
            flash('Employer account submitted! PESO admin will review and approve your registration.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('auth/register_employer.html', form={},
                           categories=CATEGORY_LIST)

@app.route('/settings/password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = current_user()
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
    return render_template('settings/password.html', user=user)

# ── JOBSEEKER PORTAL ──────────────────────────────────────────────────────────
def _get_my_applicant():
    return get_db().execute(
        'SELECT * FROM applicants WHERE user_id=?', (session['user_id'],)
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
        f   = request.form
        age = f.get('age', '').strip()
        brgy = f.get('barangay', '').strip()
        db.execute('''
            UPDATE applicants SET sex=?, age=?, barangay=?, district=?,
                employment_status=?, is_pwd=?, educ_level=?,
                preferred_position=?, skills=?, work_experience=?,
                birthdate=?, contact_number=?
            WHERE id=?
        ''', (
            f.get('sex', ''),
            int(age) if age.isdigit() else None,
            brgy, barangay_to_district(brgy),
            f.get('employment_status', 'Unemployed'),
            1 if f.get('is_pwd') else 0,
            f.get('educ_level', ''),
            f.get('preferred_position', '').strip(),
            f.get('skills', '').strip(),
            f.get('work_experience', '').strip(),
            f.get('birthdate', '').strip(),
            f.get('contact_number', '').strip(),
            ap['id'],
        ))
        db.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('jobseeker_profile'))
    user = current_user()
    return render_template('jobseeker/profile.html', ap=dict(ap),
                           user=user, educ_levels=EDUC_LEVELS,
                           barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
                           barangay_district_map=BARANGAY_DISTRICT,
                           positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
                           work_exp_list=WORK_EXPERIENCE_LIST)

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
            f'SELECT * FROM job_vacancies WHERE {OPEN_VACANCY_SQL}'
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
    if ap:
        applied_ids = {r['vacancy_id'] for r in db.execute(
            "SELECT vacancy_id FROM referrals WHERE applicant_id=? AND status != 'cancelled'",
            (ap['id'],)
        ).fetchall()}
    return render_template('jobseeker/recommendations.html',
                           ap=ap, results=results, generated=generated,
                           profile_ok=profile_ok, applied_ids=applied_ids,
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

@app.route('/employer/pending')
@login_required
def employer_pending():
    if session.get('role') != ROLE_EMPLOYER:
        return redirect(_role_home())
    emp = _get_my_employer()
    if emp and emp['is_approved']:
        return redirect(url_for('employer_dashboard'))
    return render_template('employer/pending.html')

@app.route('/employer/dashboard')
@employer_required
def employer_dashboard():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_pending'))
    db = get_db()
    active_vac = db.execute(
        'SELECT COUNT(*) FROM job_vacancies WHERE employer_id=? AND is_active=1',
        (session['user_id'],)
    ).fetchone()[0]
    total_referred = db.execute(
        'SELECT COUNT(*) FROM referrals r '
        'JOIN job_vacancies jv ON r.vacancy_id=jv.id '
        'WHERE jv.employer_id=?',
        (session['user_id'],)
    ).fetchone()[0]
    recent_referrals = db.execute('''
        SELECT r.*, a.first_name, a.last_name, jv.job_title
        FROM referrals r
        JOIN applicants a ON r.applicant_id=a.id
        JOIN job_vacancies jv ON r.vacancy_id=jv.id
        WHERE jv.employer_id=?
        ORDER BY r.referred_at DESC LIMIT 5
    ''', (session['user_id'],)).fetchall()
    return render_template('employer/dashboard.html', emp=emp,
                           active_vac=active_vac, total_referred=total_referred,
                           recent_referrals=recent_referrals)

@app.route('/employer/vacancies')
@employer_required
def employer_vacancies():
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_pending'))
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
        return redirect(url_for('employer_pending'))
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
                                   educ_choices=REQ_EDUC_CHOICES, today=_today_ph())
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
                           educ_choices=REQ_EDUC_CHOICES, today=_today_ph())

@app.route('/employer/vacancies/<int:vid>/edit', methods=['GET', 'POST'])
@employer_required
def employer_vacancy_edit(vid):
    emp = _get_my_employer()
    if not emp or not emp['is_approved']:
        return redirect(url_for('employer_pending'))
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
                                   action='edit', educ_choices=REQ_EDUC_CHOICES, today=_today_ph())
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
                           educ_choices=REQ_EDUC_CHOICES, today=_today_ph())

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
        return redirect(url_for('employer_pending'))
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
    return render_template('home.html',
                           total_applicants=total_applicants,
                           active_vacancies=active_vacancies,
                           total_employers=total_employers,
                           total_recs=total_recs,
                           total_referrals=total_referrals,
                           pending_employers=pending_employers,
                           last_login=last_login,
                           recent_applicants=recent_applicants,
                           recent_referrals_rows=recent_referrals_rows)

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
        SELECT a.*, u.username, u.email
        FROM applicants a LEFT JOIN users u ON a.user_id = u.id
        WHERE a.id = ?
    ''', (aid,)).fetchone()
    if not ap:
        flash('Applicant not found.', 'danger')
        return redirect(url_for('applicants_list'))
    return render_template('applicants/view.html', ap=dict(ap))

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
    referrals = db.execute(f'''
        SELECT r.*,
               a.first_name, a.last_name,
               jv.job_title, jv.employer_name, jv.occupational_category,
               u.full_name as referred_by_name
        FROM referrals r
        JOIN applicants a     ON r.applicant_id = a.id
        JOIN job_vacancies jv ON r.vacancy_id   = jv.id
        LEFT JOIN users u     ON r.referred_by  = u.id
        {where}
        ORDER BY r.referred_at DESC
    ''', params).fetchall()
    return render_template('admin/referrals.html', referrals=referrals,
                           status=status, search=search)

@app.route('/referrals/<int:rid>/slip')
@login_required
def referral_slip(rid):
    db = get_db()
    r = db.execute('''
        SELECT r.*, a.first_name, a.last_name, a.sex, a.age, a.barangay,
               a.contact_number, a.educ_level, a.preferred_position, a.user_id AS applicant_user_id,
               jv.job_title, jv.employer_name, jv.occupational_category, jv.employer_id,
               jv.created_at AS posted_at, jv.application_deadline, jv.req_gender, jv.req_age_min,
               jv.req_age_max, jv.req_education, jv.req_physical, jv.req_experience,
               jv.req_other, jv.req_documents,
               u.full_name AS accepted_by_name
        FROM referrals r
        JOIN applicants a     ON r.applicant_id = a.id
        JOIN job_vacancies jv ON r.vacancy_id   = jv.id
        JOIN users u          ON r.referred_by  = u.id
        WHERE r.id=?
    ''', (rid,)).fetchone()
    role = session.get('role')
    allowed = bool(r) and (
        role == ROLE_ADMIN
        or (role == ROLE_JOBSEEKER and r['applicant_user_id'] == session['user_id'])
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
    q = f'SELECT *, {EXPIRED_SQL} AS expired FROM job_vacancies'
    if conds:
        q += ' WHERE ' + ' AND '.join(conds)
    q += ' ORDER BY created_at DESC'
    vacancies = db.execute(q, params).fetchall()
    view = request.args.get('view', 'card')
    return render_template('vacancies/list.html', vacancies=vacancies,
                           search=search, status=status, view=view)

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
        user = f.get('username','').strip()
        mail = f.get('email','').strip()
        pw   = f.get('password','')
        conf = f.get('confirm_password','')
        errs = []
        if not all([name, user, mail, pw]):
            errs.append('All fields are required.')
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
                    'INSERT INTO users (full_name,username,email,password_hash,role) VALUES (?,?,?,?,?)',
                    (name, user, mail, generate_password_hash(pw), ROLE_ADMIN)
                )
                get_db().commit()
                flash('User account created.', 'success')
                return redirect(url_for('users_list'))
            except sqlite3.IntegrityError:
                flash('Username or email already exists.', 'danger')
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
        username = f.get('username','').strip()
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
                db.execute('UPDATE users SET full_name=?,username=?,email=?,password_hash=?,role=? WHERE id=?',
                           (name, username, mail, generate_password_hash(pw), new_role, uid))
            else:
                db.execute('UPDATE users SET full_name=?,username=?,email=?,role=? WHERE id=?',
                           (name, username, mail, new_role, uid))
            db.commit()
            flash('User updated.', 'success')
            return redirect(url_for('users_list'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('users/form.html', user=dict(u), action='edit')

@app.route('/users/<int:uid>/delete', methods=['POST'])
@admin_required
def user_delete(uid):
    if uid == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users_list'))
    db = get_db()
    u  = db.execute('SELECT full_name, username FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        flash('User not found.', 'danger')
        return redirect(url_for('users_list'))
    db.execute('DELETE FROM login_logs WHERE user_id=?', (uid,))
    db.execute('DELETE FROM users WHERE id=?', (uid,))
    db.commit()
    flash(f'Account for {u["full_name"]} (@{u["username"]}) has been permanently deleted.', 'success')
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
            'SELECT e.*, u.username, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.id '
            'WHERE e.is_approved=0 ORDER BY e.created_at DESC'
        ).fetchall()
    elif status == 'approved':
        rows = db.execute(
            'SELECT e.*, u.username, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.id '
            'WHERE e.is_approved=1 ORDER BY e.created_at DESC'
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT e.*, u.username, u.email, u.is_active '
            'FROM employers e JOIN users u ON e.user_id=u.id '
            'ORDER BY e.created_at DESC'
        ).fetchall()
    pending_count = db.execute(
        'SELECT COUNT(*) FROM employers WHERE is_approved=0'
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
    db.execute('UPDATE employers SET is_approved=1 WHERE id=?', (eid,))
    db.execute('UPDATE users SET is_active=1 WHERE id=?', (emp['user_id'],))
    # Activate all vacancies submitted during registration
    db.execute('UPDATE job_vacancies SET is_active=1 WHERE employer_id=?', (emp['user_id'],))
    db.commit()
    vac_count = db.execute(
        'SELECT COUNT(*) FROM job_vacancies WHERE employer_id=?', (emp['user_id'],)
    ).fetchone()[0]
    flash(f'Employer "{emp["company_name"]}" approved — {vac_count} vacancy/vacancies now live.', 'success')
    return redirect(url_for('admin_employers'))

@app.route('/admin/employers/<int:eid>/reject', methods=['POST'])
@admin_required
def admin_employer_reject(eid):
    db  = get_db()
    emp = db.execute('SELECT * FROM employers WHERE id=?', (eid,)).fetchone()
    if not emp:
        flash('Employer not found.', 'danger')
        return redirect(url_for('admin_employers'))
    db.execute('UPDATE employers SET is_approved=0 WHERE id=?', (eid,))
    db.execute('UPDATE users SET is_active=0 WHERE id=?', (emp['user_id'],))
    db.commit()
    flash(f'Employer "{emp["company_name"]}" rejected/deactivated.', 'warning')
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
