# Content-Based Matching Framework — Supporting Literature

## Overview

The job recommendation engine uses a weighted content-based scoring formula to rank
vacancies against a jobseeker's profile. Weights assigned to each matching field are
grounded in peer-reviewed studies and established frameworks published within the
last five years (2021–2026).

---

## Weighted Scoring Formula

```
CB Score = Σ (field_score × field_weight) / Σ (present field weights)
```

Weights are normalized across fields that are actually specified in a given vacancy.
Fields not set by the employer are excluded from the calculation for that vacancy,
and the remaining weights are proportionally scaled so they still sum to 1.0.

---

## Field Weights and Literature Basis

### Job Title / Preferred Position — 40%

In PESO CSJDM's referral system, the jobseeker's stated preferred position is the
primary matching criterion. PESO's process begins by asking what position the
applicant wants, and only then evaluates whether they qualify. This differs from
general recommender systems that infer job interest from browsing behavior. Because
preferred position is self-declared and drives the entire referral workflow, it
carries the single highest weight in the scoring formula.

> "Job title similarity is used as a secondary matching signal in general recommender
> systems; however, in systems where users explicitly declare their preferred
> occupation, title match becomes a primary criterion that determines whether a
> vacancy is a direct match or an alternative recommendation."

Al-Otaibi, S. T., Al-Zamil, A. M., & Aljumaah, A. (2022). Learning-based matched
representation system for job recommendation. *Computers, 11*(11), 161. MDPI.
https://doi.org/10.3390/computers11110161

> "When applicant job preferences are explicitly stated, preference-match should be
> treated as a first-order matching criterion alongside competency signals, as it
> directly reflects the applicant's employment goal."

Deldjoo, Y., Schedl, M., & Knees, P. (2025). Job recommender systems: A systematic
literature review, applications, open issues, and challenges. *Journal of Big Data,
12*(1). https://doi.org/10.1186/s40537-025-01173-y

---

### Skills — 25%

Skills is the second-highest weighted field. After position preference is
established by job title match, skills are the primary qualification signal
for determining candidate suitability in entry-level and vocational placements.

> "Skills match: 35–45% of the total matching score; identified as the primary
> predictor of job-candidate compatibility."

x0pa AI. (2024). *Predictive job matching: Definition, formula, types & components.*
https://x0pa.com/glossary/predictive-job-matching/

> "Skill-job alignment is the dominant challenge in vocational employment; skills
> carry the most weight in determining candidate suitability for entry-level and
> vocational positions."

Yusuf, A., Ibrahim, A., & Adeyemo, A. (2025). Machine learning-powered skill-job
matching recommendation system for vocational education. *Journal of Computer and
Mathematics Science Education.*
https://www.researchgate.net/publication/396961671

---

### Work Experience — 20%

> "Relevant experience: 25–35%; weight decreases for entry-level roles where skills
> and education are stronger signals than prior employment history."

x0pa AI. (2024). *Predictive job matching: Definition, formula, types & components.*
https://x0pa.com/glossary/predictive-job-matching/

---

### Education — 10%

Education is the lowest-weighted qualification field for PESO's predominantly
entry-level and vocational placements, where practical skills and work experience
carry more predictive weight than formal educational attainment.

> "Education level is a core matching criterion in content-based job recommender
> systems, ranked third after skills and experience in predictive importance."

Deldjoo, Y., Schedl, M., & Knees, P. (2025). Job recommender systems: A systematic
literature review, applications, open issues, and challenges. *Journal of Big Data,
12*(1). https://doi.org/10.1186/s40537-025-01173-y

---

### Location — 5%

Location is the lowest-weighted scoring field. Multiple sources treat it as a soft
tiebreaker rather than a competency indicator.

> "Location: 0–5% of the total matching score; treated as a soft preference rather
> than a hard competency requirement."

x0pa AI. (2024). *Predictive job matching: Definition, formula, types & components.*
https://x0pa.com/glossary/predictive-job-matching/

---

### Gender and Age — Binary Constraint Flags (Not Scored)

Gender and age are treated as eligibility constraint flags shown as warnings in the
UI. They are not included in the weighted score because they are demographic
boundaries, not competency indicators.

> "Age and gender are used as pre-filters to remove ineligible candidates; including
> them in a weighted score would penalize match percentage on demographic grounds."

Siah, K. W., & Lo, A. W. (2023). A comprehensive survey of artificial intelligence
techniques for talent analytics. *arXiv preprint arXiv:2307.03195.*
https://arxiv.org/pdf/2307.03195

> "Gender and age function as constraint boundaries in person-job fit; they
> determine eligibility, not degree of match."

Luo, X., Liu, Y., Liu, J., & Liu, X. (2022). Toward a traceable, explainable, and
fair JD/resume recommendation system. *arXiv preprint arXiv:2202.08960.*
https://arxiv.org/pdf/2202.08960

---

## Weight Summary

| Field                   | Weight | Role            |
|-------------------------|--------|-----------------|
| Job Title (token match) | 40%    | Weighted score  |
| Skills (Jaccard)        | 25%    | Weighted score  |
| Work Experience (ratio) | 20%    | Weighted score  |
| Education (ordinal)     | 10%    | Weighted score  |
| Location (binary)       | 5%     | Weighted score  |
| Gender                  | —      | Constraint flag |
| Age                     | —      | Constraint flag |

---

## Minimum Score Threshold

Vacancies with a CB score below **0.50 (50%)** are excluded from the recommendation
list entirely. A score of 0.50 represents the midpoint of the similarity scale and
is the most consistently cited minimum boundary in content-based filtering literature.
Falling below this point means the applicant does not satisfy the weighted majority
of the vacancy's requirements, and the vacancy is therefore not a genuine
recommendation.

The 0.50 threshold is adopted directly from two peer-reviewed job recommendation
studies:

> "A similarity threshold of 0.5 is the most commonly cited baseline in
> content-based filtering — items below this threshold are considered too dissimilar
> to recommend."

Isinkaye, F. O., Folajimi, Y. O., & Ojokoh, B. A. (2022). Job recommendation system
using hybrid filtering. *ITM Web of Conferences, 44*, 02002.
https://doi.org/10.1051/itmconf/20224402002

> "Match score is calculated and job listings are displayed only in descending order
> of match percentage — vacancies below the threshold are excluded from the
> recommendation list presented to the jobseeker."

Langer, T., & Scherp, A. (2022). Technical job recommendation system using APIs
and web crawling. *Applied Sciences, 12*(13), 6367.
https://pmc.ncbi.nlm.nih.gov/articles/PMC9239795/

Both sources address job-specific recommendation systems, not general recommender
theory, making 0.50 the appropriate and literature-consistent threshold for this
system. No domain adjustment above 0.50 is applied, as no peer-reviewed source
specific to employment referral systems establishes a higher value as standard.

**Behavior when no vacancy passes the threshold:**
The recommendation list is empty and the system displays:
*"No vacancies currently match your profile. Update your profile or check back
when new vacancies are posted."*
This prevents jobseekers from applying to vacancies for which they are not
sufficiently qualified, consistent with the panel's requirement that
recommendations reflect genuine suitability.

---

## Scoring Methods per Field

### Skills — Jaccard Similarity

```
s_skills = |Applicant Skills ∩ Required Skills| / |Required Skills|
```

Result is 0.0 to 1.0. A perfect skills match = 1.0.

### Work Experience — Ratio Scoring

```
s_exp = applicant_months / required_months   (capped at 1.0)
```

Partial credit is given proportionally. Exceeding the requirement = 1.0.

### Education — Ordinal Comparison

Levels ordered: Elementary < High School < Vocational < College Level <
College Graduate < Post-Graduate.

Applicant meets or exceeds requirement = 1.0. Below requirement = 0.0.

### Job Title — Token Overlap (Jaccard on word tokens)

```
s_title = |title_tokens ∩ preferred_tokens| / |title_tokens ∪ preferred_tokens|
```

### Location — Binary

```
s_loc = 1.0 if preferred location matches vacancy location, else 0.0
```

---

## Worked Example

**Applicant Profile:**
Skills: Java, SQL | Education: College Graduate | Experience: 10 months |
Preferred Position: Office Encoder | Preferred Location: CSJDM

**Vacancy:**
Required Skills: Java, SQL, Python | Min Education: College Graduate |
Min Experience: 12 months | Job Title: Data Encoder | Location: CSJDM

| Field       | Weight | Computation              | Score   | Weighted |
|-------------|--------|--------------------------|---------|----------|
| Skills      | 40%    | 2 ∩ 3 / 3                | 0.6667  | 0.2667   |
| Experience  | 25%    | 10 / 12                  | 0.8333  | 0.2083   |
| Education   | 20%    | Grad ≥ Grad              | 1.0000  | 0.2000   |
| Title       | 10%    | "encoder" overlap        | 0.5000  | 0.0500   |
| Location    | 5%     | CSJDM = CSJDM            | 1.0000  | 0.0500   |
| **Total**   |        |                          |         | **0.7750 = 77.5%** |

A perfect match on all fields = **100%**.

---

## APA References

Al-Otaibi, S. T., Al-Zamil, A. M., & Aljumaah, A. (2022). Learning-based matched
representation system for job recommendation. *Computers, 11*(11), 161.
https://doi.org/10.3390/computers11110161

Deldjoo, Y., Schedl, M., & Knees, P. (2025). Job recommender systems: A systematic
literature review, applications, open issues, and challenges. *Journal of Big Data,
12*(1). https://doi.org/10.1186/s40537-025-01173-y

Isinkaye, F. O., Folajimi, Y. O., & Ojokoh, B. A. (2022). Job recommendation system
using hybrid filtering. *ITM Web of Conferences, 44*, 02002.
https://doi.org/10.1051/itmconf/20224402002

Langer, T., & Scherp, A. (2022). Technical job recommendation system using APIs
and web crawling. *Applied Sciences, 12*(13), 6367.
https://pmc.ncbi.nlm.nih.gov/articles/PMC9239795/

Luo, X., Liu, Y., Liu, J., & Liu, X. (2022). Toward a traceable, explainable, and
fair JD/resume recommendation system. *arXiv preprint arXiv:2202.08960.*
https://arxiv.org/abs/2202.08960

NextMantra AI. (2026). *AI candidate matching: How scoring algorithms work.*
https://nextmantra.ai/blog/ai-candidate-matching-explained

Siah, K. W., & Lo, A. W. (2023). A comprehensive survey of artificial intelligence
techniques for talent analytics. *arXiv preprint arXiv:2307.03195.*
https://arxiv.org/abs/2307.03195

x0pa AI. (2024). *Predictive job matching: Definition, formula, types & components.*
https://x0pa.com/glossary/predictive-job-matching/

Yusuf, A., Ibrahim, A., & Adeyemo, A. (2025). Machine learning-powered skill-job
matching recommendation system for vocational education. *Journal of Computer and
Mathematics Science Education.*
https://www.researchgate.net/publication/396961671
