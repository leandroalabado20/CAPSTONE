"""Fix and improve all demo data in peso.db for the final defense."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_db
from werkzeug.security import generate_password_hash
import json

PW_HASH = generate_password_hash('Demo1234')

with app.app_context():
    db = get_db()

    # ── 1. PASSWORDS — set all to Demo1234 ───────────────────────────────────
    db.execute('UPDATE users SET password_hash=?', (PW_HASH,))

    # ── 2. FIX EMPLOYER total_workforce encoding (corrupted dash) ────────────
    db.execute("UPDATE employers SET total_workforce='Small (10-99)'   WHERE total_workforce LIKE 'Small%'")
    db.execute("UPDATE employers SET total_workforce='Medium (100-199)' WHERE total_workforce LIKE 'Medium%'")
    db.execute("UPDATE employers SET total_workforce='Large (200+)'     WHERE total_workforce LIKE 'Large%'")

    # ── 3. APPLICANT 1 – Juan dela Cruz (user_id=7) ──────────────────────────
    db.execute("""UPDATE applicants SET
        skills            = 'Machine Operation, Quality Control, Driving, Electrician, Forklift Operation',
        city              = 'City of San Jose del Monte',
        tin               = '123-456-789-000',
        civil_status      = 'Single',
        height_cm         = '170',
        religion          = 'Roman Catholic',
        address_line      = '12 Rizal St',
        province          = 'Bulacan',
        is_ofw            = 0,
        ofw_country       = '',
        is_former_ofw     = 1,
        former_ofw_country = 'United Arab Emirates',
        ofw_return_date   = '2026-01-10',
        unemployed_reason = 'Finished Contract',
        job_search_months = 9,
        pref_work_local   = 'City of San Jose del Monte, Bulacan',
        languages         = ?,
        education         = ?,
        trainings         = ?,
        eligibilities     = ?,
        work_history      = ?,
        other_skills      = ?,
        certified         = 1
        WHERE applicant_id = 1""",
    (
        json.dumps([
            {'language':'Filipino','read':True,'write':True,'speak':True,'understand':True},
            {'language':'English', 'read':True,'write':True,'speak':True,'understand':True},
        ]),
        json.dumps([
            {'level':'College Graduate','school':'Bulacan State University',
             'course':'BS Industrial Technology','year_graduated':'2022'},
        ]),
        json.dumps([
            {'title':'TESDA NC II – Driving (Light Vehicle)','conducted_by':'TESDA Bulacan',
             'hours':40,'year':'2022'},
        ]),
        json.dumps([
            {'type':'National Certificate (TESDA NC)',
             'title':'NC II – Driving (Light Vehicle)',
             'date_acquired':'2022-06-01','rating':''},
        ]),
        json.dumps([
            {'company':'ACME Manufacturing Corp.','address':'Muzon, CSJDM, Bulacan',
             'position':'Machine Operator','date_from':'2022-08-01','date_to':'2025-12-15',
             'status':'Resigned','reason':'OFW opportunity'},
        ]),
        json.dumps(['Forklift Operation','Basic Electrical Wiring']),
    ))

    # ── 4. APPLICANT 2 – Maria Santos (user_id=8) ────────────────────────────
    db.execute("""UPDATE applicants SET
        age               = 25,
        birthdate         = '2001-05-20',
        sex               = 'Female',
        barangay          = 'Kaypian',
        district          = 'District 2',
        civil_status      = 'Single',
        height_cm         = '155',
        religion          = 'Roman Catholic',
        contact_number    = '09181110002',
        address_line      = '45 Sampaguita St',
        city              = 'City of San Jose del Monte',
        province          = 'Bulacan',
        skills            = 'Customer Service, Cashiering, Product Merchandising, Basic Computer Operations, POS System',
        work_experience   = 'Cashier, Sales Associate',
        employment_status = 'Unemployed',
        unemployed_reason = 'End of Contract',
        job_search_months = 4,
        pref_work_local   = 'City of San Jose del Monte, Bulacan',
        languages         = ?,
        education         = ?,
        trainings         = ?,
        eligibilities     = ?,
        work_history      = ?,
        other_skills      = ?,
        certified         = 1
        WHERE applicant_id = 2""",
    (
        json.dumps([
            {'language':'Filipino','read':True,'write':True,'speak':True,'understand':True},
            {'language':'English', 'read':True,'write':False,'speak':True,'understand':True},
        ]),
        json.dumps([
            {'level':'Senior High School Graduate','school':'Kaypian National High School',
             'course':'ABM Strand','year_graduated':'2019'},
        ]),
        json.dumps([
            {'title':'Customer Service Excellence','conducted_by':'TESDA Bulacan',
             'hours':24,'year':'2021'},
        ]),
        json.dumps([]),
        json.dumps([
            {'company':'SuperFresh Retail Corp.','address':'Gaya-Gaya, CSJDM, Bulacan',
             'position':'Sales Associate','date_from':'2021-03-01','date_to':'2024-02-28',
             'status':'End of Contract','reason':'Contractual ended'},
        ]),
        json.dumps(['Basic Baking','Beautician']),
    ))

    # ── 5. APPLICANT 3 – Pedro Reyes (user_id=9) ─────────────────────────────
    db.execute("""UPDATE applicants SET
        age               = 31,
        birthdate         = '1995-03-10',
        sex               = 'Male',
        barangay          = 'Minuyan I',
        district          = 'District 1',
        civil_status      = 'Married',
        height_cm         = '168',
        religion          = 'Roman Catholic',
        contact_number    = '09181110003',
        address_line      = '78 Mabini St',
        city              = 'City of San Jose del Monte',
        province          = 'Bulacan',
        disability        = '["Physical"]',
        skills            = 'Forklift Operation, Warehouse Operations, Driving, Inventory Management',
        work_experience   = 'Forklift Operator, Warehouse Helper',
        employment_status = 'Unemployed',
        unemployed_reason = 'Redundancy / Retrenchment',
        job_search_months = 5,
        pref_work_local   = 'City of San Jose del Monte, Bulacan',
        languages         = ?,
        education         = ?,
        trainings         = ?,
        eligibilities     = ?,
        work_history      = ?,
        other_skills      = ?,
        certified         = 1
        WHERE applicant_id = 3""",
    (
        json.dumps([
            {'language':'Filipino','read':True,'write':True,'speak':True,'understand':True},
        ]),
        json.dumps([
            {'level':'High School Graduate','school':'Minuyan National High School',
             'course':'','year_graduated':'2012'},
        ]),
        json.dumps([
            {'title':'TESDA NC II – Forklift Operation','conducted_by':'TESDA Bulacan',
             'hours':60,'year':'2015'},
        ]),
        json.dumps([
            {'type':'National Certificate (TESDA NC)',
             'title':'NC II – Forklift Operation',
             'date_acquired':'2015-09-01','rating':''},
        ]),
        json.dumps([
            {'company':'Metro Logistics Inc.','address':'Tungkong Mangga, CSJDM, Bulacan',
             'position':'Forklift Operator','date_from':'2016-01-10','date_to':'2026-05-31',
             'status':'Retrenched','reason':'Company downsizing'},
        ]),
        json.dumps(['Basic Automotive Maintenance']),
    ))

    # ── 6. APPLICANT 4 – Ana Lopez (user_id=10) ──────────────────────────────
    db.execute("""UPDATE applicants SET
        age               = 24,
        birthdate         = '2002-08-14',
        sex               = 'Female',
        barangay          = 'Gaya-Gaya',
        district          = 'District 1',
        civil_status      = 'Single',
        height_cm         = '160',
        religion          = 'Roman Catholic',
        address_line      = '23 Rizal Ave',
        city              = 'City of San Jose del Monte',
        province          = 'Bulacan',
        skills            = 'Data Encoding, Microsoft Office, Records Management, Customer Service, Scheduling',
        work_experience   = 'Office Clerk, Administrative Assistant',
        employment_status = 'Unemployed',
        unemployed_reason = 'Resigned',
        job_search_months = 6,
        pref_work_local   = 'City of San Jose del Monte, Bulacan',
        languages         = ?,
        education         = ?,
        trainings         = ?,
        eligibilities     = ?,
        work_history      = ?,
        other_skills      = ?,
        certified         = 1
        WHERE applicant_id = 4""",
    (
        json.dumps([
            {'language':'Filipino','read':True,'write':True,'speak':True,'understand':True},
            {'language':'English', 'read':True,'write':True,'speak':True,'understand':True},
        ]),
        json.dumps([
            {'level':'College Graduate',
             'school':'Bulacan State University – Sarmiento Campus',
             'course':'BS Business Administration','year_graduated':'2024'},
        ]),
        json.dumps([
            {'title':'Business Process Outsourcing (BPO) NC II','conducted_by':'TESDA Bulacan',
             'hours':40,'year':'2024'},
        ]),
        json.dumps([]),
        json.dumps([
            {'company':'BrightPath Business Services','address':'Sapang Palay, CSJDM, Bulacan',
             'position':'Office Clerk','date_from':'2024-06-01','date_to':'2026-05-31',
             'status':'Resigned','reason':'Career advancement'},
        ]),
        json.dumps(['Basic Bookkeeping','Event Coordination']),
    ))

    # ── 7. APPLICANT 5 – Jose Garcia (user_id=11) ────────────────────────────
    db.execute("""UPDATE applicants SET
        age               = 35,
        birthdate         = '1991-09-22',
        sex               = 'Male',
        barangay          = 'San Rafael I',
        district          = 'District 2',
        civil_status      = 'Married',
        height_cm         = '172',
        religion          = 'Roman Catholic',
        address_line      = '5 Aguinaldo St',
        city              = 'City of San Jose del Monte',
        province          = 'Bulacan',
        skills            = 'Security / Guard Duties, Firearms Handling, First Aid / Basic Life Support, Crowd Control, Cleaning / Sanitation',
        work_experience   = 'Security Guard, Utility Worker',
        employment_status = 'Unemployed',
        unemployed_reason = 'End of Contract',
        job_search_months = 3,
        pref_work_local   = 'City of San Jose del Monte, Bulacan',
        languages         = ?,
        education         = ?,
        trainings         = ?,
        eligibilities     = ?,
        work_history      = ?,
        other_skills      = ?,
        certified         = 1
        WHERE applicant_id = 5""",
    (
        json.dumps([
            {'language':'Filipino','read':True,'write':True,'speak':True,'understand':True},
        ]),
        json.dumps([
            {'level':'High School Graduate','school':'San Rafael National High School',
             'course':'','year_graduated':'2008'},
        ]),
        json.dumps([
            {'title':'Basic Security Services','conducted_by':'PNP-SOSIA','hours':120,'year':'2010'},
            {'title':'First Aid & Basic Life Support','conducted_by':'Philippine Red Cross',
             'hours':16,'year':'2015'},
        ]),
        json.dumps([
            {'type':'Civil Service Eligibility','title':'CSC Sub-Professional',
             'date_acquired':'2012-08-01','rating':'80.15'},
        ]),
        json.dumps([
            {'company':'Guardian Facilities Services','address':'San Rafael I, CSJDM, Bulacan',
             'position':'Security Guard','date_from':'2010-03-01','date_to':'2026-09-30',
             'status':'End of Contract','reason':'Contract ended'},
        ]),
        json.dumps(['Basic Electrical Work','Gardening']),
    ))

    # ── 8. VACANCIES — add job_location to all ───────────────────────────────
    locations = {
        'Metro Logistics Inc.':         'Tungkong Mangga, City of San Jose del Monte, Bulacan',
        'ACME Manufacturing Corp.':     'Muzon, City of San Jose del Monte, Bulacan',
        'SuperFresh Retail Corp.':      'Gaya-Gaya, City of San Jose del Monte, Bulacan',
        'BrightPath Business Services': 'Sapang Palay, City of San Jose del Monte, Bulacan',
        'Guardian Facilities Services': 'San Rafael I, City of San Jose del Monte, Bulacan',
    }
    for emp, loc in locations.items():
        db.execute(
            "UPDATE job_vacancies SET job_location=? WHERE employer_name=? AND (job_location IS NULL OR job_location='')",
            (loc, emp)
        )

    # ── 9. VACANCIES — interview schedule (one per employer, demo-ready) ──────
    schedules = [
        # vid  req_dl        iv_start      iv_end        time_s  time_e  venue
        (2,  '2026-11-05', '2026-11-12', '2026-11-14', '08:00','17:00',
         'Metro Logistics Inc., 12 Quirino Highway, Tungkong Mangga, CSJDM'),
        (5,  '2026-11-05', '2026-11-12', '2026-11-14', '08:00','17:00',
         'ACME Manufacturing Corp., Industrial Park Bldg 4, Muzon, CSJDM'),
        (7,  '2026-11-03', '2026-11-10', '2026-11-11', '09:00','16:00',
         'SuperFresh Retail Corp., SuperFresh Mall, Gaya-Gaya, CSJDM'),
        (11, '2026-11-07', '2026-11-17', '2026-11-18', '08:00','17:00',
         'BrightPath Business Services, BrightPath Tower, Sapang Palay, CSJDM'),
        (13, '2026-11-01', '2026-11-08', '2026-11-08', '08:00','12:00',
         'Guardian Facilities Services, Guardian Bldg, San Rafael I, CSJDM'),
    ]
    for vid, rd, id_, ie, ts, te, venue in schedules:
        db.execute("""UPDATE job_vacancies SET
            requirements_deadline=?, interview_date=?, interview_date_end=?,
            interview_time=?, interview_time_end=?, venue_address=?
            WHERE vacancy_id=?""",
            (rd, id_, ie, ts, te, venue, vid))

    # ── 10. VACANCIES — add req_skills to key vacancies ──────────────────────
    req_skills_map = {
        2:  'Forklift Operation,Warehouse Operations',
        3:  'Driving',
        5:  'Machine Operation,Quality Control',
        7:  'Customer Service,Cashiering',
        11: 'Data Encoding,Microsoft Office',
        13: 'Security / Guard Duties,Firearms Handling',
    }
    for vid, skills in req_skills_map.items():
        db.execute('UPDATE job_vacancies SET req_skills=? WHERE vacancy_id=?', (skills, vid))

    db.commit()
    print('Done. Verifying...')

    # ── VERIFICATION ─────────────────────────────────────────────────────────
    print('\n=== PASSWORDS ===')
    from werkzeug.security import check_password_hash
    for u in db.execute('SELECT email, password_hash FROM users ORDER BY user_id').fetchall():
        ok = check_password_hash(u['password_hash'], 'Demo1234')
        print(f"  {'OK' if ok else 'FAIL'} {u['email']}")

    print('\n=== APPLICANT PROFILE COMPLETENESS ===')
    for a in db.execute('SELECT applicant_id, first_name, last_name, city, skills, certified, birthdate FROM applicants WHERE applicant_id<=5').fetchall():
        print(f"  ap{a['applicant_id']} {a['first_name']} {a['last_name']}: city={a['city']}, certified={a['certified']}, birthdate={a['birthdate']}, skills={str(a['skills'])[:50]}")

    print('\n=== VACANCIES WITH LOCATION & SCHEDULE ===')
    cnt_loc = db.execute("SELECT COUNT(*) FROM job_vacancies WHERE job_location IS NOT NULL AND job_location!=''").fetchone()[0]
    cnt_sch = db.execute('SELECT COUNT(*) FROM job_vacancies WHERE interview_date IS NOT NULL').fetchone()[0]
    print(f'  {cnt_loc}/35 have job_location, {cnt_sch}/35 have interview schedule')

    print('\n=== EMPLOYERS workforce fix ===')
    for e in db.execute('SELECT company_name, total_workforce FROM employers').fetchall():
        print(f"  {e['company_name']}: {e['total_workforce']}")
