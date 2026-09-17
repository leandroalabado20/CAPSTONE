"""
PESO CSJDM Web-Based Data-Driven Job Recommendation System
Flask Application Entry Point

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

# Pagination
APPLICANTS_PER_PAGE = 24

# Icons used in the recommendation results UI (one per occupational category)
CAT_ICONS = {
    'Warehouse and Logistics':       'bi-box-seam',
    'Production and Manufacturing':  'bi-gear-fill',
    'Sales/Service/Retail':          'bi-shop',
    'Clerical and Administrative':   'bi-file-earmark-text-fill',
    'General Services and Security': 'bi-shield-fill',
}

# Age thresholds for Youth / Senior Citizen classification
YOUTH_AGE_MIN  = 15
YOUTH_AGE_MAX  = 30
SENIOR_AGE_MIN = 60

# ── PEIS IMPORT NORMALIZATION ──────────────────────────────────────────────────
# The PEIS export carries 40+ columns; only the 12 fields in FR-03 are stored.
# Every raw row is passed through normalize_peis_row() before insertion.

# Raw PEIS education strings → the 10 canonical EDUC_LEVELS.
EDUC_NORMALIZE = {
    # ── Elementary ────────────────────────────────────────────────────────────
    'GRADE I':                                        'Elementary Level',
    'GRADE II':                                       'Elementary Level',
    'GRADE III':                                      'Elementary Level',
    'GRADE IV':                                       'Elementary Level',
    'GRADE V':                                        'Elementary Level',
    'GRADE VI':                                       'Elementary Level',
    'ELEMENTARY GRADUATE':                            'Elementary Graduate',
    # ── High School ───────────────────────────────────────────────────────────
    'GRADE VII':                                      'High School Level',
    'GRADE VIII':                                     'High School Level',
    '1ST YEAR HIGH SCHOOL/GRADE VII (FOR K TO 12)':  'High School Level',
    '2ND YEAR HIGH SCHOOL/GRADE VIII (FOR K TO 12)': 'High School Level',
    '3RD YEAR HIGH SCHOOL/GRADE IX (FOR K TO 12)':   'High School Level',
    '4TH YEAR HIGH SCHOOL/GRADE X (FOR K TO 12)':    'High School Level',
    'HIGH SCHOOL GRADUATE':                           'High School Graduate',
    'SECONDARY (K-12)':                               'High School Graduate',
    'SECONDARY (NON K-12)':                           'High School Graduate',
    # ── Senior High School ────────────────────────────────────────────────────
    'GRADE XI (FOR K TO 12)':                         'Senior High School Level',
    'GRADE XII (FOR K TO 12)':                        'Senior High School Graduate',
    # ── College ───────────────────────────────────────────────────────────────
    '1ST YEAR COLLEGE LEVEL':                         'College Level',
    '2ND YEAR COLLEGE LEVEL':                         'College Level',
    '3RD YEAR COLLEGE LEVEL':                         'College Level',
    '4TH YEAR COLLEGE LEVEL':                         'College Level',
    '5TH YEAR COLLEGE LEVEL':                         'College Level',
    'COLLEGE GRADUATE':                               'College Graduate',
    'MASTERAL/POST GRADUATE':                         'College Graduate',
    'MASTERAL/POST GRADUATE LEVEL':                   'College Graduate',
    # ── Vocational / ALS ──────────────────────────────────────────────────────
    'VOCATIONAL GRADUATE':                            'Vocational',
    'VOCATIONAL UNDERGRADUATE':                       'Vocational',
    'ALS':                                            'ALS',
    'ALS (ALTERNATIVE LEARNING SYSTEM)':              'ALS',
}

# CSJDM barangay → council district.
# Complete list: 26 barangays in District 1, 36 barangays in District 2 (62 total).
# Source: Wikipedia – San Jose del Monte / csjdm.gov.ph
BARANGAY_DISTRICT = {
    # ── District 1 (26 barangays) ─────────────────────────────────────────────
    'POBLACION':                  'District 1',
    'POBLACION I':                'District 1',
    'FRANCISCO HOMES-GUIJO':      'District 1',
    'FRANCISCO HOMES-MULAWIN':    'District 1',
    'FRANCISCO HOMES-NARRA':      'District 1',
    'FRANCISCO HOMES-YAKAL':      'District 1',
    'GUMAOC EAST':                'District 1',
    'GUMAOC WEST':                'District 1',
    'GUMAOC CENTRAL':             'District 1',
    'GRACEVILLE':                 'District 1',
    'GAYA-GAYA':                  'District 1',
    'SANTO CRISTO':               'District 1',
    'TUNGKONG MANGGA':            'District 1',
    'DULONG BAYAN':               'District 1',
    'CIUDAD REAL':                'District 1',
    'MAHARLIKA':                  'District 1',
    'SAN MANUEL':                 'District 1',
    'KAYPIAN':                    'District 1',
    'SAN ISIDRO':                 'District 1',
    'SAN ROQUE':                  'District 1',
    'KAYBANBAN':                  'District 1',
    'PARADISE III':               'District 1',
    'MUZON':                      'District 1',
    'MUZON PROPER':               'District 1',
    'MUZON EAST':                 'District 1',
    'MUZON WEST':                 'District 1',
    'MUZON SOUTH':                'District 1',
    # ── District 2 (36 barangays) ─────────────────────────────────────────────
    'SAPANG PALAY':               'District 2',
    'SAPANG PALAY PROPER':        'District 2',
    'MINUYAN PROPER':             'District 2',
    'MINUYAN':                    'District 2',
    'MINUYAN I':                  'District 2',
    'MINUYAN II':                 'District 2',
    'MINUYAN III':                'District 2',
    'MINUYAN IV':                 'District 2',
    'MINUYAN V':                  'District 2',
    'BAGONG BUHAY':               'District 2',
    'BAGONG BUHAY I':             'District 2',
    'BAGONG BUHAY II':            'District 2',
    'BAGONG BUHAY III':           'District 2',
    'SAN MARTIN':                 'District 2',
    'SAN MARTIN I':               'District 2',
    'SAN MARTIN II':              'District 2',
    'SAN MARTIN III':             'District 2',
    'SAN MARTIN IV':              'District 2',
    'SAN MARTIN DE PORRES':       'District 2',
    'ST. MARTIN DE PORRES':       'District 2',
    'SANTA CRUZ':                 'District 2',
    'SANTA CRUZ I':               'District 2',
    'SANTA CRUZ II':              'District 2',
    'SANTA CRUZ III':             'District 2',
    'SANTA CRUZ IV':              'District 2',
    'SANTA CRUZ V':               'District 2',
    'FATIMA':                     'District 2',
    'FATIMA I':                   'District 2',
    'FATIMA II':                  'District 2',
    'FATIMA III':                 'District 2',
    'FATIMA IV':                  'District 2',
    'FATIMA V':                   'District 2',
    'CITRUS':                     'District 2',
    'SAN PEDRO':                  'District 2',
    'SAN RAFAEL':                 'District 2',
    'SAN RAFAEL I':               'District 2',
    'SAN RAFAEL II':              'District 2',
    'SAN RAFAEL III':             'District 2',
    'SAN RAFAEL IV':              'District 2',
    'SAN RAFAEL V':               'District 2',
    'ASSUMPTION':                 'District 2',
    'LAWANG PARI':                'District 2',
    'SANTO NIÑO':                 'District 2',
    'SANTO NIÑO I':               'District 2',
    'SANTO NIÑO II':              'District 2',
}


def normalize_educ(raw):
    """Map a raw PEIS education string to one of the 10 canonical levels ('' if unknown)."""
    return EDUC_NORMALIZE.get(re.sub(r'\s+', ' ', str(raw)).strip().upper(), '')


def barangay_to_district(raw):
    """Look up the council district for a barangay ('' if unknown)."""
    return BARANGAY_DISTRICT.get(re.sub(r'\s+', ' ', str(raw)).strip().upper(), '')


def parse_age(raw):
    """'46y 2mos' / '32' / 46.0 -> 46 (int); None if no digits."""
    m = re.search(r'\d+', str(raw))
    return int(m.group()) if m else None


def yn_to_int(raw):
    """'Yes'/'No' (any case) -> 1/0."""
    return 1 if str(raw).strip().lower() in ('yes', 'y', '1', 'true') else 0


def parse_peis_date(raw):
    """Pandas Timestamp / datetime / date string -> 'YYYY-MM-DD', or None."""
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
    """One raw PEIS row (dict of UPPER-CASE headers) -> clean dict of the 12 stored
    fields, or None only if the row is completely empty. Rows missing a required ML
    field (education / preferred position / skills) are still returned with that
    field left blank, so they can be imported and flagged for completion."""
    # Helper: safely get a PEIS column value as a stripped string
    get_col = lambda c: '' if pd.isna(row.get(c, '')) else str(row.get(c, '')).strip()

    first     = get_col('FIRSTNAME') or get_col('FIRST NAME')
    last      = get_col('LASTNAME')  or get_col('LAST NAME')
    educ      = normalize_educ(get_col('EDUC LEVEL'))
    preferred = get_col('PREFERRED POSITION')
    skills    = get_col('SKILLS')
    if not any((first, last, educ, preferred, skills)):
        return None                              # skip only truly empty / junk rows

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
            created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_archived        INTEGER  DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS job_vacancies (
            id                   INTEGER  PRIMARY KEY AUTOINCREMENT,
            employer_name        TEXT     NOT NULL,
            job_title            TEXT     NOT NULL,
            occupational_category TEXT    NOT NULL,
            is_local             INTEGER  DEFAULT 1,
            is_active            INTEGER  DEFAULT 1,
            created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
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
        CREATE TABLE IF NOT EXISTS login_logs (
            id         INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            username   TEXT,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            outcome    TEXT
        );
    ''')

    # Migrate an older applicants table to the lean schema (drops personal/admin
    # columns, adds age). Existing rows are preserved for the retained columns.
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

    # Add peis_reg_date to tables that predate this column.
    acols = [r[1] for r in db.execute("PRAGMA table_info(applicants)").fetchall()]
    if 'peis_reg_date' not in acols:
        db.execute('ALTER TABLE applicants ADD COLUMN peis_reg_date DATE')

    existing = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if existing == 0:
        db.execute(
            'INSERT INTO users (full_name, username, email, password_hash) VALUES (?, ?, ?, ?)',
            ('Administrator', 'admin', 'admin@peso.gov.ph', generate_password_hash('admin123'))
        )
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

    # Rank the 5 occupational categories by their predicted probability (descending)
    cat_scores = sorted(
        [(CATEGORIES[i], round(float(proba[i]), 4)) for i in range(len(CATEGORIES))],
        key=lambda x: x[1], reverse=True,
    )

    # Group active vacancies by occupational category
    vac_by_cat = {}
    for v in vacancies:
        vac_by_cat.setdefault(v['occupational_category'], []).append({
            'id':       v['id'],
            'title':    v['job_title'],
            'employer': v['employer_name'],
        })

    # One result entry per category (always all 5), in score order
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

def current_user():
    if 'user_id' in session:
        return get_db().execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return None

# ── CONTEXT PROCESSOR ─────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {'pipeline_loaded': pipeline is not None}

# ── TEMPLATE FILTERS ──────────────────────────────────────────────────────────
_PHT = timedelta(hours=8)  # SQLite CURRENT_TIMESTAMP is UTC; Philippines is UTC+8

@app.template_filter('friendly_dt')
def friendly_dt(value):
    """Format a SQLite UTC timestamp as Philippine Time (UTC+8)."""
    if not value:
        return ''
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(str(value), fmt) + _PHT
            return dt.strftime('%b %d, %Y · %I:%M %p').replace(' 0', ' ')
        except ValueError:
            continue
    return str(value)

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('home') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
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
                session['user_id']  = user['id']
                session['username'] = user['username']
                session['full_name']= user['full_name']
                db.execute('INSERT INTO login_logs (user_id,username,ip_address,outcome) VALUES (?,?,?,?)',
                           (user['id'], username, ip, 'success'))
                db.commit()
                return redirect(url_for('home'))
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
    return redirect(url_for('login'))

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
            return redirect(url_for('recommendation'))
    return render_template('settings/password.html', user=user)

# ── HOME / OVERVIEW ─────────────────────────────────────────────────────────
@app.route('/home')
@login_required
def home():
    db = get_db()

    # Summary counts
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

    # Last successful login for this user, excluding the current session's login
    # (the most recent success row is this session, so the 2nd most recent is the
    # actual previous login).
    last_login_row = db.execute(
        "SELECT timestamp FROM login_logs "
        "WHERE user_id=? AND outcome='success' "
        "ORDER BY timestamp DESC LIMIT 1 OFFSET 1",
        (session['user_id'],)
    ).fetchone()
    last_login = last_login_row['timestamp'] if last_login_row else None

    # Recent activity
    recent_applicants = db.execute(
        'SELECT id, first_name, last_name, preferred_position, created_at '
        'FROM applicants WHERE is_archived=0 '
        'ORDER BY created_at DESC, id DESC LIMIT 5'
    ).fetchall()
    # One row per (applicant, day): the first vacancy inserted for the top-ranked
    # category that session, so we don't show N rows for the same applicant.
    recent_recs = db.execute(
        'SELECT r.rank, r.suitability_score, r.recommended_at, '
        '       a.first_name, a.last_name, '
        '       jv.job_title, jv.employer_name '
        'FROM recommendations r '
        'JOIN applicants a      ON r.applicant_id = a.id '
        'JOIN job_vacancies jv  ON r.vacancy_id   = jv.id '
        'WHERE r.rank = 1 '
        '  AND r.id IN ('
        '    SELECT MIN(id) FROM recommendations '
        '    WHERE rank = 1 '
        '    GROUP BY applicant_id, date(recommended_at)'
        '  ) '
        'ORDER BY r.recommended_at DESC LIMIT 5'
    ).fetchall()

    return render_template('home.html',
                           total_applicants=total_applicants,
                           active_vacancies=active_vacancies,
                           total_employers=total_employers,
                           total_recs=total_recs,
                           last_login=last_login,
                           recent_applicants=recent_applicants,
                           recent_recs=recent_recs)

# ── RECOMMENDATION ────────────────────────────────────────────────────────────
@app.route('/recommendation')
@login_required
def recommendation():
    db = get_db()
    applicants = db.execute(
        'SELECT id, first_name, last_name, educ_level, preferred_position, skills, work_experience FROM applicants '
        'WHERE is_archived = 0 ORDER BY last_name, first_name'
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
@login_required
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
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/api/analytics')
@login_required
def api_analytics():
    # Returns JSON consumed by analytics.html via fetch().
    # All queries honour an optional date filter on peis_reg_date.
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
@login_required
def applicants_list():
    db = get_db()
    search    = request.args.get('search', '').strip()
    archived  = request.args.get('archived', '0') == '1'
    status    = request.args.get('status', 'all')      # all | incomplete | employed | unemployed
    district  = request.args.get('district', '')       # '' | District 1 | District 2
    view      = request.args.get('view', 'card')        # card | table
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
    pages  = max(1, (total + per_page - 1) // per_page)  # ceiling division
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
@login_required
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
                           educ_levels=EDUC_LEVELS, action='register')

@app.route('/applicants/<int:aid>/edit', methods=['GET', 'POST'])
@login_required
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
                           educ_levels=EDUC_LEVELS, action='edit')

@app.route('/applicants/<int:aid>/archive', methods=['POST'])
@login_required
def applicant_archive(aid):
    get_db().execute('UPDATE applicants SET is_archived=1 WHERE id=?', (aid,))
    get_db().commit()
    flash('Applicant archived.', 'success')
    return redirect(url_for('applicants_list'))

@app.route('/applicants/<int:aid>/restore', methods=['POST'])
@login_required
def applicant_restore(aid):
    get_db().execute('UPDATE applicants SET is_archived=0 WHERE id=?', (aid,))
    get_db().commit()
    flash('Applicant restored.', 'success')
    return redirect(url_for('applicants_list') + '?archived=1')

@app.route('/applicants/<int:aid>/delete', methods=['POST'])
@login_required
def applicant_delete(aid):
    db = get_db()
    ap = db.execute('SELECT first_name, last_name FROM applicants WHERE id=?', (aid,)).fetchone()
    if not ap:
        flash('Applicant not found.', 'danger')
        return redirect(url_for('applicants_list'))
    db.execute('DELETE FROM recommendations WHERE applicant_id=?', (aid,))
    db.execute('DELETE FROM applicants WHERE id=?', (aid,))
    db.commit()
    flash(f'Applicant {ap["first_name"]} {ap["last_name"]} has been permanently deleted.', 'success')
    return redirect(url_for('applicants_list'))

@app.route('/applicants/upload', methods=['GET', 'POST'])
@login_required
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
        fname    = secure_filename(file.filename)
        fpath    = os.path.join(UPLOAD_FOLDER, fname)
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

# ── VACANCIES ─────────────────────────────────────────────────────────────────
@app.route('/vacancies')
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
def vacancy_delete(vid):
    db = get_db()
    v  = db.execute('SELECT job_title, employer_name FROM job_vacancies WHERE id=?', (vid,)).fetchone()
    if not v:
        flash('Vacancy not found.', 'danger')
        return redirect(url_for('vacancies_list'))
    db.execute('DELETE FROM recommendations WHERE vacancy_id=?', (vid,))
    db.execute('DELETE FROM job_vacancies WHERE id=?', (vid,))
    db.commit()
    flash(f'Vacancy "{v["job_title"]}" ({v["employer_name"]}) has been permanently deleted.', 'success')
    return redirect(url_for('vacancies_list'))

# ── USERS ─────────────────────────────────────────────────────────────────────
@app.route('/users')
@login_required
def users_list():
    db     = get_db()
    status = request.args.get('status', 'all')
    view   = request.args.get('view', 'card')
    if status == 'active':
        users = db.execute('SELECT * FROM users WHERE is_active=1 ORDER BY full_name').fetchall()
    elif status == 'inactive':
        users = db.execute('SELECT * FROM users WHERE is_active=0 ORDER BY full_name').fetchall()
    else:
        users = db.execute('SELECT * FROM users ORDER BY full_name').fetchall()
    return render_template('users/list.html', users=users, status=status, view=view)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
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
                    'INSERT INTO users (full_name,username,email,password_hash) VALUES (?,?,?,?)',
                    (name, user, mail, generate_password_hash(pw))
                )
                get_db().commit()
                flash('User account created.', 'success')
                return redirect(url_for('users_list'))
            except sqlite3.IntegrityError:
                flash('Username or email already exists.', 'danger')
    return render_template('users/form.html', user=None, action='add')

@app.route('/users/<int:uid>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(uid):
    db = get_db()
    u  = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        flash('User not found.', 'danger')
        return redirect(url_for('users_list'))
    if request.method == 'POST':
        f    = request.form
        name = f.get('full_name','').strip()
        mail = f.get('email','').strip()
        pw   = f.get('new_password','')
        try:
            if pw:
                if len(pw) < 8:
                    flash('Password must be at least 8 characters.', 'danger')
                    return render_template('users/form.html', user=dict(u), action='edit')
                db.execute('UPDATE users SET full_name=?,email=?,password_hash=? WHERE id=?',
                           (name, mail, generate_password_hash(pw), uid))
            else:
                db.execute('UPDATE users SET full_name=?,email=? WHERE id=?',
                           (name, mail, uid))
            db.commit()
            flash('User updated.', 'success')
            return redirect(url_for('users_list'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'danger')
    return render_template('users/form.html', user=dict(u), action='edit')

@app.route('/users/<int:uid>/delete', methods=['POST'])
@login_required
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
@login_required
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
@login_required
def login_history():
    logs = get_db().execute(
        'SELECT ll.*, u.full_name FROM login_logs ll '
        'LEFT JOIN users u ON ll.user_id=u.id '
        'ORDER BY ll.timestamp DESC LIMIT 200'
    ).fetchall()
    return render_template('users/login_history.html', logs=logs)

# ── STARTUP ───────────────────────────────────────────────────────────────────
init_db()
load_pipeline()

if __name__ == '__main__':
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("PESO CSJDM running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
