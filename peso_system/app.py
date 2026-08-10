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
from datetime import datetime
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
ALLOWED_EXT    = {'csv', 'xlsx', 'xls'}

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
            id                INTEGER  PRIMARY KEY AUTOINCREMENT,
            first_name        TEXT     NOT NULL,
            last_name         TEXT     NOT NULL,
            sex               TEXT,
            civil_status      TEXT,
            birthdate         TEXT,
            contact_number    TEXT,
            email             TEXT,
            barangay          TEXT,
            district          TEXT,
            is_4ps            INTEGER  DEFAULT 0,
            is_pwd            INTEGER  DEFAULT 0,
            is_youth          INTEGER  DEFAULT 0,
            is_senior         INTEGER  DEFAULT 0,
            employment_status TEXT     DEFAULT 'Unemployed',
            educ_level        TEXT     NOT NULL,
            preferred_position TEXT    NOT NULL,
            skills            TEXT     NOT NULL,
            work_experience   TEXT,
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_archived       INTEGER  DEFAULT 0
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
        except Exception:
            pipeline = None

def _strip_numeric_noise(text):
    text = re.sub(r'\b\d+\s*(?:mos?|years?)\s*as\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def _clean_profile(educ_level, preferred_position, skills, work_experience):
    if not work_experience or not work_experience.strip():
        work_experience = 'NO EXPERIENCE'
    f = {
        'e': educ_level,
        'p': preferred_position,
        's': skills,
        'w': work_experience,
    }
    f = {k: v.lower() for k, v in f.items()}
    f = {k: re.sub(r'[^a-z0-9\s]', ' ', v) for k, v in f.items()}
    f = {k: re.sub(r'\s+', ' ', v).strip() for k, v in f.items()}
    f['w'] = _strip_numeric_noise(f['w'])
    return re.sub(r'\s+', ' ', f'{f["e"]} {f["p"]} {f["s"]} {f["w"]}').strip()

def get_recommendations(educ_level, preferred_position, skills, work_experience, vacancies):
    if pipeline is None:
        return []
    vec   = pipeline['vectorizer']
    model = pipeline['model']
    text  = _clean_profile(educ_level, preferred_position, skills, work_experience)
    proba = model.predict_proba(vec.transform([text]))[0]
    cat_scores = {CATEGORIES[i]: round(float(proba[i]), 4) for i in range(len(CATEGORIES))}
    scored = []
    for v in vacancies:
        score = cat_scores.get(v['occupational_category'], 0.0)
        scored.append({
            'id':               v['id'],
            'title':            v['job_title'],
            'employer':         v['employer_name'],
            'category':         v['occupational_category'],
            'suitability_score': score,
            'suitability_pct':  f'{score * 100:.1f}%',
        })
    scored.sort(key=lambda x: x['suitability_score'], reverse=True)
    for i, item in enumerate(scored, 1):
        item['rank'] = i
    return scored[:5]

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

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('recommendation') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('recommendation'))
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
                return redirect(url_for('recommendation'))
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

# ── RECOMMENDATION ────────────────────────────────────────────────────────────
@app.route('/recommendation')
@login_required
def recommendation():
    db = get_db()
    applicants = db.execute(
        'SELECT id, first_name, last_name, educ_level, preferred_position FROM applicants '
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
                           preselect_id=preselect_id)

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
        for item in results:
            db.execute(
                'INSERT INTO recommendations '
                '(applicant_id,vacancy_id,suitability_score,rank,generated_by) VALUES (?,?,?,?,?)',
                (applicant_id, item['id'], item['suitability_score'], item['rank'], session['user_id'])
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
    db = get_db()

    total = db.execute('SELECT COUNT(*) FROM applicants WHERE is_archived=0').fetchone()[0]
    male  = db.execute("SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND sex='Male'").fetchone()[0]
    fem   = db.execute("SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND sex='Female'").fetchone()[0]
    youth = db.execute('SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND is_youth=1').fetchone()[0]
    senior= db.execute('SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND is_senior=1').fetchone()[0]
    pwd   = db.execute('SELECT COUNT(*) FROM applicants WHERE is_archived=0 AND is_pwd=1').fetchone()[0]

    educ_rows = db.execute(
        'SELECT educ_level, COUNT(*) c FROM applicants WHERE is_archived=0 '
        'GROUP BY educ_level ORDER BY c DESC'
    ).fetchall()
    emp_rows = db.execute(
        'SELECT employment_status, COUNT(*) c FROM applicants WHERE is_archived=0 '
        'GROUP BY employment_status'
    ).fetchall()
    d1_rows = db.execute(
        "SELECT barangay, COUNT(*) c FROM applicants "
        "WHERE is_archived=0 AND district='District 1' AND barangay!='' "
        "GROUP BY barangay ORDER BY c DESC LIMIT 10"
    ).fetchall()
    d2_rows = db.execute(
        "SELECT barangay, COUNT(*) c FROM applicants "
        "WHERE is_archived=0 AND district='District 2' AND barangay!='' "
        "GROUP BY barangay ORDER BY c DESC LIMIT 10"
    ).fetchall()

    total_vac    = db.execute('SELECT COUNT(*) FROM job_vacancies WHERE is_active=1').fetchone()[0]
    local_vac    = db.execute("SELECT COUNT(*) FROM job_vacancies WHERE is_active=1 AND is_local=1").fetchone()[0]
    total_emp    = db.execute("SELECT COUNT(DISTINCT employer_name) FROM job_vacancies WHERE is_active=1").fetchone()[0]
    local_emp    = db.execute("SELECT COUNT(DISTINCT employer_name) FROM job_vacancies WHERE is_active=1 AND is_local=1").fetchone()[0]

    top_vac = db.execute(
        'SELECT job_title, COUNT(*) c FROM job_vacancies WHERE is_active=1 '
        'GROUP BY job_title ORDER BY c DESC LIMIT 10'
    ).fetchall()
    top_ind = db.execute(
        'SELECT occupational_category, COUNT(*) c FROM job_vacancies WHERE is_active=1 '
        'GROUP BY occupational_category ORDER BY c DESC'
    ).fetchall()
    top_place = db.execute(
        'SELECT jv.job_title, COUNT(*) c FROM recommendations r '
        'JOIN job_vacancies jv ON r.vacancy_id=jv.id WHERE r.rank=1 '
        'GROUP BY jv.job_title ORDER BY c DESC LIMIT 10'
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
        },
        'vacancies': {
            'total': total_vac, 'local': local_vac, 'overseas': total_vac - local_vac,
            'total_employers': total_emp, 'local_employers': local_emp,
            'overseas_employers': total_emp - local_emp,
            'top_vac_labels':   [r['job_title'] for r in top_vac],
            'top_vac_values':   [r['c'] for r in top_vac],
            'ind_labels':       [r['occupational_category'] for r in top_ind],
            'ind_values':       [r['c'] for r in top_ind],
            'place_labels':     [r['job_title'] for r in top_place],
            'place_values':     [r['c'] for r in top_place],
        }
    })

# ── APPLICANTS ────────────────────────────────────────────────────────────────
@app.route('/applicants')
@login_required
def applicants_list():
    db = get_db()
    search   = request.args.get('search', '').strip()
    archived = request.args.get('archived', '0') == '1'
    q        = 'SELECT * FROM applicants WHERE is_archived=?'
    params   = [1 if archived else 0]
    if search:
        q += ' AND (first_name LIKE ? OR last_name LIKE ? OR preferred_position LIKE ? OR skills LIKE ?)'
        like = f'%{search}%'
        params += [like, like, like, like]
    q += ' ORDER BY last_name, first_name'
    applicants = db.execute(q, params).fetchall()
    return render_template('applicants/list.html', applicants=applicants,
                           search=search, archived=archived)

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
        db.execute('''
            INSERT INTO applicants (first_name,last_name,sex,civil_status,birthdate,
                contact_number,email,barangay,district,is_4ps,is_pwd,is_youth,is_senior,
                employment_status,educ_level,preferred_position,skills,work_experience)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            f.get('first_name','').strip(), f.get('last_name','').strip(),
            f.get('sex',''), f.get('civil_status',''), f.get('birthdate',''),
            f.get('contact_number','').strip(), f.get('email','').strip(),
            f.get('barangay','').strip(), f.get('district',''),
            1 if f.get('is_4ps') else 0, 1 if f.get('is_pwd') else 0,
            1 if f.get('is_youth') else 0, 1 if f.get('is_senior') else 0,
            f.get('employment_status','Unemployed'),
            f.get('educ_level',''), f.get('preferred_position','').strip(),
            f.get('skills','').strip(), f.get('work_experience','').strip(),
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
        db.execute('''
            UPDATE applicants SET first_name=?,last_name=?,sex=?,civil_status=?,birthdate=?,
                contact_number=?,email=?,barangay=?,district=?,is_4ps=?,is_pwd=?,is_youth=?,
                is_senior=?,employment_status=?,educ_level=?,preferred_position=?,skills=?,
                work_experience=? WHERE id=?
        ''', (
            f.get('first_name','').strip(), f.get('last_name','').strip(),
            f.get('sex',''), f.get('civil_status',''), f.get('birthdate',''),
            f.get('contact_number','').strip(), f.get('email','').strip(),
            f.get('barangay','').strip(), f.get('district',''),
            1 if f.get('is_4ps') else 0, 1 if f.get('is_pwd') else 0,
            1 if f.get('is_youth') else 0, 1 if f.get('is_senior') else 0,
            f.get('employment_status','Unemployed'),
            f.get('educ_level',''), f.get('preferred_position','').strip(),
            f.get('skills','').strip(), f.get('work_experience','').strip(),
            aid,
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
            flash('Only CSV, XLS, or XLSX files are accepted.', 'danger')
            return redirect(request.url)
        fname    = secure_filename(file.filename)
        fpath    = os.path.join(UPLOAD_FOLDER, fname)
        file.save(fpath)
        try:
            if ext in ('xlsx', 'xls'):
                try:
                    df = pd.read_excel(fpath, header=2)
                    if 'EDUC LEVEL' not in [c.strip().upper() for c in df.columns]:
                        df = pd.read_excel(fpath, header=0)
                except Exception:
                    df = pd.read_excel(fpath, header=0)
            else:
                df = pd.read_csv(fpath)
            df.columns = [str(c).strip().upper() for c in df.columns]
            col_map = {
                'EDUC LEVEL': 'educ_level', 'EDUCATION LEVEL': 'educ_level',
                'PREFERRED POSITION': 'preferred_position',
                'SKILLS': 'skills', 'WORK EXPERIENCE': 'work_experience',
                'FIRST NAME': 'first_name', 'FIRSTNAME': 'first_name',
                'LAST NAME': 'last_name', 'LASTNAME': 'last_name',
                'SEX': 'sex', 'CIVIL STATUS': 'civil_status',
                'BARANGAY': 'barangay', 'CONTACT NUMBER': 'contact_number',
                'EMAIL': 'email', 'EMAIL ADDRESS': 'email',
            }
            db = get_db()
            ok, skip, errs = 0, 0, []
            for idx, row in df.iterrows():
                try:
                    rec = {}
                    for pc, sc in col_map.items():
                        if pc in df.columns:
                            v = row.get(pc, '')
                            rec[sc] = '' if pd.isna(v) else str(v).strip()
                    if not rec.get('educ_level') or not rec.get('preferred_position') or not rec.get('skills'):
                        skip += 1
                        errs.append(f"Row {idx+1}: Missing required fields")
                        continue
                    db.execute('''
                        INSERT INTO applicants (first_name,last_name,sex,civil_status,
                            contact_number,email,barangay,educ_level,
                            preferred_position,skills,work_experience)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        rec.get('first_name','Unknown'), rec.get('last_name','Unknown'),
                        rec.get('sex',''), rec.get('civil_status',''),
                        rec.get('contact_number',''), rec.get('email',''),
                        rec.get('barangay',''), rec.get('educ_level',''),
                        rec.get('preferred_position',''), rec.get('skills',''),
                        rec.get('work_experience',''),
                    ))
                    ok += 1
                except Exception as e:
                    skip += 1
                    errs.append(f"Row {idx+1}: {e}")
            db.commit()
            flash(f'Upload complete: {ok} imported, {skip} skipped.',
                  'success' if ok > 0 else 'warning')
            for e in errs[:5]:
                flash(e, 'warning')
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
    return render_template('vacancies/list.html', vacancies=vacancies,
                           search=search, status=status)

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

# ── USERS ─────────────────────────────────────────────────────────────────────
@app.route('/users')
@login_required
def users_list():
    users = get_db().execute('SELECT * FROM users ORDER BY full_name').fetchall()
    return render_template('users/list.html', users=users)

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
    app.run(debug=True, host='0.0.0.0', port=5000)
