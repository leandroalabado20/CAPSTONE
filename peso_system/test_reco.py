import sys, json, re
sys.path.insert(0, '.')

EDUC_RANK = {'No Formal Education':0,'Elementary':1,'High School':2,'Vocational':3,
             'College Level':4,'College Graduate':5,'Post-Graduate':6}
CB_WEIGHTS = {'skills':0.45,'experience':0.35,'education':0.20}
CB_MIN     = 0.50
TITLE_MIN  = 0.50
STOP       = {'the','a','an','of','and','for','in','at','to','or','as','is','on','by','with'}

def token_set(t):
    return {w for w in re.split(r'[\s/\-,]+', (t or '').lower()) if w and w not in STOP}

def total_exp(ap):
    raw = ap.get('work_history') or '[]'
    data = json.loads(raw) if isinstance(raw, str) else raw
    return sum(int(e['months']) for e in data if str(e.get('months','')).isdigit())

def ap_skills(ap):
    return {s.strip().lower() for s in (ap.get('skills') or '').split(',') if s.strip()}

def score(v, ap):
    filled, breakdown, weighted = 0, {}, {}
    rg = v.get('req_gender')
    if rg and rg != 'Any':
        breakdown['gender'] = 1.0 if ap.get('sex') == rg else 0.0
    lo, hi = v.get('req_age_min'), v.get('req_age_max')
    if lo or hi:
        age = ap.get('age')
        in_range = (not lo or age >= lo) and (not hi or age <= hi) if age is not None else False
        breakdown['age'] = 1.0 if in_range else 0.0
    req_edu = v.get('req_education')
    if req_edu:
        filled += 1
        have = ap.get('educ_level','')
        if req_edu in EDUC_RANK and have in EDUC_RANK:
            s = 1.0 if EDUC_RANK[have] >= EDUC_RANK[req_edu] else 0.0
        else:
            s = 1.0 if have == req_edu else 0.0
        breakdown['education'] = weighted['education'] = s
    req_mo = v.get('req_experience_months')
    if req_mo:
        filled += 1
        have_mo = total_exp(ap)
        s = 1.0 if have_mo >= req_mo else round(have_mo / req_mo, 4)
        breakdown['experience'] = weighted['experience'] = s
    req_s = v.get('req_skills','') or ''
    if req_s:
        req_set = {x.strip().lower() for x in req_s.split(',') if x.strip()}
        if req_set:
            filled += 1
            s = round(len(req_set & ap_skills(ap)) / len(req_set), 4)
            breakdown['skills'] = weighted['skills'] = s
    tt = token_set(v.get('job_title'))
    pt = token_set(ap.get('preferred_position'))
    union = tt | pt
    title_score = round(len(tt & pt) / len(union), 4) if union else 0.0
    breakdown['title'] = title_score
    total_w = sum(CB_WEIGHTS[k] for k in weighted)
    cb = round(sum(weighted[k]*CB_WEIGHTS[k] for k in weighted)/total_w, 4) if total_w > 0 else 1.0
    return cb, filled, title_score, breakdown

PASS_COUNT, FAIL_COUNT = 0, 0
def check(name, actual, expected, tol=0.001):
    global PASS_COUNT, FAIL_COUNT
    if isinstance(expected, float):
        ok = abs(actual - expected) <= tol
    else:
        ok = actual == expected
    if ok:
        PASS_COUNT += 1
        print('  PASS [%s]' % name)
    else:
        FAIL_COUNT += 1
        print('  FAIL [%s] expected=%s got=%s' % (name, expected, actual))

AP = {'preferred_position':'Data Encoder',
      'skills':'Data Encoding, Microsoft Office, Records Management',
      'educ_level':'College Graduate',
      'work_history': json.dumps([{'months':'24'}]),
      'sex':'Female','age':25}
V  = {'job_title':'Data Encoder',
      'req_skills':'Data Encoding, Microsoft Office, Records Management',
      'req_education':'College Graduate',
      'req_experience_months':12,
      'req_gender':None,'req_age_min':None,'req_age_max':None}

print('=== 1. WEIGHTS SUM TO 1.0 ===')
check('weights_sum', round(sum(CB_WEIGHTS.values()),4), 1.0)

print('=== 2. PERFECT MATCH (all 3 fields met) ===')
cb, filled, ts, bd = score(V, AP)
check('perfect_cb_score',   cb,              1.0)
check('perfect_title',      ts,              1.0)
check('perfect_filled',     filled,          3)
check('perfect_education',  bd['education'], 1.0)
check('perfect_experience', bd['experience'],1.0)
check('perfect_skills',     bd['skills'],    1.0)

print('=== 3. PARTIAL SKILLS (2 of 3 required) ===')
ap2 = dict(AP); ap2['skills'] = 'Data Encoding, Microsoft Office'
cb2, _, _, bd2 = score(V, ap2)
expected_skills = round(2/3, 4)
expected_cb2    = round(expected_skills*0.45 + 1.0*0.35 + 1.0*0.20, 4)
check('partial_skills_score', bd2['skills'], expected_skills)
check('partial_cb_score',     cb2,           expected_cb2)

print('=== 4. PARTIAL EXPERIENCE (6 of 12 months) ===')
ap3 = dict(AP); ap3['work_history'] = json.dumps([{'months':'6'}])
_, _, _, bd3 = score(V, ap3)
check('partial_exp_score', bd3['experience'], round(6/12, 4))

print('=== 5. EDUCATION BELOW REQUIREMENT ===')
ap4 = dict(AP); ap4['educ_level'] = 'High School'
_, _, _, bd4 = score(V, ap4)
check('educ_below_req', bd4['education'], 0.0)

print('=== 6. EDUCATION EXCEEDS REQUIREMENT (Post-Grad vs College Grad) ===')
ap5 = dict(AP); ap5['educ_level'] = 'Post-Graduate'
_, _, _, bd5 = score(V, ap5)
check('educ_exceeds_req', bd5['education'], 1.0)

print('=== 7. GENDER GATE ===')
v_male = dict(V); v_male['req_gender'] = 'Male'
_, _, _, bd_gf = score(v_male, AP)           # AP is Female
check('gender_gate_fail', bd_gf.get('gender'), 0.0)
ap_male = dict(AP); ap_male['sex'] = 'Male'
_, _, _, bd_gp = score(v_male, ap_male)
check('gender_gate_pass', bd_gp.get('gender'), 1.0)

print('=== 8. AGE GATE ===')
v_age = dict(V); v_age['req_age_min'] = 20; v_age['req_age_max'] = 30
_, _, _, bd_ap = score(v_age, AP)            # age=25 => in range
check('age_gate_pass', bd_ap.get('age'), 1.0)
ap_old = dict(AP); ap_old['age'] = 35
_, _, _, bd_af = score(v_age, ap_old)
check('age_gate_fail', bd_af.get('age'), 0.0)

print('=== 9. NO REQUIREMENTS => open vacancy, cb=1.0 ===')
v_open = {'job_title':'Data Encoder','req_skills':None,'req_education':None,
          'req_experience_months':None,'req_gender':None,'req_age_min':None,'req_age_max':None}
cb_open, filled_open, _, _ = score(v_open, AP)
check('open_cb_score', cb_open,    1.0)
check('open_filled',   filled_open, 0)

print('=== 10. TITLE PRE-FILTER ===')
_, _, ts_match, _ = score(v_open, AP)
check('title_exact_match', ts_match, 1.0)
ap_diff = dict(AP); ap_diff['preferred_position'] = 'Beautician'
_, _, ts_none, _ = score(v_open, ap_diff)
check('title_no_match_below_threshold', ts_none < TITLE_MIN, True)
# partial title match - shared token
v_enc = dict(v_open); v_enc['job_title'] = 'Office Encoder'
_, _, ts_part, _ = score(v_enc, AP)   # "encoder" shared => Jaccard = 1/3 = 0.333
check('title_partial_below_threshold', ts_part < TITLE_MIN, True)

print('=== 11. ZERO SKILLS OVERLAP => skills score = 0.0, cb = 0.55 (above threshold) ===')
# With 3 required fields: 0.0*0.45 + 1.0*0.35 + 1.0*0.20 = 0.55 — ranked lower but still shown
ap_nomatch = dict(AP); ap_nomatch['skills'] = 'Driving, Forklift Operation'
cb_low, _, _, bd_low = score(V, ap_nomatch)
check('zero_skills_score_zero', bd_low.get('skills'), 0.0)
check('zero_skills_cb_above_min', cb_low > CB_MIN, True)   # 0.55 > 0.50, shown but ranked lower
check('zero_skills_cb_value', cb_low, 0.55)

print('=== 12. MULTI-ENTRY EXPERIENCE TOTALS CORRECTLY ===')
ap_multi = dict(AP)
ap_multi['work_history'] = json.dumps([{'months':'10'},{'months':'8'},{'months':'6'}])
check('multi_exp_total', total_exp(ap_multi), 24)

print('=== 13. SKILLS CAP AT 3 (server-side) ===')
from app import merge_required_skills
class FakeForm:
    def get(self, k, d=''):
        if k == 'req_skills_text':
            return 'Cashiering, Customer Service, Computer Literacy, Driving'
        return d
    def getlist(self, k): return []
merged = merge_required_skills(FakeForm())
count = len([x for x in merged.split(',') if x.strip()]) if merged else 0
check('skills_server_cap', count <= 3, True)

print('=== 14. WEIGHT PROPORTIONAL RESCALING (1 field set) ===')
v_skills_only = {'job_title':'Data Encoder','req_skills':'Data Encoding',
                 'req_education':None,'req_experience_months':None,
                 'req_gender':None,'req_age_min':None,'req_age_max':None}
cb_s, filled_s, _, bd_s = score(v_skills_only, AP)
check('single_field_filled',   filled_s, 1)
check('single_field_cb_score', cb_s,     1.0)   # 1 skill matched / 1 required = 1.0

print('=== 15. ALTERNATIVE JOB LOGIC: skills>0 required ===')
# vacancy with no skills set but title doesn't match => should NOT appear as alternative
v_alt = dict(v_open); v_alt['job_title'] = 'Carpenter'
ap_beauty = dict(AP); ap_beauty['preferred_position'] = 'Beautician'
ap_beauty['skills'] = 'Haircut, Manicure'
_, _, ts_alt, bd_alt = score(v_alt, ap_beauty)
is_pos_match = ts_alt >= TITLE_MIN
skills_ok = bd_alt.get('skills', 0.0) > 0.0
# no req_skills set => skills not in breakdown => would not qualify as alternative
check('alt_no_skills_excluded', skills_ok, False)

print()
print('Results: %d passed, %d failed out of %d checks' % (PASS_COUNT, FAIL_COUNT, PASS_COUNT+FAIL_COUNT))
if FAIL_COUNT == 0:
    print('All checks passed.')
else:
    print('Some checks FAILED — review above.')
