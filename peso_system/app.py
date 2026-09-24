"""
PESO CSJDM Web-Based Data-Driven Job Recommendation System
Flask Application Entry Point — Multi-Entity Version

Roles: admin | staff | employer | jobseeker
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

import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── APP CONFIG ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'peso-csjdm-2026-secret-change-in-prod')

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATABASE       = os.path.join(BASE_DIR, 'peso.db')
PIPELINE_PATH  = os.path.join(BASE_DIR, 'ml', 'recommendation_pipeline.pkl')
UPLOAD_FOLDER  = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXT    = {'xlsx', 'xls'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── ROLE CONSTANTS ────────────────────────────────────────────────────────────
ROLE_ADMIN     = 'admin'
ROLE_STAFF     = 'staff'
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

# ── PEIS IMPORT NORMALIZATION ──────────────────────────────────────────────────
EDUC_NORMALIZE = {
    'GRADE I':                                        'Elementary Level',
    'GRADE II':                                       'Elementary Level',
    'GRADE III':                                      'Elementary Level',
    'GRADE IV':                                       'Elementary Level',
    'GRADE V':                                        'Elementary Level',
    'GRADE VI':                                       'Elementary Level',
    'ELEMENTARY GRADUATE':                            'Elementary Graduate',
    'GRADE VII':                                      'High School Level',
    'GRADE VIII':                                     'High School Level',
    '1ST YEAR HIGH SCHOOL/GRADE VII (FOR K TO 12)':  'High School Level',
    '2ND YEAR HIGH SCHOOL/GRADE VIII (FOR K TO 12)': 'High School Level',
    '3RD YEAR HIGH SCHOOL/GRADE IX (FOR K TO 12)':   'High School Level',
    '4TH YEAR HIGH SCHOOL/GRADE X (FOR K TO 12)':    'High School Level',
    'HIGH SCHOOL GRADUATE':                           'High School Graduate',
    'SECONDARY (K-12)':                               'High School Graduate',
    'SECONDARY (NON K-12)':                           'High School Graduate',
    'GRADE XI (FOR K TO 12)':                         'Senior High School Level',
    'GRADE XII (FOR K TO 12)':                        'Senior High School Graduate',
    '1ST YEAR COLLEGE LEVEL':                         'College Level',
    '2ND YEAR COLLEGE LEVEL':                         'College Level',
    '3RD YEAR COLLEGE LEVEL':                         'College Level',
    '4TH YEAR COLLEGE LEVEL':                         'College Level',
    '5TH YEAR COLLEGE LEVEL':                         'College Level',
    'COLLEGE GRADUATE':                               'College Graduate',
    'MASTERAL/POST GRADUATE':                         'College Graduate',
    'MASTERAL/POST GRADUATE LEVEL':                   'College Graduate',
    'VOCATIONAL GRADUATE':                            'Vocational',
    'VOCATIONAL UNDERGRADUATE':                       'Vocational',
    'ALS':                                            'ALS',
    'ALS (ALTERNATIVE LEARNING SYSTEM)':              'ALS',
}

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


def normalize_educ(raw):
    return EDUC_NORMALIZE.get(re.sub(r'\s+', ' ', str(raw)).strip().upper(), '')


def barangay_to_district(raw):
    return BARANGAY_DISTRICT.get(re.sub(r'\s+', ' ', str(raw)).strip().upper(), '')


def parse_age(raw):
    m = re.search(r'\d+', str(raw))
    return int(m.group()) if m else None


def yn_to_int(raw):
    return 1 if str(raw).strip().lower() in ('yes', 'y', '1', 'true') else 0


def parse_peis_date(raw):
    if raw is None:
        return None
    try:
        import pandas as _pd
        if hasattr(raw, '__float__') and _pd.isna(raw):
            return None
        return _pd.to_datetime(raw).strftime('%Y-%m-%d')
    except Exception:
        return None


def normalize_peis_row(row):
    get_col = lambda c: '' if pd.isna(row.get(c, '')) else str(row.get(c, '')).strip()
    first     = get_col('FIRSTNAME') or get_col('FIRST NAME')
    last      = get_col('LASTNAME')  or get_col('LAST NAME')
    educ      = normalize_educ(get_col('EDUC LEVEL'))
    preferred = get_col('PREFERRED POSITION')
    skills    = get_col('SKILLS')
    if not any((first, last, educ, preferred, skills)):
        return None
    barangay = get_col('BARANGAY')
    sex_raw  = get_col('SEX').upper()
    return {
        'first_name':         first or 'Unknown',
        'last_name':          last or 'Unknown',
        'educ_level':         educ,
        'preferred_position': preferred,
        'skills':             skills,
        'work_experience':    get_col('WORK EXPERIENCE'),
        'sex':                'Male' if sex_raw.startswith('M') else ('Female' if sex_raw.startswith('F') else ''),
        'employment_status':  get_col('EMP. STATUS') or get_col('EMPLOYMENT STATUS') or 'Unemployed',
        'barangay':           barangay,
        'district':           barangay_to_district(barangay),
        'age':                parse_age(get_col('AGE')),
        'is_pwd':             yn_to_int(get_col('PWD')),
        'peis_reg_date':      parse_peis_date(row.get('REG. DATE')),
    }

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
            role          TEXT    DEFAULT 'staff',
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
            peis_reg_date      DATE,
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
            notes        TEXT,
            FOREIGN KEY (applicant_id) REFERENCES applicants(id),
            FOREIGN KEY (vacancy_id)   REFERENCES job_vacancies(id),
            FOREIGN KEY (referred_by)  REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS referral_requests (
            id           INTEGER  PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER  NOT NULL,
            message      TEXT,
            status       TEXT     DEFAULT 'pending',
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewed_by  INTEGER,
            reviewed_at  DATETIME,
            notes        TEXT,
            FOREIGN KEY (applicant_id) REFERENCES applicants(id),
            FOREIGN KEY (reviewed_by)  REFERENCES users(id)
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
                peis_reg_date      DATE,
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
    if 'peis_reg_date' not in acols:
        db.execute('ALTER TABLE applicants ADD COLUMN peis_reg_date DATE')
    if 'user_id' not in acols:
        db.execute('ALTER TABLE applicants ADD COLUMN user_id INTEGER REFERENCES users(id)')

    vcols = [r[1] for r in db.execute("PRAGMA table_info(job_vacancies)").fetchall()]
    if 'employer_id' not in vcols:
        db.execute('ALTER TABLE job_vacancies ADD COLUMN employer_id INTEGER REFERENCES users(id)')

    ucols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
    if 'role' not in ucols:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'staff'")

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

def get_recommendations(educ_level, preferred_position, skills, work_experience, vacancies):
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
        vac_by_cat.setdefault(v['occupational_category'], []).append({
            'id':       v['id'],
            'title':    v['job_title'],
            'employer': v['employer_name'],
        })
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

def staff_required(f):
    return role_required(ROLE_ADMIN, ROLE_STAFF)(f)

def admin_required(f):
    return role_required(ROLE_ADMIN)(f)

def employer_required(f):
    return role_required(ROLE_EMPLOYER)(f)

def jobseeker_required(f):
    return role_required(ROLE_JOBSEEKER)(f)

def _role_home():
    role = session.get('role', ROLE_STAFF)
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
    pending_requests_count = 0
    pending_employers_count = 0
    if session.get('role') in (ROLE_ADMIN, ROLE_STAFF):
        try:
            db = get_db()
            pending_requests_count = db.execute(
                "SELECT COUNT(*) FROM referral_requests WHERE status='pending'"
            ).fetchone()[0]
            pending_employers_count = db.execute(
                "SELECT COUNT(*) FROM employers WHERE is_approved=0"
            ).fetchone()[0]
        except Exception:
            pass
    return {
        'pipeline_loaded':         pipeline is not None,
        'session_role':            session.get('role', ''),
        'pending_requests_count':  pending_requests_count,
        'pending_employers_count': pending_employers_count,
    }

# ── TEMPLATE FILTERS ──────────────────────────────────────────────────────────
_PHT = timedelta(hours=8)

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
    conds, params = ['is_active=1'], []
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
                session['role']      = user['role'] or ROLE_STAFF
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
    if request.method == 'POST':
        f        = request.form
        username = f.get('username', '').strip()
        email    = f.get('email', '').strip()
        pw       = f.get('password', '')
        conf     = f.get('confirm_password', '')
        first    = f.get('first_name', '').strip()
        last     = f.get('last_name', '').strip()

        errs = []
        if not all([username, email, pw, first, last]):
            errs.append('All required fields must be filled.')
        if pw != conf:
            errs.append('Passwords do not match.')
        if len(pw) < 8:
            errs.append('Password must be at least 8 characters.')
        if errs:
            for e in errs:
                flash(e, 'danger')
            return render_template('auth/register_jobseeker.html',
                                   educ_levels=EDUC_LEVELS, form=f,
                                   barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
                                   barangay_district_map=BARANGAY_DISTRICT,
                                   positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
                                   work_exp_list=WORK_EXPERIENCE_LIST)
        db = get_db()
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
                     skills, work_experience, user_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                first, last,
                f.get('sex', ''),
                int(age) if age.isdigit() else None,
                barangay,
                barangay_to_district(barangay),
                'Unemployed',
                0,
                educ, preferred, skills, work_exp,
                uid,
            ))
            db.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('auth/register_jobseeker.html',
                           educ_levels=EDUC_LEVELS, form={},
                           barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
                           barangay_district_map=BARANGAY_DISTRICT,
                           positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
                           work_exp_list=WORK_EXPERIENCE_LIST)

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
            flash('Employer account submitted! PESO staff will review and approve your registration.', 'success')
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
                'FROM job_vacancies WHERE is_active=1'
            ).fetchall()
            recs = get_recommendations(
                ap['educ_level'], ap['preferred_position'],
                ap['skills'], ap['work_experience'] or '',
                [dict(v) for v in vacancies]
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
        flash('Profile not found. Contact PESO staff.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    if request.method == 'POST':
        f   = request.form
        age = f.get('age', '').strip()
        brgy = f.get('barangay', '').strip()
        db.execute('''
            UPDATE applicants SET sex=?, age=?, barangay=?, district=?,
                employment_status=?, is_pwd=?, educ_level=?,
                preferred_position=?, skills=?, work_experience=?
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
    if ap and ap['educ_level'] and ap['preferred_position'] and ap['skills']:
        if pipeline:
            vacancies = db.execute(
                'SELECT id, employer_name, job_title, occupational_category '
                'FROM job_vacancies WHERE is_active=1'
            ).fetchall()
            results = get_recommendations(
                ap['educ_level'], ap['preferred_position'],
                ap['skills'], ap['work_experience'] or '',
                [dict(v) for v in vacancies]
            )
    return render_template('jobseeker/recommendations.html',
                           ap=ap, results=results,
                           pipeline_loaded=pipeline is not None)

@app.route('/jobseeker/referrals')
@jobseeker_required
def jobseeker_referrals():
    db = get_db()
    ap = _get_my_applicant()
    referrals = []
    my_request = None
    if ap:
        referrals = db.execute('''
            SELECT r.*, jv.job_title, jv.employer_name, jv.occupational_category,
                   u.full_name as referred_by_name
            FROM referrals r
            JOIN job_vacancies jv ON r.vacancy_id = jv.id
            JOIN users u ON r.referred_by = u.id
            WHERE r.applicant_id = ?
            ORDER BY r.referred_at DESC
        ''', (ap['id'],)).fetchall()
        my_request = db.execute(
            "SELECT * FROM referral_requests WHERE applicant_id=? ORDER BY requested_at DESC LIMIT 1",
            (ap['id'],)
        ).fetchone()
    return render_template('jobseeker/referrals.html', ap=ap,
                           referrals=referrals, my_request=my_request)

@app.route('/jobseeker/request-referral', methods=['POST'])
@jobseeker_required
def jobseeker_request_referral():
    ap = _get_my_applicant()
    if not ap:
        flash('Profile not found.', 'danger')
        return redirect(url_for('jobseeker_dashboard'))
    if not ap['educ_level'] or not ap['preferred_position'] or not ap['skills']:
        flash('Please complete your profile (education level, preferred position, and skills) before requesting a referral.', 'warning')
        return redirect(url_for('jobseeker_profile'))
    db = get_db()
    existing = db.execute(
        "SELECT id FROM referral_requests WHERE applicant_id=? AND status IN ('pending','reviewing')",
        (ap['id'],)
    ).fetchone()
    if existing:
        flash('You already have a pending referral request. Please wait for PESO staff to review it.', 'info')
        return redirect(url_for('jobseeker_referrals'))
    message = request.form.get('message', '').strip()
    db.execute(
        'INSERT INTO referral_requests (applicant_id, message) VALUES (?,?)',
        (ap['id'], message)
    )
    db.commit()
    flash('Referral request submitted! PESO staff will review your profile and get back to you.', 'success')
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
    hired = db.execute(
        "SELECT COUNT(*) FROM referrals r "
        "JOIN job_vacancies jv ON r.vacancy_id=jv.id "
        "WHERE jv.employer_id=? AND r.status='hired'",
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
                           hired=hired, recent_referrals=recent_referrals)

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
        f'SELECT * FROM job_vacancies WHERE {" AND ".join(conds)} ORDER BY created_at DESC',
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
        if not f.get('job_title') or not f.get('occupational_category'):
            flash('Job title and occupational category are required.', 'danger')
            return render_template('employer/vacancy_form.html', emp=emp,
                                   vacancy=f, categories=CATEGORY_LIST, action='add')
        get_db().execute(
            'INSERT INTO job_vacancies (employer_name, job_title, occupational_category, '
            'is_local, employer_id) VALUES (?,?,?,?,?)',
            (emp['company_name'], f.get('job_title', '').strip(),
             f.get('occupational_category', ''),
             1 if f.get('is_local', '1') == '1' else 0,
             session['user_id'])
        )
        get_db().commit()
        flash('Job vacancy posted.', 'success')
        return redirect(url_for('employer_vacancies'))
    return render_template('employer/vacancy_form.html', emp=emp,
                           vacancy=None, categories=CATEGORY_LIST, action='add')

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
        db.execute(
            'UPDATE job_vacancies SET job_title=?, occupational_category=?, is_local=? WHERE id=?',
            (f.get('job_title', '').strip(), f.get('occupational_category', ''),
             1 if f.get('is_local', '1') == '1' else 0, vid)
        )
        db.commit()
        flash('Vacancy updated.', 'success')
        return redirect(url_for('employer_vacancies'))
    return render_template('employer/vacancy_form.html', emp=emp,
                           vacancy=dict(v), categories=CATEGORY_LIST, action='edit')

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

@app.route('/employer/referrals/<int:rid>/outcome', methods=['POST'])
@employer_required
def employer_referral_outcome(rid):
    outcome = request.form.get('outcome', '')
    if outcome not in ('hired', 'not_hired'):
        flash('Invalid outcome.', 'danger')
        return redirect(url_for('employer_referred'))
    db = get_db()
    # Verify this referral belongs to a vacancy owned by this employer
    r = db.execute(
        'SELECT r.id FROM referrals r '
        'JOIN job_vacancies jv ON r.vacancy_id=jv.id '
        'WHERE r.id=? AND jv.employer_id=?',
        (rid, session['user_id'])
    ).fetchone()
    if r:
        db.execute('UPDATE referrals SET status=? WHERE id=?', (outcome, rid))
        db.commit()
        flash('Hiring outcome recorded.', 'success')
    else:
        flash('Referral not found.', 'danger')
    return redirect(url_for('employer_referred'))

# ── HOME / OVERVIEW (staff) ──────────────────────────────────────────────────
@app.route('/home')
@staff_required
def home():
    db = get_db()
    total_applicants = db.execute(
        'SELECT COUNT(*) FROM applicants WHERE is_archived=0'
    ).fetchone()[0]
    active_vacancies = db.execute(
        'SELECT COUNT(*) FROM job_vacancies WHERE is_active=1'
    ).fetchone()[0]
    total_employers = db.execute(
        'SELECT COUNT(DISTINCT employer_name) FROM job_vacancies WHERE is_active=1'
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

# ── RECOMMENDATION ────────────────────────────────────────────────────────────
@app.route('/recommendation')
@staff_required
def recommendation():
    db = get_db()
    applicants = db.execute(
        'SELECT id, first_name, last_name, educ_level, preferred_position, skills, work_experience '
        'FROM applicants WHERE is_archived = 0 ORDER BY last_name, first_name'
    ).fetchall()
    results       = session.pop('rec_results', None)
    input_profile = session.pop('rec_input', None)
    sel_applicant = session.pop('rec_applicant', None)
    preselect_id  = request.args.get('applicant_id')
    return render_template('recommendation.html',
                           applicants=applicants,
                           results=results,
                           input_profile=input_profile,
                           sel_applicant=sel_applicant,
                           preselect_id=preselect_id,
                           pipeline_loaded=pipeline is not None)

@app.route('/recommendation/generate', methods=['POST'])
@staff_required
def generate_recommendation():
    db           = get_db()
    mode         = request.form.get('mode', 'select')
    applicant_id = request.form.get('applicant_id')
    sel_applicant = None

    if mode == 'select' and applicant_id:
        ap = db.execute('SELECT * FROM applicants WHERE id = ? AND is_archived = 0',
                        (applicant_id,)).fetchone()
        if not ap:
            flash('Applicant not found.', 'danger')
            return redirect(url_for('recommendation'))
        educ_level         = ap['educ_level']
        preferred_position = ap['preferred_position']
        skills             = ap['skills']
        work_experience    = ap['work_experience'] or ''
        sel_applicant = {
            'id':         ap['id'],
            'full_name':  f"{ap['first_name']} {ap['last_name']}",
            'educ_level': ap['educ_level'],
            'preferred_position': ap['preferred_position'],
            'skills':     ap['skills'],
            'work_experience': ap['work_experience'] or '',
        }
    else:
        educ_level         = request.form.get('educ_level', '').strip()
        preferred_position = request.form.get('preferred_position', '').strip()
        skills             = request.form.get('skills', '').strip()
        work_experience    = request.form.get('work_experience', '').strip()
        applicant_id       = None

    if not educ_level or not preferred_position or not skills:
        flash('Education level, preferred position, and skills are required.', 'warning')
        return redirect(url_for('recommendation'))

    vacancies = db.execute(
        'SELECT id, employer_name, job_title, occupational_category '
        'FROM job_vacancies WHERE is_active = 1'
    ).fetchall()

    if not vacancies:
        flash('No active job vacancies found. Please add vacancies first.', 'warning')
        return redirect(url_for('recommendation'))

    if pipeline is None:
        flash('Recommendation engine is not available. The ML pipeline file was not found.', 'danger')
        return redirect(url_for('recommendation'))

    results = get_recommendations(educ_level, preferred_position, skills, work_experience,
                                  [dict(v) for v in vacancies])

    if applicant_id:
        for cat in results:
            for vac in cat['vacancies']:
                db.execute(
                    'INSERT INTO recommendations '
                    '(applicant_id,vacancy_id,suitability_score,rank,generated_by) VALUES (?,?,?,?,?)',
                    (applicant_id, vac['id'], cat['suitability_score'], cat['rank'], session['user_id'])
                )
        db.commit()

    session['rec_results']   = results
    session['rec_input']     = {
        'educ_level': educ_level,
        'preferred_position': preferred_position,
        'skills': skills,
        'work_experience': work_experience,
    }
    session['rec_applicant'] = sel_applicant
    return redirect(url_for('recommendation'))

# ── ANALYTICS ─────────────────────────────────────────────────────────────────
@app.route('/analytics')
@staff_required
def analytics():
    return render_template('analytics.html')

@app.route('/api/analytics')
@staff_required
def api_analytics():
    db = get_db()
    date_from = request.args.get('date_from', '').strip()
    date_to   = request.args.get('date_to', '').strip()
    dp = []
    df_sql = ''
    if date_from:
        df_sql += ' AND peis_reg_date >= ?'
        dp.append(date_from)
    if date_to:
        df_sql += ' AND peis_reg_date <= ?'
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
@staff_required
def applicants_list():
    db = get_db()
    search    = request.args.get('search', '').strip()
    archived  = request.args.get('archived', '0') == '1'
    status    = request.args.get('status', 'all')
    district  = request.args.get('district', '')
    view      = request.args.get('view', 'card')
    page      = max(1, request.args.get('page', 1, type=int) or 1)
    per_page  = APPLICANTS_PER_PAGE

    where  = ['is_archived=?']
    params = [1 if archived else 0]
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
                           search=search, archived=archived, status=status,
                           district=district, view=view, page=page, pages=pages,
                           total=total)

@app.route('/applicants/register', methods=['GET', 'POST'])
@staff_required
def applicant_register():
    if request.method == 'POST':
        f = request.form
        if not f.get('first_name') or not f.get('last_name') or \
           not f.get('educ_level') or not f.get('preferred_position') or not f.get('skills'):
            flash('First name, last name, education level, preferred position, and skills are required.', 'danger')
            return render_template('applicants/form.html', applicant=f,
                                   educ_levels=EDUC_LEVELS, action='register')
        db = get_db()
        age = f.get('age', '').strip()
        peis_reg_date = f.get('peis_reg_date', '').strip() or None
        db.execute('''
            INSERT INTO applicants (first_name,last_name,sex,age,barangay,district,
                employment_status,is_pwd,educ_level,preferred_position,skills,work_experience,
                peis_reg_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            f.get('first_name','').strip(), f.get('last_name','').strip(),
            f.get('sex',''), int(age) if age.isdigit() else None,
            f.get('barangay','').strip(), f.get('district',''),
            f.get('employment_status','Unemployed'),
            1 if f.get('is_pwd') else 0,
            f.get('educ_level',''), f.get('preferred_position','').strip(),
            f.get('skills','').strip(), f.get('work_experience','').strip(),
            peis_reg_date,
        ))
        db.commit()
        new_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        flash('Applicant registered successfully.', 'success')
        if f.get('recommend_now'):
            return redirect(url_for('recommendation') + f'?applicant_id={new_id}')
        return redirect(url_for('applicants_list'))
    return render_template('applicants/form.html', applicant=None,
                           educ_levels=EDUC_LEVELS, action='register',
                           barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
                           barangay_district_map=BARANGAY_DISTRICT,
                           positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
                           work_exp_list=WORK_EXPERIENCE_LIST)

@app.route('/applicants/<int:aid>/edit', methods=['GET', 'POST'])
@staff_required
def applicant_edit(aid):
    db = get_db()
    ap = db.execute('SELECT * FROM applicants WHERE id=?', (aid,)).fetchone()
    if not ap:
        flash('Applicant not found.', 'danger')
        return redirect(url_for('applicants_list'))
    if request.method == 'POST':
        f = request.form
        age = f.get('age', '').strip()
        peis_reg_date = f.get('peis_reg_date', '').strip() or None
        db.execute('''
            UPDATE applicants SET first_name=?,last_name=?,sex=?,age=?,barangay=?,district=?,
                employment_status=?,is_pwd=?,educ_level=?,preferred_position=?,skills=?,
                work_experience=?,peis_reg_date=? WHERE id=?
        ''', (
            f.get('first_name','').strip(), f.get('last_name','').strip(),
            f.get('sex',''), int(age) if age.isdigit() else None,
            f.get('barangay','').strip(), f.get('district',''),
            f.get('employment_status','Unemployed'),
            1 if f.get('is_pwd') else 0,
            f.get('educ_level',''), f.get('preferred_position','').strip(),
            f.get('skills','').strip(), f.get('work_experience','').strip(),
            peis_reg_date, aid,
        ))
        db.commit()
        flash('Applicant updated.', 'success')
        return redirect(url_for('applicants_list'))
    return render_template('applicants/form.html', applicant=dict(ap),
                           educ_levels=EDUC_LEVELS, action='edit',
                           barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
                           barangay_district_map=BARANGAY_DISTRICT,
                           positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
                           work_exp_list=WORK_EXPERIENCE_LIST)

@app.route('/applicants/<int:aid>/archive', methods=['POST'])
@staff_required
def applicant_archive(aid):
    get_db().execute('UPDATE applicants SET is_archived=1 WHERE id=?', (aid,))
    get_db().commit()
    flash('Applicant archived.', 'success')
    return redirect(url_for('applicants_list'))

@app.route('/applicants/<int:aid>/restore', methods=['POST'])
@staff_required
def applicant_restore(aid):
    get_db().execute('UPDATE applicants SET is_archived=0 WHERE id=?', (aid,))
    get_db().commit()
    flash('Applicant restored.', 'success')
    return redirect(url_for('applicants_list') + '?archived=1')

@app.route('/applicants/<int:aid>/delete', methods=['POST'])
@staff_required
def applicant_delete(aid):
    db = get_db()
    ap = db.execute('SELECT first_name, last_name FROM applicants WHERE id=?', (aid,)).fetchone()
    if not ap:
        flash('Applicant not found.', 'danger')
        return redirect(url_for('applicants_list'))
    db.execute('DELETE FROM recommendations WHERE applicant_id=?', (aid,))
    db.execute('DELETE FROM referrals WHERE applicant_id=?', (aid,))
    db.execute('DELETE FROM applicants WHERE id=?', (aid,))
    db.commit()
    flash(f'Applicant {ap["first_name"]} {ap["last_name"]} has been permanently deleted.', 'success')
    return redirect(url_for('applicants_list'))

@app.route('/applicants/upload', methods=['GET', 'POST'])
@staff_required
def applicants_upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXT:
            flash('Only XLSX or XLS files are accepted.', 'danger')
            return redirect(request.url)
        fname = secure_filename(file.filename)
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        file.save(fpath)
        try:
            try:
                df = pd.read_excel(fpath, header=2)
                if 'EDUC LEVEL' not in [c.strip().upper() for c in df.columns]:
                    df = pd.read_excel(fpath, header=0)
            except Exception:
                df = pd.read_excel(fpath, header=0)
            df.columns = [str(c).strip().upper() for c in df.columns]
            db = get_db()
            ok, skip, incomplete = 0, 0, 0
            for idx, row in df.iterrows():
                try:
                    rec = normalize_peis_row(row)
                    if rec is None:
                        skip += 1
                        continue
                    if not rec['skills'] or not rec['educ_level'] or not rec['preferred_position']:
                        incomplete += 1
                    db.execute('''
                        INSERT INTO applicants
                            (first_name,last_name,educ_level,preferred_position,skills,
                             work_experience,sex,employment_status,barangay,district,
                             age,is_pwd,peis_reg_date)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        rec['first_name'], rec['last_name'], rec['educ_level'],
                        rec['preferred_position'], rec['skills'], rec['work_experience'],
                        rec['sex'], rec['employment_status'], rec['barangay'],
                        rec['district'], rec['age'], rec['is_pwd'], rec['peis_reg_date'],
                    ))
                    ok += 1
                except Exception:
                    skip += 1
            db.commit()
            flash(f'Upload complete: {ok} applicant(s) imported'
                  + (f', {skip} blank row(s) skipped' if skip else '') + '.',
                  'success' if ok > 0 else 'warning')
            if incomplete:
                flash(f'{incomplete} applicant(s) were imported with an incomplete profile '
                      '(missing skills, education, or preferred position). Please complete '
                      'these records before generating recommendations.', 'warning')
        except Exception as e:
            flash(f'Error reading file: {e}', 'danger')
        finally:
            try:
                os.remove(fpath)
            except Exception:
                pass
        return redirect(url_for('applicants_list'))
    return render_template('applicants/upload.html')

# ── REFERRALS (staff) ─────────────────────────────────────────────────────────
@app.route('/referrals')
@staff_required
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
        JOIN users u          ON r.referred_by  = u.id
        {where}
        ORDER BY r.referred_at DESC
    ''', params).fetchall()
    return render_template('staff/referrals.html', referrals=referrals,
                           status=status, search=search)

@app.route('/referrals/issue', methods=['POST'])
@staff_required
def referral_issue():
    applicant_id = request.form.get('applicant_id')
    vacancy_id   = request.form.get('vacancy_id')
    notes        = request.form.get('notes', '').strip()

    if not applicant_id or not vacancy_id:
        flash('Applicant and vacancy are required to issue a referral.', 'danger')
        return redirect(url_for('recommendation'))

    db = get_db()
    # Verify applicant and vacancy exist
    ap = db.execute('SELECT first_name, last_name FROM applicants WHERE id=?', (applicant_id,)).fetchone()
    jv = db.execute('SELECT job_title, employer_name FROM job_vacancies WHERE id=?', (vacancy_id,)).fetchone()
    if not ap or not jv:
        flash('Applicant or vacancy not found.', 'danger')
        return redirect(url_for('recommendation'))

    # Prevent duplicate active referrals
    existing = db.execute(
        "SELECT id FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status NOT IN ('not_hired')",
        (applicant_id, vacancy_id)
    ).fetchone()
    if existing:
        flash(f'{ap["first_name"]} {ap["last_name"]} has already been referred to "{jv["job_title"]}" at {jv["employer_name"]}.', 'warning')
        return redirect(url_for('recommendation'))

    db.execute(
        'INSERT INTO referrals (applicant_id, vacancy_id, referred_by, notes) VALUES (?,?,?,?)',
        (applicant_id, vacancy_id, session['user_id'], notes)
    )
    db.commit()
    flash(f'Referral issued: {ap["first_name"]} {ap["last_name"]} → {jv["job_title"]} ({jv["employer_name"]}).', 'success')
    return redirect(url_for('recommendation'))

@app.route('/referrals/<int:rid>/cancel', methods=['POST'])
@staff_required
def referral_cancel(rid):
    db = get_db()
    r  = db.execute('SELECT * FROM referrals WHERE id=?', (rid,)).fetchone()
    if not r:
        flash('Referral not found.', 'danger')
        return redirect(url_for('referrals_list'))
    db.execute("UPDATE referrals SET status='cancelled' WHERE id=?", (rid,))
    db.commit()
    flash('Referral cancelled.', 'success')
    return redirect(url_for('referrals_list'))

# ── REFERRAL REQUESTS (staff) ──────────────────────────────────────────────────
@app.route('/staff/referral-requests')
@staff_required
def staff_referral_requests():
    db     = get_db()
    status = request.args.get('status', 'pending')
    conds, params = [], []
    if status != 'all':
        conds.append('rr.status=?')
        params.append(status)
    where = ('WHERE ' + ' AND '.join(conds)) if conds else ''
    reqs = db.execute(f'''
        SELECT rr.*,
               a.first_name, a.last_name, a.preferred_position, a.educ_level, a.skills,
               u.full_name as reviewer_name
        FROM referral_requests rr
        JOIN applicants a ON rr.applicant_id = a.id
        LEFT JOIN users u ON rr.reviewed_by = u.id
        {where}
        ORDER BY rr.requested_at DESC
    ''', params).fetchall()
    counts = {
        'pending':   db.execute("SELECT COUNT(*) FROM referral_requests WHERE status='pending'").fetchone()[0],
        'reviewing': db.execute("SELECT COUNT(*) FROM referral_requests WHERE status='reviewing'").fetchone()[0],
        'referred':  db.execute("SELECT COUNT(*) FROM referral_requests WHERE status='referred'").fetchone()[0],
        'rejected':  db.execute("SELECT COUNT(*) FROM referral_requests WHERE status='rejected'").fetchone()[0],
    }
    return render_template('staff/referral_requests.html',
                           reqs=reqs, status=status, counts=counts)

@app.route('/staff/referral-requests/<int:rid>/review')
@staff_required
def staff_review_request(rid):
    db  = get_db()
    req = db.execute(
        'SELECT rr.*, a.first_name, a.last_name '
        'FROM referral_requests rr JOIN applicants a ON rr.applicant_id=a.id '
        'WHERE rr.id=?', (rid,)
    ).fetchone()
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('staff_referral_requests'))
    if req['status'] == 'pending':
        db.execute(
            "UPDATE referral_requests SET status='reviewing', reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP WHERE id=?",
            (session['user_id'], rid)
        )
        db.commit()
    ap = db.execute('SELECT * FROM applicants WHERE id=?', (req['applicant_id'],)).fetchone()
    results = []
    if ap and ap['educ_level'] and ap['preferred_position'] and ap['skills'] and pipeline:
        vacancies = db.execute(
            'SELECT id, employer_name, job_title, occupational_category '
            'FROM job_vacancies WHERE is_active=1'
        ).fetchall()
        if vacancies:
            results = get_recommendations(
                ap['educ_level'], ap['preferred_position'],
                ap['skills'], ap['work_experience'] or '',
                [dict(v) for v in vacancies]
            )
    return render_template('staff/review_request.html',
                           req=dict(req), ap=dict(ap) if ap else None,
                           results=results, pipeline_loaded=pipeline is not None)

@app.route('/staff/referral-requests/<int:rid>/refer', methods=['POST'])
@staff_required
def staff_refer_from_request(rid):
    db         = get_db()
    vacancy_id = request.form.get('vacancy_id')
    notes      = request.form.get('notes', '').strip()
    req = db.execute('SELECT * FROM referral_requests WHERE id=?', (rid,)).fetchone()
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('staff_referral_requests'))
    if not vacancy_id:
        flash('No vacancy selected.', 'danger')
        return redirect(url_for('staff_review_request', rid=rid))
    ap = db.execute('SELECT first_name, last_name FROM applicants WHERE id=?',
                    (req['applicant_id'],)).fetchone()
    jv = db.execute('SELECT job_title, employer_name FROM job_vacancies WHERE id=?',
                    (vacancy_id,)).fetchone()
    if not ap or not jv:
        flash('Applicant or vacancy not found.', 'danger')
        return redirect(url_for('staff_review_request', rid=rid))
    existing = db.execute(
        "SELECT id FROM referrals WHERE applicant_id=? AND vacancy_id=? AND status NOT IN ('not_hired','cancelled')",
        (req['applicant_id'], vacancy_id)
    ).fetchone()
    if existing:
        flash(f'{ap["first_name"]} {ap["last_name"]} is already actively referred to "{jv["job_title"]}".', 'warning')
        return redirect(url_for('staff_review_request', rid=rid))
    db.execute(
        'INSERT INTO referrals (applicant_id, vacancy_id, referred_by, notes) VALUES (?,?,?,?)',
        (req['applicant_id'], vacancy_id, session['user_id'], notes)
    )
    db.execute(
        "UPDATE referral_requests SET status='referred', reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP WHERE id=?",
        (session['user_id'], rid)
    )
    db.commit()
    flash(f'Referral issued: {ap["first_name"]} {ap["last_name"]} → {jv["job_title"]} ({jv["employer_name"]}).', 'success')
    return redirect(url_for('staff_referral_requests'))

@app.route('/staff/referral-requests/<int:rid>/reject', methods=['POST'])
@staff_required
def staff_reject_request(rid):
    db    = get_db()
    notes = request.form.get('notes', '').strip()
    req   = db.execute('SELECT * FROM referral_requests WHERE id=?', (rid,)).fetchone()
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('staff_referral_requests'))
    db.execute(
        "UPDATE referral_requests SET status='rejected', reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP, notes=? WHERE id=?",
        (session['user_id'], notes, rid)
    )
    db.commit()
    flash('Referral request rejected.', 'warning')
    return redirect(url_for('staff_referral_requests'))

# ── VACANCIES ─────────────────────────────────────────────────────────────────
@app.route('/vacancies')
@staff_required
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
    q = 'SELECT * FROM job_vacancies'
    if conds:
        q += ' WHERE ' + ' AND '.join(conds)
    q += ' ORDER BY created_at DESC'
    vacancies = db.execute(q, params).fetchall()
    view = request.args.get('view', 'card')
    return render_template('vacancies/list.html', vacancies=vacancies,
                           search=search, status=status, view=view)

@app.route('/vacancies/add', methods=['GET', 'POST'])
@staff_required
def vacancy_add():
    if request.method == 'POST':
        f = request.form
        if not f.get('employer_name') or not f.get('job_title') or not f.get('occupational_category'):
            flash('Employer name, job title, and occupational category are required.', 'danger')
            return render_template('vacancies/form.html', vacancy=f,
                                   categories=CATEGORY_LIST, action='add')
        get_db().execute(
            'INSERT INTO job_vacancies (employer_name,job_title,occupational_category,is_local) VALUES (?,?,?,?)',
            (f.get('employer_name','').strip(), f.get('job_title','').strip(),
             f.get('occupational_category',''), 1 if f.get('is_local','1')=='1' else 0)
        )
        get_db().commit()
        flash('Job vacancy added.', 'success')
        return redirect(url_for('vacancies_list'))
    return render_template('vacancies/form.html', vacancy=None,
                           categories=CATEGORY_LIST, action='add')

@app.route('/vacancies/<int:vid>/edit', methods=['GET', 'POST'])
@staff_required
def vacancy_edit(vid):
    db = get_db()
    v  = db.execute('SELECT * FROM job_vacancies WHERE id=?', (vid,)).fetchone()
    if not v:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('vacancies_list'))
    if request.method == 'POST':
        f = request.form
        db.execute(
            'UPDATE job_vacancies SET employer_name=?,job_title=?,occupational_category=?,is_local=? WHERE id=?',
            (f.get('employer_name','').strip(), f.get('job_title','').strip(),
             f.get('occupational_category',''), 1 if f.get('is_local','1')=='1' else 0, vid)
        )
        db.commit()
        flash('Vacancy updated.', 'success')
        return redirect(url_for('vacancies_list'))
    return render_template('vacancies/form.html', vacancy=dict(v),
                           categories=CATEGORY_LIST, action='edit')

@app.route('/vacancies/<int:vid>/toggle', methods=['POST'])
@staff_required
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
@staff_required
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
    db     = get_db()
    status = request.args.get('status', 'all')
    role   = request.args.get('role', 'staff')
    view   = request.args.get('view', 'card')

    role_cond = {
        'staff':     "role IN ('admin','staff')",
        'employer':  "role = 'employer'",
        'jobseeker': "role = 'jobseeker'",
        'all':       "1=1",
    }.get(role, "role IN ('admin','staff')")

    status_cond = ''
    if status == 'active':
        status_cond = ' AND is_active=1'
    elif status == 'inactive':
        status_cond = ' AND is_active=0'

    users = get_db().execute(
        f'SELECT * FROM users WHERE {role_cond}{status_cond} ORDER BY role, full_name'
    ).fetchall()

    counts = {
        'staff':     db.execute("SELECT COUNT(*) FROM users WHERE role IN ('admin','staff')").fetchone()[0],
        'employer':  db.execute("SELECT COUNT(*) FROM users WHERE role='employer'").fetchone()[0],
        'jobseeker': db.execute("SELECT COUNT(*) FROM users WHERE role='jobseeker'").fetchone()[0],
    }
    return render_template('users/list.html', users=users, status=status,
                           role=role, view=view, counts=counts)

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
                    (name, user, mail, generate_password_hash(pw), ROLE_STAFF)
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

    ep = None  # employer profile
    ap = None  # applicant/jobseeker profile
    if u['role'] == ROLE_EMPLOYER:
        row = db.execute('SELECT * FROM employers WHERE user_id=?', (uid,)).fetchone()
        ep = dict(row) if row else {}
    elif u['role'] == ROLE_JOBSEEKER:
        row = db.execute('SELECT * FROM applicants WHERE user_id=?', (uid,)).fetchone()
        ap = dict(row) if row else {}

    def _render(user_override=None):
        return render_template('users/form.html',
            user=user_override or dict(u), action='edit',
            employer_profile=ep, applicant_profile=ap,
            educ_levels=EDUC_LEVELS,
            barangays=sorted(BARANGAY_DISTRICT.keys(), key=str.title),
            barangay_district_map=BARANGAY_DISTRICT,
            positions=PREFERRED_POSITIONS, skills_list=SKILLS_LIST,
            work_exp_list=WORK_EXPERIENCE_LIST)

    if request.method == 'POST':
        f        = request.form
        name     = f.get('full_name','').strip()
        mail     = f.get('email','').strip()
        username = f.get('username','').strip()
        pw       = f.get('new_password','')
        new_role = f.get('role', u['role'])
        if u['role'] == ROLE_ADMIN and new_role != ROLE_ADMIN:
            admin_count = db.execute(
                "SELECT COUNT(*) FROM users WHERE role='admin'"
            ).fetchone()[0]
            if admin_count <= 1:
                flash('Cannot remove admin role — at least one admin must exist.', 'danger')
                return _render()
        if pw and len(pw) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return _render()
        try:
            if pw:
                db.execute('UPDATE users SET full_name=?,username=?,email=?,password_hash=?,role=? WHERE id=?',
                           (name, username, mail, generate_password_hash(pw), new_role, uid))
            else:
                db.execute('UPDATE users SET full_name=?,username=?,email=?,role=? WHERE id=?',
                           (name, username, mail, new_role, uid))

            if u['role'] == ROLE_EMPLOYER:
                company  = f.get('company_name', '').strip()
                contact  = f.get('contact_person', '').strip()
                phone    = f.get('phone', '').strip()
                address  = f.get('address', '').strip()
                if db.execute('SELECT id FROM employers WHERE user_id=?', (uid,)).fetchone():
                    db.execute(
                        'UPDATE employers SET company_name=?,contact_person=?,phone=?,address=? WHERE user_id=?',
                        (company, contact, phone, address, uid))
                else:
                    db.execute(
                        'INSERT INTO employers (user_id,company_name,contact_person,phone,address) VALUES (?,?,?,?,?)',
                        (uid, company, contact, phone, address))

            elif u['role'] == ROLE_JOBSEEKER:
                ap_row = db.execute('SELECT id FROM applicants WHERE user_id=?', (uid,)).fetchone()
                if ap_row:
                    db.execute('''
                        UPDATE applicants SET sex=?,age=?,barangay=?,district=?,
                            employment_status=?,is_pwd=?,educ_level=?,
                            preferred_position=?,skills=?,work_experience=?
                        WHERE user_id=?
                    ''', (
                        f.get('sex', ''),
                        f.get('age', '') or None,
                        f.get('barangay', '').strip(),
                        f.get('district', '').strip(),
                        f.get('employment_status', 'Unemployed'),
                        1 if f.get('is_pwd') else 0,
                        f.get('educ_level', ''),
                        f.get('preferred_position', '').strip(),
                        f.get('skills', '').strip(),
                        f.get('work_experience', '').strip(),
                        uid,
                    ))

            db.commit()
            flash('User updated.', 'success')
            return redirect(url_for('users_list', role=u['role']))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return _render()

TEMP_PASSWORDS = {
    ROLE_STAFF:     'Staff@1234',
    ROLE_EMPLOYER:  'Employer@1234',
    ROLE_JOBSEEKER: 'Seeker@1234',
}

@app.route('/users/<int:uid>/reset-password', methods=['POST'])
@admin_required
def user_reset_password(uid):
    db = get_db()
    u  = db.execute('SELECT full_name, role FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        flash('User not found.', 'danger')
        return redirect(url_for('users_list'))
    temp_pw = TEMP_PASSWORDS.get(u['role'])
    if not temp_pw:
        flash('Password reset is not available for this role.', 'danger')
        return redirect(url_for('user_edit', uid=uid))
    db.execute('UPDATE users SET password_hash=? WHERE id=?',
               (generate_password_hash(temp_pw), uid))
    db.commit()
    flash(f'Password for {u["full_name"]} has been reset to: {temp_pw}', 'success')
    return redirect(url_for('user_edit', uid=uid))

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

@app.route('/users/<int:uid>/toggle', methods=['POST'])
@admin_required
def user_toggle(uid):
    if uid == session['user_id']:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('users_list'))
    db = get_db()
    u  = db.execute('SELECT is_active FROM users WHERE id=?', (uid,)).fetchone()
    if u:
        db.execute('UPDATE users SET is_active=? WHERE id=?',
                   (0 if u['is_active'] else 1, uid))
        db.commit()
        flash('User status updated.', 'success')
    return redirect(url_for('users_list'))

@app.route('/users/login-history')
@staff_required
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

# ── STARTUP ───────────────────────────────────────────────────────────────────
init_db()
load_pipeline()

if __name__ == '__main__':
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("PESO CSJDM running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
