---
name: system-redesign-rationale
description: "Sept 2026 redesign direction — multi-entity system justified by PESO walk-in queue problem; core problem, solution logic, entity roles, and feature priority"
---

## Why the System Was Redesigned (Multi-Entity)

Professor flagged the original single-user (PESO staff only) web system as inappropriate for a web-based deployment — no justification for buying a domain if only one entity uses it in-office.

Two options given:
1. Convert to offline desktop application
2. Add multiple entities (jobseeker, employer, admin, PESO staff)

**Decision: Option 2.** Offline conversion would invalidate the paper title and weaken the capstone. Multi-entity expands scope additively without tearing down existing work.

---

## The Actual Problem Being Solved

**Root cause:** Matching happens at the counter, in real time, manually.

Current jobseeker experience:
```
Travel to office → queue → wait → staff manually checks vacancies on the spot
→ either referred OR turned away — trip may have been wasted
```

Two pain points:
- **Jobseeker:** wasted trip, travel cost, uncertainty, no guarantee before arriving
- **PESO Staff:** handles one person at a time at the counter, manually, with a growing queue

---

## What the System Actually Does

Moves the matching **out of the counter and onto the internet, before the visit.**

```
Jobseeker registers online → fills profile from home
→ ML pre-matches to job categories
→ PESO staff reviews at their desk (no queue pressure)
→ Staff issues referral online
→ Jobseeker notified → comes in ONLY to pick up referral slip (or downloads it)
```

Physical visit becomes optional or guaranteed-outcome — you only come in if already matched.

---

## One-Sentence Pitch

> "The system eliminates the PESO walk-in queue by moving jobseeker registration, vacancy browsing, and job matching online — so that when a jobseeker physically visits the office, PESO staff has already made the referral decision."

---

## Entity Roles (Summary)

**Admin**
- Manages PESO staff accounts and employer registrations
- Views audit logs and system-wide analytics (read-only)
- No operational role in employment facilitation

**PESO Staff**
- Reviews jobseeker profiles and ML-generated recommendations
- **Sole authority to issue referrals** — no other entity can refer
- Manages vacancies (add/edit/deactivate)
- Uploads PEIS batch data
- Views full analytics dashboard

**Employer**
- Posts and manages their own job vacancies online
- Views applicants referred to their vacancies (name + referral date only)
- Records hiring outcome (hired / not hired)
- Cannot view full applicant profiles or ML scores

**Jobseeker**
- Registers and fills profile online (education, skills, preferred position, work experience)
- Browses active vacancies
- Views own ML-generated job category recommendations
- Tracks referral status issued by PESO staff
- Cannot self-refer or contact employers directly

---

## Referral Flow

```
Jobseeker fills profile online
        ↓
ML generates ranked job category recommendations
        ↓
PESO Staff reviews recommendations + active vacancies
        ↓
PESO Staff issues referral  ← SOLE AUTHORITY
        ↓
Jobseeker sees referral status / notification
        ↓
Employer sees referred applicant → records hiring outcome
        ↓
PESO Staff analytics dashboard updated
```

---

## Feature Priority

**Core (directly solves the queue problem):**
- Jobseeker online registration + profile
- Browse active vacancies (public)
- ML recommendation visible to jobseeker
- PESO staff reviews + issues referral online
- Referral status notification to jobseeker
- Employer posts vacancies online
- Employer confirms hiring outcome

**Nice to have (useful but not critical to queue):**
- Downloadable referral slip (PDF)
- Employer views referred applicants
- Admin panel
