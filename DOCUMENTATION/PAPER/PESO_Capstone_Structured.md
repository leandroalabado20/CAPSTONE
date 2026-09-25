# A Web-Based Data-Driven Job Recommendation System with Dashboard for PESO CSJDM

A Capstone Project by

Alabado, Leandro M.
Nebereja, John Laurence R.
Nimbra, Luis Paolo L.
Poquiz, Lance Andrei P.
Referuga, Kristel

Submitted to the Faculty of Information Technology
Bulacan State University–Sarmiento Campus

In Partial Fulfillment
of the Requirements for the Degree
Bachelor of Science in Information Technology
Major in Data and Business Analytics

2026

---

# CHAPTER I
## INTRODUCTION



### Background of the Study

Job recommendation systems have become a widely adopted mechanism for connecting applicants to suitable employment opportunities across labor markets worldwide, offering faster and more consistent matching of applicant qualifications to available job openings than manual review alone can sustain (Ertuğrul & Bitirim, 2025).

Employment offices are among the most direct settings for implementing job recommendation systems, where staff manage daily referral decisions by manually cross-referencing applicant profiles against vacancy lists without structured decision support (Najjar et al., 2021; Sacchi & Scarano, 2025).

In the Philippines, this need is addressed through the Public Employment Service Office, established under Republic Act No. 8759 (1999), which mandates free employment facilitation, including job referrals and placement services, to Filipino job seekers nationwide. PESO offices accumulate years of applicant records and placement data through daily operations, yet the systems managing those records remain focused on storage rather than on using that history to support referral decisions (Bachita & Bayoneta, 2021).

An interview conducted by the researchers at the Public Employment Service Office of the City of San Jose del Monte, Bulacan confirmed an operational challenge as an active daily burden. On a regular day, the office receives an average of 15 walk-in applicants, rising to 20 to 75 during recruitment activities. For every applicant, staff must manually pull up the applicant's profile, consult the active vacancy list separately, and decide on a referral based entirely on personal judgment, with no tool to narrow down the options of job openings that best fit the applicant. As applicant volume grows throughout the day, the process slows, the queue lengthens, the office becomes crowded, and staff are exhausted by the same repetitive referral steps repeated for every person in the queue.

The same assessment revealed a second difficulty in reporting. When staff need to produce a picture of the office's applicant pool, such as the count of applicants by age group, educational attainment, or skills profile, no consolidated view is available through PEIS. Every figure must be produced by sorting and filtering records one category at a time, a repetitive process that consumes time the office does not have and delays the submission of required reports. Both difficulties point to the same underlying need: a system that consolidates applicant data into a unified dashboard and provides structured, ranked job recommendations to replace the manual cross-referencing that currently governs every referral decision at the office.

The most pressing of these needs is the referral burden itself. Staff need a web-based system that reduces the time and effort required to match applicants to available vacancies, giving them a structured basis for every referral decision rather than relying on recall alone. Yet building that system introduces a second problem that the literature has not resolved. Studies applying supervised text classification for job recommendation consistently identify Logistic Regression, Random Forest, and Naïve Bayes as leading classifiers, but no agreement exists on which performs best because results shift with every change in dataset (Betrand et al., 2025; Darma et al., 2026), and none of these studies have used PESO placement data despite every PESO office nationwide operating on the same PEIS records (Bachita & Bayoneta, 2021). A third problem follows once the system is built, as it remains unanswered whether it meets established software quality standards and whether the staff expected to rely on it daily would actually adopt it. This study addresses all three by developing the system, identifying the best-performing classifier on PESO CSJDM data, and evaluating both quality and readiness for adoption.

### Objectives of the Study

The general objective of this study is to develop and evaluate a web-based data-driven job recommendation system with dashboard for PESO CSJDM.

Specifically, the study aims to:

1. Design, develop, and deploy a web-based data-driven job recommendation system with dashboard for PESO CSJDM.

2. Implement the best-performing classification algorithm, as determined through a comparative evaluation of Logistic Regression, Random Forest, and Naïve Bayes.

3. Evaluate the developed system using ISO/IEC 25010:2023 and the Technology Acceptance Model (TAM).


### Significance of the Study

This study contributes to three areas: the operational improvement of a specific government employment office, the broader question of how Philippine public employment offices can adopt data-driven decision support using records they already hold, and the research literature on algorithm selection for employment recommendation in government contexts. The following groups stand to benefit from these contributions.

**PESO CSJDM Staff.** As the primary users and host institution, PESO CSJDM and its staff benefit most directly. The system reduces the time and effort required to match applicants to available vacancies by providing a ranked list of suitable job openings with suitability scores, giving staff a structured and quantified basis for every referral decision rather than relying on recall alone. At the institutional level, the Analytical Dashboard gives the office a data-driven picture of its registrant pool through registrant counts, sex distribution, youth, senior citizen, and PWD tallies, educational attainment distribution, employment status, and barangay breakdown by district, supporting the preparation of the office's quarterly job seeker reports and program planning.

**Job Seekers.** Job seekers registered at PESO CSJDM benefit indirectly through a faster referral queue. The system does not interact with job seekers directly, but by reducing the time staff spend on each referral decision, it shortens the queue and decreases the waiting time experienced by every walk-in applicant, particularly during high-volume recruitment days when the office receives up to 75 applicants in a single day.

**Other PESO Offices Nationwide.** The operational problem at PESO CSJDM is not unique to one city. Other PESO offices facing the same referral challenges can look to this study as a documented reference for what a similar system looks like, how it performs, and which algorithm to adopt when building one for their own placement data, without repeating the comparison from scratch.

**Future Researchers.** The study contributes the first empirical comparison of Logistic Regression, Random Forest, and Naïve Bayes on the operational placement records of a Philippine public employment office, together with a replicable development process and a dual ISO/IEC 25010:2023 and TAM evaluation framework, giving future researchers a grounded starting point for studying job recommendation in government contexts where data is small, imbalanced, and operationally collected.

### Scope and Delimitations

The study covers the development and evaluation of a web-based data-driven job recommendation system with dashboard for PESO CSJDM, designed for use by PESO staff as the sole user role with a single access level. The system operates through two main analytics tabs: the Job Recommendation tab and the Analytical Dashboard tab, supported by Applicant Management and Job Vacancy Management modules for data entry and maintenance. The recommendation engine is trained on historical placement records from PESO CSJDM, comparing Logistic Regression, Random Forest, and Naïve Bayes using TF-IDF vectorization, with the algorithm achieving the highest Macro F1-Score deployed as the active model. The system is accessible through a responsive web interface supporting both desktop and mobile browsers. Development and evaluation are conducted within the operational context of the City of San Jose del Monte, Bulacan, using PESO CSJDM records only. The system operates in English only.

**Delimitations.** The study does not propose a novel job recommendation algorithm; it applies established supervised text classification techniques drawn from the existing literature, specifically TF-IDF vectorization paired with Logistic Regression, Random Forest, and Naïve Bayes, to the operational placement records of PESO CSJDM. The system matches job seekers to available vacancies in one direction only and does not recommend applicants for a given vacancy. Job seekers do not interact with the system directly and cannot register or create accounts. Referral recording, the act of logging which vacancy a staff member referred an applicant to, remains handled by PESO staff through PEIS; the system generates and logs its ranked recommendation outputs but does not record the actual referral outcome; the staff member's final decision on which vacancy to refer an applicant to is recorded in PEIS, not in this system. Placement outcome tracking and long-term employment outcomes such as hiring confirmation, retention, and career progression are outside the system's scope. The system does not integrate with PEIS directly through any API or real-time data sync; PEIS exports are uploaded manually by staff as Excel files. Notifications of any kind, including email, SMS, and in-app alerts, are not supported. The ML model is trained offline by the research team prior to deployment and cannot be retrained from within the web interface. The recommendation engine covers only the five occupational categories present in the historical placement records, and broadening coverage to the full range of posted vacancy titles is identified as future work. Advanced approaches including gradient boosting, stacking, deep learning, and large language model-based matching are excluded. The system is not designed for direct deployment in other PESO offices without retraining on local data, does not support multiple branches or offices, and was evaluated at a single point in time in a controlled local environment, not during live PESO operations. The analytical dashboard presents data from stored records only and does not reflect real-time updates.

**Limitations.** The volume of usable labeled records is limited to confirmed placements the office has historically documented, and those records are heavily concentrated in a small number of occupational categories, which bounds the classification performance achievable by any algorithm. The system also depends on the field structure of PEIS exports for batch upload, and changes to that format would require corresponding adjustment of the upload mapping. Local-only deployment means the system is not accessible outside the office network without additional infrastructure. Because the recommendation engine scores vacancies at the occupational category level, all vacancies belonging to the same category receive an identical suitability score for a given applicant profile. When multiple vacancies are tied at the same score, the system does not apply a secondary ranking criterion; their relative order within the tied group is determined by the order in which they were added to the database. This behavior is an acknowledged limitation: a more granular ranking, for instance one that accounts for word overlap between the job title and the applicant's preferred position or work experience, would require a training signal at the job-title level, which the available placement records do not support.

### Definition of Terms

The following terms are defined operationally, as they are used in the present study, and are arranged alphabetically.

**Analytical Dashboard.** The system module that presents registered job seeker data drawn from the applicants table. It covers total registrants with male and female breakdown, counts of youth, senior citizen, and person with disability registrants, distribution by educational attainment across ten levels, distribution by employment status, and barangay-level distribution separated by District 1 and District 2. Job vacancy records are used only by the recommendation engine and are not aggregated in the dashboard. The dashboard supports the preparation of the office's quarterly job seeker reports.

**Applicant Profiling.** The process of organizing a job seeker's competency profile, including skills, educational attainment, work experience, and preferred position, into a structured format for classification. The system uses this structured profile to rank suitable job openings by suitability score.

**Decision Support System (DSS).** A computer-based system that assists users in making informed decisions by processing and presenting relevant data in a structured format. In this study, the system supports PESO staff in referral decisions while retaining staff authority over every final outcome.


**ISO/IEC 25010.** An international standard for software product quality used in this study to evaluate the system across nine characteristics: functional suitability, performance efficiency, compatibility, interaction capability, reliability, security, maintainability, flexibility, and safety (Rojas et al., 2025).

**Job Recommendation Module.** The system module that applies the trained classification pipeline to a selected applicant's profile and ranks currently active vacancies by suitability score.

**Job Referral.** The act of connecting a registered job seeker to a specific employer or job opening based on qualifications, carried out by a PESO staff member as part of the office's employment facilitation mandate.

**Machine Learning.** A field of artificial intelligence in which algorithms learn patterns from historical data and apply those patterns to new inputs. In this study, a machine learning pipeline trained on PESO CSJDM placement records powers the Job Recommendation Module.

**Macro F1-Score.** The unweighted average of per-class F1-Scores, giving each occupational category equal importance regardless of how many records it contains. Used as the primary algorithm selection criterion because it exposes weak performance on under-represented categories that overall accuracy conceals (Opitz, 2024).

**Occupational Category.** A broader grouping of related job titles used as the target label for the classification model. In the present study, 88 distinct job position titles from the PESO CSJDM historical placement records are consolidated into five occupational categories: Warehouse and Logistics, Production and Manufacturing, Sales/Service/Retail, Clerical and Administrative, and General Services and Security. Consolidation is necessary because individual job titles are too sparsely represented in the dataset for a valid stratified train-test split.

**Philippine Employment Information System (PEIS).** The existing recordkeeping system used by PESO offices to store and retrieve applicant and employer information. The proposed system complements PEIS without replacing it as the office's primary system of record.

**Recommendation Engine.** The system component that applies the trained classification model to a job seeker's profile to identify and rank suitable job openings by suitability score.

**Technology Acceptance Model (TAM).** A framework for measuring technology adoption through three constructs: perceived usefulness, perceived ease of use, and behavioral intention to use. In this study, TAM assesses how PESO CSJDM staff perceive and intend to adopt the developed system.

**TF-IDF (Term Frequency-Inverse Document Frequency).** A text vectorization method that converts a text document into a set of numerical weights by measuring how often each term appears in that document (term frequency) relative to how rarely it appears across all documents in the dataset (inverse document frequency). Terms that appear across nearly all documents receive lower weight because they carry little discriminating information; terms that appear in only a few documents receive higher weight because they are more distinctive. In the present study, TF-IDF transforms each applicant's concatenated profile text into a numerical feature vector as the first step of the classification pipeline.

---

# CHAPTER II
## REVIEW OF RELATED LITERATURE AND SYSTEMS

This chapter reviews literature and related systems that inform the design, algorithm selection, and evaluation of the proposed system. Five thematic areas are covered under the Review of Related Literature: the adoption of job recommendation systems by employment offices around the world, algorithm comparison studies that have examined the classifiers under consideration, data preprocessing approaches used in comparable systems, supervised machine learning approaches for job recommendation that directly inform the system design, and evaluation metrics for multi-class classification systems that establish the selection criterion used in the present study. Following the literature review, six related systems are described and compared in a structured table, examining how each system addressed the problem of matching applicants to positions and where each falls short relative to the conditions of the present study.

---

### Review of Related Literature

#### Job Recommendation in Employment Offices

A government employment platform operated by the state of Punjab in India integrated an AI-powered job recommendation system after an assessment confirmed that the existing portal imposed documented barriers that prevented effective vacancy matching: applicants encountered navigational complexity that deterred first-time users, were excluded by the absence of multilingual support, and were required to independently search the full inventory of posted vacancies without any personalized guidance, placing the entire burden of vacancy discovery on job seekers without any recommendation support. The resulting system served hundreds of thousands of registered job seekers in the state and integrated multilingual support in English, Hindi, and Punjabi alongside a profile-based recommendation engine that generated personalized ranked vacancy lists for each applicant, replacing the unassisted manual search process that had characterized the original platform. Assessed on the System Usability Scale and recommendation precision metrics, the deployment achieved a System Usability Scale score of 78.5 out of 100, a Precision@10 recommendation score of 68%, and a factual accuracy rate of 94%, collectively representing a 50% improvement in platform usability over the unaugmented baseline, results that demonstrate how integrating job recommendation into a government employment platform significantly improved the vacancy matching workflow by replacing unguided manual search with a structured, profile-driven recommendation process. This evidence directly establishes the viability of the same transformation for PESO CSJDM, where staff currently perform the functional equivalent of that unstructured process for every walk-in applicant, manually cross-referencing each applicant's profile against the full vacancy list without any recommendation tool, and where introducing a structured recommendation system represents a justified, evidence-backed improvement to the office's daily referral workflow (Srihari et al., 2025).

A randomized controlled trial conducted with over 1,250 job seekers, in partnership with a public employment service, directly measured whether automated job recommendations integrated into an employment platform produce a measurable improvement in the employment office's core operational function: connecting job seekers to suitable positions. The trial evaluated two recommendation approaches under controlled conditions, one that aligned suggestions with each applicant's prior occupational history, and one that derived recommendations from an assessed skill profile rather than past employment, enabling matches beyond previously held job titles and accommodating applicants whose prior roles did not reflect their full competencies. Evaluated on job finding rates as the primary outcome measure, both recommendation types improved job finding rates on average, with profile-based recommendations producing the strongest gains for applicants with limited work experience or mismatch between prior employment and assessed skills, the population most commonly served by walk-in government employment offices. The trial result that automated, profile-based recommendations produced a measurable improvement in employment outcomes at a public employment service provides direct empirical evidence that structured job recommendation systems make a quantifiable, real-world difference in the effectiveness of government employment office workflow, not only in technical performance metrics but in the actual employment results delivered to job seekers. This finding directly supports the design and rationale of the proposed system at PESO CSJDM, where applicant profiles covering skills, education level, work experience, and preferred position are used to generate ranked vacancy recommendations for staff to use in referral decisions, addressing the same operational gap the trial identified: providing structured, profile-based matching to entry-level and first-time job seekers who constitute a significant share of the office's daily walk-in applicants (Bächli et al., 2025).

A field experiment conducted in partnership with a public employment service evaluated whether providing unemployed job seekers with structured occupational recommendations, specifically suggestions for suitable alternative occupations alongside comparative information about the employment prospects of those alternatives relative to each applicant's initial target occupation, produced measurable improvements in employment outcomes compared to job seekers who received no such recommendations. The intervention was directed at job seekers registered in occupations with limited vacancy availability, a circumstance in which the absence of recommendation support most directly constrains an applicant's ability to find suitable work, and the study found that the vast majority of treated job seekers engaged with the occupational recommendation messages they received. Evaluated at an 18-month follow-up, the experiment found that employment, hours of work, and labor income each improved by 5 to 6 percent among job seekers who received occupational recommendations relative to the untreated control group, a result that demonstrates that structured occupational recommendations provided through a public employment service produced a quantifiable, real-world improvement in the employment office's core function of connecting job seekers to suitable work. This finding reinforces the operational case for the proposed system at PESO CSJDM: staff currently match each walk-in applicant against available vacancies using only manual judgment without any recommendation tool to surface better-matched alternatives, and the 5 to 6 percent employment improvement measured in this trial establishes that replacing unstructured manual matching with structured occupational recommendations at a public employment service produces real, measurable gains in the outcomes that employment offices exist to deliver (Belot et al., 2025).

#### Algorithm Comparison for Employment Recommendation

K-Nearest Neighbors and Naïve Bayes were evaluated in a career path recommendation system built from 22 assessment indicators spanning academic interests, learning style, and preferred work environment, collected through questionnaires from 300 respondents. The dataset was divided 80/20 for training and testing, and both algorithms were evaluated on accuracy, precision, recall, and F1-score under identical conditions. Naïve Bayes outperformed KNN, achieving 97% accuracy alongside 93% precision, recall, and F1-score, while KNN produced lower values across all four metrics. The authors attributed the Naïve Bayes advantage to its probabilistic structure, which handled the feature independence in questionnaire-based profile data more effectively than the distance-based KNN approach. Among the algorithms compared, Naïve Bayes was identified as the best-performing algorithm (Darma et al., 2026).

A large-scale benchmark study on resume classification constructed a dataset of 13,389 resumes distributed across 43 occupational categories and applied TF-IDF feature extraction to three supervised classifiers, Multinomial Naïve Bayes, Logistic Regression, and Random Forest, under identical training and evaluation conditions. Performance was measured using both accuracy and Macro F1-Score across all 43 categories, ensuring that no category was overweighted in the final comparison. Multinomial Naïve Bayes achieved the highest Macro F1-Score at 82.8% and the highest accuracy at 81.3%, followed by Logistic Regression at 80.6% Macro F1 and 79.8% accuracy, while Random Forest produced the lowest scores at 78.6% Macro F1 and 78.5% accuracy. This result stands in contrast to Betrand et al. (2025), where Random Forest dominated both alternatives on a smaller career guidance dataset, demonstrating that the performance ranking of the three algorithms shifts with every change in data domain and scale. This variation directly motivates the empirical comparison in the present study: rather than adopting a prior literature ranking, an independent evaluation on the actual PESO CSJDM placement records is necessary to determine which algorithm best captures the occupational classification patterns in government employment data (Heakl et al., 2024).

Supervised classification applied to student educational profiles compared Decision Tree, Random Forest, and Naïve Bayes to determine which best classifies a profile to a suitable career trajectory. The study employed SelectKBest feature selection to identify and retain the most discriminative profile attributes before passing the reduced feature set into each classifier. Performance was assessed across accuracy, precision, recall, and F1-score on the same dataset, with Decision Tree and Naïve Bayes producing lower scores across all four metrics. Among the algorithms compared, Random Forest was identified as the best-performing algorithm, though the study relied on a clean, balanced educational dataset, leaving open whether this advantage holds under limited records and heavy category concentration common in government employment data (Betrand et al., 2025).

#### Data Preprocessing Approaches in Job Recommendation Literature

Feature selection in profile-based job recommendation has consistently been anchored in structured profile attributes rather than interaction or behavioral logs. A content-based job recommendation system built to match job seekers to appropriate vacancies used exclusively structured profile text attributes, education level, declared skills, personal interests, salary expectation, and preferred job location, as the feature base for computing applicant-to-vacancy similarity through TF-IDF vectorization and cosine similarity. The system required no ratings, clickstream data, behavioral logs, or prior application history from users to generate recommendations, demonstrating that structured profile text content is a sufficient and appropriate input for employment matching even when interaction data is absent. Evaluated on a test set, the system achieved a Mean Average Precision (MAP) of 0.798, confirming that profile-text-only content-based matching produces reliable recommendation outputs. This operating condition is structurally identical to that of PESO CSJDM: the office collects structured profile text from walk-in applicants through daily registration but maintains no ratings system, no application history database, and no clickstream records, making a profile-text-based classification approach the most appropriate design for the PESO recommendation engine (Winardi et al., 2025).

Sparse job title labels are a documented challenge in employment classification datasets. A data-centric study on automated occupation coding of job advertisements examined how label granularity affects classification performance, using hierarchical International Standard Classification of Occupations (ISCO) codes applied to multilingual job postings. The study found that models trained on fine-grained 6-digit ISCO codes, which distinguish hundreds of specific job titles, produced substantially lower classification accuracy than models trained on broader 1-digit or 2-digit occupational groupings applied to the same data, because fine-grained codes contain too few training examples per-class for the model to learn reliable patterns. Transitioning from fine-grained to broader occupational groupings consistently improved classification accuracy by approximately 1 to 2 percentage points. This finding directly informs the PESO data preparation decision: the raw placement records contain 88 unique job position values, many appearing in only one or two records, which is insufficient for any classifier to learn reliable patterns at the individual title level. All 88 job titles are therefore consolidated into five occupational categories, Warehouse and Logistics, Production and Manufacturing, Sales/Service/Retail, Clerical and Administrative, and General Services and Security, ensuring each class contains enough records for a valid stratified train-test split and that the model learns from categories with sufficient representation (Beręsewicz et al., 2024).

Preprocessing of applicant profile text for job recommendation has been implemented by treating combined user profile content as a single processable text unit rather than encoding each attribute separately. A job recommendation system applied text cleaning, including stop-word removal and HTML tag stripping, to user profile text covering declared skills, interests, and preferred job areas, then computed TF-IDF document vectors from the combined profile text and matched them against vectorized job descriptions through cosine similarity. By treating all profile attribute content as one unified text document for vectorization, the system avoided the need for separate categorical or numerical encoding of individual profile fields before matching. This preprocessing principle informs the feature construction step in the present study: four profile fields collected from PESO CSJDM applicants, education level, preferred position, skills, and work experience, are concatenated into a single profile text string per applicant record before TF-IDF vectorization, creating a unified text representation from which the vectorizer learns the 356 discriminative terms that power the classification model (N. Kumar et al., 2022).

#### Supervised Machine Learning Approaches for Job Recommendation

A job-candidate matching system was developed whose text classification pipeline closely mirrors the approach adopted in the present study. CVs in PDF, DOCX, and plain-text formats were cleaned through lowercasing, punctuation removal, stop-word filtering, and lemmatization before TF-IDF vectorization produced term-weighted feature vectors from the standardized text. A Random Over Sampler resolved class imbalance in the 1,428 LinkedIn CV dataset prior to training six classifiers, namely Logistic Regression, Random Forest, SVM, k-Nearest Neighbors, Gradient Boosting, and Naïve Bayes, each assessed on accuracy, precision, recall, and F1-score on an 80/20 split. SVM achieved the best results at 96.38% accuracy and 96.40% F1-score, with Logistic Regression second at 94.68%, Random Forest at 89.57%, and Naïve Bayes at 80.96%. The study's final stage applies cosine similarity to rank full job description vectors, a step requiring rich vacancy text unavailable in PESO records, which contain only employer name and job title. The present study replaces this step with predict_proba probability estimates from the best-performing classifier, using each category's confidence score as the vacancy suitability signal. The shared structure of preprocessing, TF-IDF vectorization, and multi-classifier comparison, combined with the presence of Logistic Regression, Random Forest, and Naïve Bayes in the results, directly supports adopting this pipeline design for PESO placement data and establishes a reference baseline for interpreting classifier performance on government records (Chihab et al., 2025).

A study on civil servant recruitment demonstrated that a government office's own administrative records are sufficient for supervised employment classification, applying three classifiers to 2,490 applicant records from Indonesia's Ministry of Finance (Kementerian Keuangan) 2024 recruitment cycle. The dataset consisted of scores from the agency's official assessment battery, including national insight tests, general intelligence evaluations, and personal characteristics and work orientation ratings, sourced directly from the government system rather than from external questionnaires or self-reported inputs. Logistic Regression, Random Forest, and XGBoost were trained and compared using accuracy as the primary metric; XGBoost led at 98.09%, followed by Random Forest at 97.79%, while Logistic Regression recorded 78.97%, confirming that classifier families yield clearly distinct and interpretable results on institutional government data. The structural alignment with the present study is direct: both rely exclusively on a government agency's existing operational records for training, both compare classifier families that include Logistic Regression and Random Forest, and neither requires external data sources, user ratings, or behavioral logs. This validates the present study's decision to train solely on PESO CSJDM historical placement records and confirms that the classifiers evaluated will produce differentiated and meaningful performance outcomes on government-collected applicant data (Adillah et al., 2026).

A comparative evaluation of CNN against seven traditional classifiers for job recommendation provided, through its documentation of the traditional approach, a step-by-step account of TF-IDF as a feature extraction method for occupational text. The pipeline proceeds through text normalization and stop-word removal, tokenization, term frequency measurement as a within-document ratio, inverse document frequency weighting to penalize terms common across the corpus, multiplication of both values to produce a per-term importance score, construction of term-weighted document vectors, and cosine similarity ranking of candidates against vacancy content. Among eight methods evaluated, specifically CNN, Gradient Boosting, AdaBoost, Random Forest, Decision Tree, Logistic Regression, Naïve Bayes, and Linear Regression, CNN achieved the highest performance at 0.97 accuracy and F1-score; among traditional classifiers, Random Forest led at 0.82, followed by Decision Tree at 0.80, Logistic Regression at 0.79, and Naïve Bayes at 0.74. The cosine similarity step is not applicable to the present study because PESO vacancy records contain only employer name and job title rather than full description text; predict_proba outputs from the trained classifier serve as the vacancy ranking signal instead. The study's detailed TF-IDF documentation establishes it as a transparent and replicable method for occupational text data, and the measured performance ordering of Logistic Regression, Random Forest, and Naïve Bayes provides a reference ranking for interpreting the same classifiers' comparative results on PESO placement records (Tiwari & Upadhyay, 2024).

An alternative design for job recommendation applies TF-IDF and cosine similarity within a content-based filtering framework, constructing term-weighted vectors from job seeker profiles and vacancy records then ranking matches by the angular distance between those vectors across multiple criteria including salary, education, skills, interests, and location. Implemented in Python using Scikit-learn, this system achieved a Mean Average Precision score of 0.798, confirming that TF-IDF vectorization is an effective feature extraction method for profile-to-vacancy matching when both sides of the comparison contain sufficient descriptive text for vector construction. Content-based filtering through cosine similarity is therefore an established alternative to supervised classification for job recommendation, but its effectiveness depends entirely on the descriptive richness of the vacancy records being vectorized. PESO CSJDM vacancy records contain only employer name and job title, providing insufficient text for a meaningful cosine similarity computation between an applicant profile vector and a vacancy vector. Supervised classification does not carry this constraint: the trained classifier maps an applicant's profile text to occupational category probabilities using patterns learned from historical placement records, and those probabilities rank active vacancies directly without requiring matching text on the vacancy side. The present study adopts supervised classification over content-based filtering precisely because the approach operates within the data structure of PESO records, where the vacancy side of the matching pair lacks the descriptive content that cosine similarity requires (Winardi et al., 2025).

#### Evaluation Metrics for Supervised Classification-Based Recommendation Systems

An analytical overview of classification performance metrics for multi-class settings established precise distinctions between accuracy, Micro F1-Score, and Macro F1-Score and their behavior when class frequencies are unequal. The study found that accuracy "tends to hide strong classification errors for classes with few units, since those classes are less relevant compared to the biggest ones," meaning a classifier that fails entirely on a minority class can still record a high accuracy score because minority class errors represent a small fraction of all test records. Micro F1-Score was shown to be mathematically "just equal to Accuracy," carrying the same limitation: both are dominated by the classes that contribute the most samples, leaving minority class performance effectively invisible in the final score. Macro F1-Score, computed as the unweighted average of per-class F1-Scores, corrects this by giving "each class the same weight in the average, so that there is no distinction between highly and poorly populated classes," with high Macro F1-Score values indicating that "the algorithm has good performance on all the classes." These distinctions directly determine the evaluation design of the PESO system: the five occupational categories range from 317 records in Sales/Service/Retail (29.3%) to 149 records in Clerical and Administrative (13.8%) and 150 records in General Services and Security (13.9%). Under accuracy or Micro F1-Score, a model that fails entirely on Clerical or Security positions would still record a high overall score because those two categories together account for less than 28% of all records, and a deployed recommender that cannot correctly rank administrative or security vacancies for applicants in those groups would fail a measurable share of PESO CSJDM's daily walk-in applicants without any warning appearing in the aggregate metric. Macro F1-Score is therefore selected as the sole algorithm selection criterion, computing the F1-Score for each of the five occupational categories separately and averaging them with equal weight, ensuring that failure on the smallest category is penalized as severely as failure on the largest (Grandini et al., 2020).

---

### Review of Related Systems

A web-based job recommendation system applies TF-IDF vectorization to extract term-weighted feature vectors from job descriptions and user profiles, then compares eight machine learning methods to determine which produces the most accurate job-to-candidate matches. The preprocessing pipeline cleans and tokenizes text, removes stopwords, applies stemming, and computes TF-IDF scores for each term before constructing a similarity matrix between user profiles and job postings. Eight algorithms were trained and evaluated under the same conditions: Convolutional Neural Network, Random Forest, Logistic Regression, Linear Regression, Decision Tree, Naïve Bayes, AdaBoost, and Gradient Boosting, with performance measured across accuracy, precision, recall, and F1-score. The CNN achieved the highest scores (accuracy 0.97, F1-score 0.97), followed by Gradient Boosting (0.88), AdaBoost (0.85), and Random Forest (0.82), while Logistic Regression recorded 0.79 in both accuracy and F1-score, and Naïve Bayes recorded 0.74 in both metrics. The study demonstrated that a TF-IDF vectorization pipeline followed by multi-algorithm comparison is a replicable and effective design for job recommendation, and that performance gaps among classical classifiers become measurable and consistent when the feature extraction method is held constant across all models (Tiwari & Upadhyay, 2024).

ResuméAtlas is a resume classification system designed to improve automated candidate screening in online recruitment platforms by applying large language models to classify resumes into job categories at scale. The system is built on a curated dataset of 13,389 resumes collected from diverse sources to address the limitations of small, non-standardized datasets that constrained prior resume classification research. BERT and Gemma1.1 2B were evaluated as classification backbones, achieving top-1 accuracy of 92% and top-5 accuracy of 97.5%, demonstrating measurable improvement over the traditional classifiers evaluated on the same dataset, where Multinomial Naïve Bayes led at 82.8% Macro F1, Logistic Regression at 80.6%, and Random Forest at 78.6%. Its strength lies in the scale and diversity of its training data and the representational capacity of transformer-based models for unstructured resume text. Its limitation for the PESO context is the computational and data requirement: LLM fine-tuning requires substantially larger datasets and GPU infrastructure than a single municipal employment office maintains, and the opacity of transformer-based models conflicts with the transparency expectations of a government referral tool. The proposed system addresses both constraints by using lightweight supervised classifiers trained on PESO CSJDM's 1,083 placement records without GPU infrastructure, producing probability-based outputs that staff can directly interpret as occupational suitability scores (Heakl et al., 2024).

A career guidance system applies supervised classification to student educational profiles and compares three classification algorithms to identify which best assigns a profile to a suitable career category. The system collects profile data covering skills and abilities, interests and passions, academic performance factors, and personality traits, and applies SelectKBest feature selection to retain only the most discriminative attributes before training the classifiers. Decision Tree, Random Forest, and Naïve Bayes were trained and evaluated on the same Mendeley career guidance dataset, with performance measured across accuracy, precision, recall, and F1-score alongside per-class confusion matrices. Random Forest outperformed both alternatives across all four metrics, while Decision Tree and Naïve Bayes produced lower scores. The system was deployed as a Django web application integrated with a chatbot component, demonstrating that a supervised ML classification pipeline can be embedded into a functional web interface with minimal infrastructure (Betrand et al., 2025).

JobSphere is an AI-powered career assistant built to augment Punjab's government employment portal PGRKAM, designed specifically for rural job seekers who face language and digital literacy barriers on standard government employment websites. The system provides voice-enabled job search, automated resume parsing with skills extraction, embedding-based job recommendations, and automated mock interview preparation, with multilingual support in English, Hindi, and Punjabi delivered through a Retrieval-Augmented Generation architecture optimized with 4-bit quantization for deployment on consumer-grade GPUs. Evaluations recorded a System Usability Scale score of 78.5 out of 100, a 50% improvement over the baseline portal, with 94% factual accuracy, 68% precision@10 for job recommendations, and a 1.8-second median response time at 89% lower cost than cloud-based equivalents. Its strength lies in multilingual accessibility and voice interaction for underserved populations. Its limitation for the PESO context is the dependency on large language model infrastructure; the RAG and embedding pipeline requires GPU hardware and LLM deployment that a single municipal office cannot maintain. The proposed system differs by operating entirely within a standard Flask web server using scikit-learn classifiers trained on local placement records, requiring no GPU or external language model services (Srihari et al., 2025).

A career path recommendation system for informatics undergraduates at Battuta University applies supervised classification to structured questionnaire responses, helping students identify the IT specialization best aligned with their declared interests, academic performance, and preferred work environment. Data were collected from 300 students through a 22-indicator assessment, split into 240 training and 60 test records. K-Nearest Neighbor and Naïve Bayes were trained and compared; Naïve Bayes achieved the higher performance at 97% accuracy, 93% precision, 93% recall, and 93% F1-score. The system demonstrates that lightweight classifiers trained on structured categorical profiles can achieve high accuracy for career-to-category matching in an institutional setting. Its limitation relative to the PESO system is the reliance on a purpose-built questionnaire instrument: respondents must complete a separate assessment, and the system cannot operate on existing operational records directly. The proposed system eliminates this step by training on historical placement records already held by PESO CSJDM, making TF-IDF vectorization of existing profile text the sole data input without any separate instrument administration (Darma et al., 2026).

I-Recruiter is an intelligent decision support system for HR professionals and recruiters that automates the screening and ranking of job applicants at scale. The system operates through three sequential modules: a training block that builds ML models from a labeled resume dataset, a matching block that aligns submitted resumes with target job descriptions using natural language processing and word embeddings, and an extracting block that ranks candidates in descending order of semantic similarity score computed via cosine distance using NLTK. The system reported high confidence and excellent performance in applicant ranking and targets HR departments managing large applicant volumes where manual review is impractical. Its limitation for the PESO context is the same structural constraint observed in cosine similarity-based systems: meaningful similarity computation between an applicant vector and a vacancy vector requires rich descriptive text on the vacancy side, which PESO records do not provide beyond employer name and job title. The proposed system addresses this by using predict_proba outputs from the trained classifier, deriving vacancy suitability from learned occupational category probabilities rather than direct resume-to-job-description semantic distance (Najjar et al., 2021).

---

### Comparison of Related Systems

**Table 2. Comparison of Related Systems**

| System | Purpose | Approach | Algorithms Compared | Best Performer | Dataset | Platform | Target Users |
|---|---|---|---|---|---|---|---|
| Tiwari & Upadhyay (2024) | Job-to-candidate matching | TF-IDF + supervised ML | CNN, RF, LR, DT, NB, AdaBoost, GB, Linear Reg | CNN (0.97 F1); RF best among classical (0.82) | Public job postings | Not specified | General job seekers |
| Heakl et al. (2024) | Resume classification for candidate screening | LLM fine-tuning (BERT, Gemma1.1 2B) | BERT, Gemma1.1 2B vs. traditional ML | BERT/Gemma (top-1 acc. 92%, top-5 acc. 97.5%) | 13,389 resumes (multi-source) | Not specified | Recruitment platform operators, HR tech providers |
| Betrand et al. (2025) | Student profile to career category | SelectKBest + classification | DT, RF, NB | Random Forest (all four metrics) | Mendeley career guidance dataset | Django web application | Students |
| Srihari et al. (2025) | Career assistance on government employment portal | RAG + LLM embeddings (voice-enabled, multilingual) | LLM-based; no classifier comparison | N/A; single architecture (68% precision@10) | Punjab PGRKAM portal listings | Consumer GPU (NVIDIA RTX 3050) | Rural job seekers (English/Hindi/Punjabi) |
| Darma et al. (2026) | Student career path recommendation | Questionnaire + ML classification | KNN, Naïve Bayes | Naïve Bayes (97% accuracy, 93% F1) | 300 student questionnaires (Battuta University) | Not specified | CS students |
| Najjar et al. (2021) | Resume screening and applicant ranking | NLP + word embeddings + cosine similarity | N/A; single approach | N/A; cosine similarity scoring | Labeled resume dataset | Decision support system | HR professionals and recruiters |
| **Proposed System** | **Applicant to active vacancy referral for PESO staff** | **TF-IDF + supervised ML classification** | **LR, RF, NB** | **To be evaluated** | **PESO CSJDM historical placement records** | **Flask web application** | **PESO CSJDM staff only** |

---

### Synthesis

The six related systems reviewed above collectively establish the landscape of job and career recommendation technology across government portals, academic institutions, and HR platforms, and together they define the design space within which the present study operates.

Three recurring patterns are evident across the six systems. First, all systems that compare classification algorithms, specifically Tiwari & Upadhyay (2024), Betrand et al. (2025), and Darma et al. (2026), reach different algorithm rankings depending on the data domain, a divergence reinforced in the literature review where Heakl et al. (2024) found Naïve Bayes outperforming Logistic Regression and Random Forest on TF-IDF features, reversing the ordering Tiwari & Upadhyay (2024) reported on a different dataset, confirming that no single classifier universally outperforms the others and that an independent empirical comparison on the actual target dataset is a necessary precondition for a reliable recommendation engine, not an optional step. Second, systems that depend on external infrastructure beyond a basic web server, such as Srihari et al. (2025) with its RAG and LLM pipeline and Heakl et al. (2024) with its GPU-intensive transformer fine-tuning, achieve strong benchmark results but impose hardware and operational requirements that a single municipal employment office cannot sustain. Third, systems that rely on cosine similarity for vacancy matching, specifically Tiwari & Upadhyay (2024) at inference and Najjar et al. (2021) throughout, presuppose that both the applicant profile and the vacancy record contain rich, comparable descriptive text, a condition that does not hold in PESO CSJDM vacancy records, which provide only employer name and job title.

The proposed system is designed to address these constraints directly. It adopts the same TF-IDF vectorization and multi-classifier comparison pipeline established by Tiwari & Upadhyay (2024) and validated by Betrand et al. (2025) and Darma et al. (2026), but grounds the comparison in actual PESO CSJDM placement data rather than in a transferred benchmark. It replaces cosine similarity ranking with predict_proba probability outputs from the deployed classifier, enabling vacancy ranking without requiring descriptive text on the vacancy side, as Najjar et al. (2021) required. It operates entirely within a standard Flask and scikit-learn stack, without the GPU infrastructure or LLM services that Srihari et al. (2025) and Heakl et al. (2024) depend on, making the system maintainable by a municipal government office. No related system examined was built on government-collected operational placement records from a Philippine PESO office; the present study is the first to do so, establishing an empirical baseline that other PESO offices can reference directly.

Unlike the related systems reviewed, which were built on general-purpose datasets such as scraped resumes (Heakl et al., 2024; Chihab et al., 2025), publicly available job postings (Tiwari & Upadhyay, 2024), or purpose-built questionnaire instruments (Darma et al., 2026), the proposed system is trained exclusively on PESO CSJDM's own operational placement records, making it the first system in the reviewed literature to use Philippine PESO data. Where systems such as Tiwari and Upadhyay (2024), Najjar et al. (2021), and Winardi et al. (2025) rank matches through cosine similarity, a method that requires rich descriptive text on the vacancy side, the proposed system uses predict_proba probability outputs from the trained classifier because PESO vacancy records contain only employer name, job title, and occupational category, which is insufficient for cosine-based matching. The system also operates without the GPU infrastructure that Srihari et al. (2025) and Heakl et al. (2024) depend on, runs on a standard Flask and scikit-learn stack suitable for a municipal government office, and directs its outputs to PESO staff rather than to job seekers directly, a user orientation not present in any of the six related systems reviewed. In addition, none of the related systems include an analytical dashboard; the proposed system integrates one to support the office's quarterly job seeker reporting requirements.

---

# CHAPTER III
## DESIGN AND METHODOLOGY

This chapter translates the operational requirements established in Chapter I and the design principles drawn from the literature in Chapter II into a concrete system design and evaluation plan. The chapter presents the requirement analysis, the conceptual framework, the development methodology, the system design, the tools and development environment, the development cost, the evaluation methods, and the data handling and analysis procedures that produce the results reported in Chapter IV.

### Requirement Analysis and Documentation

Requirements were gathered through the following methods to keep system functions aligned with the daily operational needs of PESO CSJDM. Table 3 summarizes the methods used.

**Table 3. Requirements Gathering Methods**

| Method | Purpose | Participants / Sources |
|---|---|---|
| Interview | Understand current staff procedures for accepting applicant records, storing vacancy information, and referring job seekers. Surfaced the two operational problems established in Chapter I: slow, repetitive manual cross-referencing, and the absence of data-based insight at the point of referral. | PESO CSJDM employment officers and staff |
| Observation | Examine how staff handle registration and referral in practice; identify where automated recommendation and profile-driven ranking reduce manual effort. | PESO CSJDM office, on-site |
| Dataset Profiling | Profile the historical placement records to examine structure, quality, and completeness; determine which fields are suitable as input features for the recommendation model. | PESO CSJDM historical placement records (Excel) |

#### Functional Requirements

Table 4 lists what the system shall do. FR-05 is the requirement specific to the machine learning algorithm.

**Table 4. Functional Requirements**

| ID | Requirement | Description |
|---|---|---|
| FR-01 | User Authentication | The system shall allow only authorized PESO staff to log in, verified through secure username and password authentication, so that applicant and vacancy data remain accessible to authorized personnel only. |
| FR-02 | User Account Management | The system shall allow authorized PESO staff to create, view, edit, and deactivate staff accounts. Each account stores full name, username, email, and active status. Passwords are stored in hashed form and are changeable by the account holder. Deactivated accounts retain their records but are denied access until reactivated. The system shall also allow staff to review the login history recorded at each authentication attempt, including the user, timestamp, IP address, and outcome, as a security audit trail. |
| FR-03 | Applicant Management | The system shall allow PESO staff to register and maintain applicant records through two methods: (1) batch upload of an Excel file exported from PEIS, mapping PEIS field headers to system fields and importing only the fields the system requires; or (2) direct manual entry through the applicant registration form, also used for walk-in applicants requiring an immediate recommendation. Each record stores the four ML-required fields (skills, education level, work experience, preferred position) plus the demographic fields consumed by the analytical dashboard (sex, age, barangay, district, employment status, and PWD status). Administrative and personal identifiers already held in PEIS, such as SRS ID, birthdate, civil status, street address, and contact details, are not stored, avoiding duplication of records PESO already maintains and limiting the personal information the system retains. |
| FR-04 | Job Vacancy Management | The system shall allow PESO staff to register and maintain job opening records sourced from the PESO CSJDM labor market information list. Each vacancy stores the employer's company name, the job title, and the occupational category, which are the three fields required by the recommendation engine. |
| FR-05 | ML-Based Job Recommendation | The system shall provide a dedicated Job Recommendation tab through which staff generate a ranked list of currently active job openings by suitability score for a selected job seeker, using the deployed best-performing classifier among Logistic Regression, Random Forest, and Naïve Bayes. The applicant profile may come from a stored record or direct entry. Matching is one-way: given a profile, the system ranks active vacancies. |
| FR-06 | Analytical Dashboard | The system shall provide a dedicated Analytical Dashboard tab presenting registered job seeker data. The dashboard displays: total registered job seekers with male and female percentage breakdown; counts of youth, senior citizen, and person with disability registrants; distribution by educational attainment across ten levels (Elementary Level, Elementary Graduate, High School Level, High School Graduate, Senior High School Level, Senior High School Graduate, College Level, College Graduate, Vocational, and ALS); distribution by employment status (Unemployed and Employed); and barangay-level distribution separated by District 1 and District 2. The dashboard draws exclusively on the applicants table; job vacancy records are used only by the recommendation engine and are not aggregated in the dashboard. It is designed to support the preparation of the office's quarterly job seeker reports. |

#### Non-Functional Requirements

Table 5 lists how well the system shall perform. Each NFR corresponds directly to one of the nine quality characteristics of ISO/IEC 25010:2023 (Rojas et al., 2025).

**Table 5. Non-Functional Requirements**

| ID | Category | Description |
|---|---|---|
| NFR-01 | Functional Suitability | The system shall accurately and completely deliver its specified functions, including applicant and vacancy management, job recommendation with suitability ranking, and analytical dashboard reporting. |
| NFR-02 | Performance Efficiency | The system shall respond to user requests and generate recommendation outputs within an acceptable time frame, and shall accommodate growing applicant, vacancy, and recommendation records without significant performance degradation. |
| NFR-03 | Compatibility | The system shall accept PEIS-exported Excel files for batch upload without format conflicts, and shall operate alongside existing PESO tools without interference. |
| NFR-04 | Interaction Capability | The system shall provide an interface PESO staff can recognize as appropriate for their tasks, learn to operate without advanced technical skill, and navigate the two-tab analytics structure and all core referral workflows with minimal error. |
| NFR-05 | Reliability | The system shall operate consistently, storing and retrieving data correctly and producing stable outputs under continuous daily use. |
| NFR-06 | Security | The system shall protect applicant personal information and credentials through secure authentication, input validation, and protection against unauthorized access. |
| NFR-07 | Maintainability | The system shall be modular enough for the deployed model to be updated and the database schema maintained without disrupting other functions. |
| NFR-08 | Flexibility | The system shall operate across different browsers and devices without loss of function or layout, and shall be adaptable to different deployment environments. |
| NFR-09 | Safety | The system shall prevent actions that could result in unauthorized exposure or compromise of applicant data, enforcing authentication controls and input validation to restrict access to authorized PESO staff only. |

#### Data Requirements

The recommendation engine is trained on historical placement records provided by PESO CSJDM. Table 6 describes the dataset the algorithm requires.

**Table 6. Data Requirements**

| Attribute | Description |
|---|---|
| **Source** | PESO CSJDM historical placement records, provided under a Data Sharing Agreement between the research team and PESO CSJDM |
| **Format** | Excel (.xlsx) exported from the Philippine Employment Information System (PEIS) |
| **Required Fields** | skills, education_level, work_experience, preferred_position, placement_position (target label) |
| **Minimum Records** | Sufficient to support an 80/20 stratified training-test split across target classes. Because placements concentrate in a small number of frequently filled job titles while many titles hold only one or two records, sparsely represented titles are consolidated into broader occupational categories during Data Preparation so each target class retains enough records for a valid split. |
| **Data Quality Standard** | Records missing education_level or placement_position (the target label) are removed; exact-duplicate profiles are removed so no record appears in both partitions; duplicate column names in the source export are resolved by renaming with sequential suffixes. |
| **Access Authorization** | Data Sharing Agreement executed prior to dataset acquisition; a separate data privacy agreement binds each research team member to responsible handling and prohibits disclosure of personal information outside the study. |

### Conceptual Framework

*[Insert Figure 1: Conceptual Framework (Input–Process–Output Model)]*

*Figure 1. Conceptual Framework*

Figure 1 presents the conceptual framework of the study using the Input–Process–Output (IPO) model.

**Input.** The input column is organized into four sections. *Knowledge Requirements* cover the domain knowledge applied in the study: job recommendation systems, machine learning classification, decision support systems, and the ISO/IEC 25010:2023 and TAM evaluation frameworks. *Software Requirements* list the technologies used to build the system: HTML5, CSS3, and JavaScript for the frontend; Python, Flask, and SQLite for the backend; and scikit-learn, pandas, NumPy, joblib, and openpyxl for machine learning and data handling. *Data Requirements* identify the three data sources the system depends on: applicant profiles, job vacancy records from the PESO CSJDM LMI list, and historical placement records from PESO CSJDM. *User Inputs* represent the actions PESO staff perform to interact with the system: login credentials to authenticate and access the system, applicant registration or Excel batch upload, job vacancy entries, and recommendation requests to trigger the classification pipeline for a selected applicant.

**Process.** The process column presents the four phases of Rapid Application Development (RAD), each paired with the corresponding CRISP-DM activities that govern the machine learning component. Phase 1 (Requirements Planning) covers staff interviews and on-site observation at PESO CSJDM, dataset profiling, and requirements specification, aligned with the Business Understanding phase of CRISP-DM. Phase 2 (User Design) covers system architecture, ERD, and DFD design alongside UI/UX prototyping reviewed with PESO staff, aligned with the Data Understanding and Data Preparation phases of CRISP-DM, in which the placement dataset is cleaned and prepared for modeling. Phase 3 (Construction) covers the development of all system modules integrated with the machine learning pipeline, aligned with the Modeling, Evaluation, and Deployment phases of CRISP-DM, in which the three classifiers are trained, compared by Macro F1-Score, and the best-performing model is serialized as a pre-trained model file for deployment. Phase 4 (Cutover) covers ISO/IEC 25010 evaluation by IT professionals, TAM evaluation by PESO CSJDM staff, and system deployment and handover.

**Output.** The framework produces two outputs for PESO CSJDM staff: Ranked Job Category Recommendations and the Analytical Dashboard.

**Feedback.** A feedback arrow connects the output back to the input, indicating that evaluation results and system usage can be fed back into the input layer to support continuous improvement of the system.

### Development Methodology

Two complementary frameworks were adopted: Rapid Application Development (RAD) for the web-based system, and CRISP-DM for the analytics component.

*[Insert Figure 2: Rapid Application Development Model]*

*Figure 2. Rapid Application Development Model*

**Rapid Application Development (RAD).** RAD is an iterative software development methodology that replaces exhaustive upfront specification with rapid prototyping and continuous user involvement, so that requirements are discovered and refined through demonstration rather than documentation (Riadi et al., 2024). RAD was selected for this project because PESO CSJDM staff are the sole users of the system and their referral workflow knowledge is rooted in daily office practice rather than in written documentation; showing them working screens at each prototype review was the most practical way to surface accurate requirements. The fixed capstone timeline and small team size also aligned naturally with RAD's structured phase approach, where each phase delivers a testable prototype before the next begins, keeping development bounded without deferring user validation to the end.

**CRISP-DM.** CRISP-DM is a structured, industry-independent process model for data mining and machine learning projects that breaks the work into six sequential phases: Business Understanding, Data Understanding, Data Preparation, Modeling, Evaluation, and Deployment (Shimaoka et al., 2024). It was adopted for the analytics component of this study because each phase maps directly to a concrete task in building the recommendation model: understanding PESO CSJDM's referral problem, examining the placement dataset, cleaning and preparing the records for training, fitting and comparing the three classifiers, selecting the best performer using Macro F1-Score, and deploying the model through the Flask application. CRISP-DM gave the machine learning work a clear and repeatable structure that kept the modeling process aligned with the system's actual operational needs from start to finish.

Table 7 presents how the RAD and CRISP-DM phases were carried out in parallel.

**Table 7. RAD and CRISP-DM Phase Alignment**

| Phase | RAD Activities | CRISP-DM Activities | Key Deliverable |
|---|---|---|---|
| 1. Requirements Planning | Conduct interviews and on-site observation with PESO CSJDM staff; profile the historical placement dataset; define functional and non-functional requirements | Business Understanding: identify the referral decision problem, confirm placement data availability, and define model performance goals | Requirements specification; Data Sharing Agreement |
| 2. User Design | Design system architecture, DFDs, ERD, and high-fidelity mockups for all system modules; review prototypes with PESO CSJDM staff; refine per feedback | Data Understanding: examine dataset structure, field completeness, and class distribution. Data Preparation: remove incomplete records, fill blank work experience entries, consolidate 88 job titles into five occupational categories as the target label, and split 80/20 stratified | Validated system design; cleaned dataset; selected feature set |
| 3. Construction | Develop all system modules; integrate the ML pipeline with the Flask application for recommendation inference | Modeling: fit TF-IDF vectorizer on the training partition; train Logistic Regression, Random Forest, and Naïve Bayes. Evaluation: evaluate all three classifiers on the held-out test set using Accuracy, Precision, Recall, and Macro F1-Score; select the best-performing model. Deployment: serialize the selected pipeline with joblib and deploy through the Flask application | Working system; algorithm comparison results; deployed recommendation model |
| 4. Cutover | Conduct ISO/IEC 25010:2023 evaluation by IT professionals and TAM evaluation by PESO CSJDM staff; apply corrections; prepare system handover | All CRISP-DM phases completed; this phase covers post-deployment review and evaluation of the deployed model in operational context | Evaluated system; handover package |

---

### System Design

This section presents the design diagrams that explain the overall structure and behavior of the system. Each diagram is numbered, labeled, and followed by an explanation.

#### Context Diagram

*[Insert Figure 3: Context Diagram]*

*Figure 3. Context Diagram (Proposed)*

Figure 3 presents the context diagram, which shows the whole system as a single process interacting with one external entity, PESO Staff. Staff supply seven inputs: login credentials, user account details, applicant registration data, PEIS export files, vacancy details, recommendation requests, and dashboard requests, and receive seven outputs: authentication status; account, registration, and vacancy confirmations; the ranked recommendation list; the dashboard report; and login history for security audit. The machine learning model is trained offline by the research team before deployment, so staff never upload or retrain it; at runtime they simply submit a profile through a recommendation request and receive the ranked result. No external system connects to the system directly.

#### Data Flow Diagram Level 1

*[Insert Figure 4: Data Flow Diagram Level 1]*

*Figure 4. Data Flow Diagram Level 1*

Figure 4 decomposes the system into six processes and five data stores, all accessed by the single external entity, PESO Staff. Process 1, Authenticate User, checks login credentials against the Users store (T1) and records every attempt in the Login Logs store (T4). Process 2, Manage User Accounts, maintains staff accounts in T1 and lets staff review login history from T4. Process 3, Manage Applicant Records, saves manually registered and PEIS-uploaded profiles to the Applicants store (T2). Process 4, Manage Job Vacancies, maintains vacancy records in the Job Vacancies store (T3). Process 5, Generate Job Recommendations, reads an applicant profile from T2 and the active vacancy list from T3, returns a ranked recommendation list to staff, logs the result to the Recommendations store (T5), and reads from T5 to return past recommendation results when staff view a previously generated recommendation. Process 6, Display Analytics Dashboard, reads the Applicants store (T2) to produce the dashboard report; the Job Vacancies and Recommendations stores are not consulted, as the dashboard reports exclusively on registered job seeker data.

#### Use Case Diagram

*[Insert Figure 5: Use Case Diagram]*

*Figure 5. Use Case Diagram*

Figure 5 presents the use case diagram. The single actor, PESO Staff, interacts with six use cases that correspond directly to the six processes of the Level 1 DFD. Authenticate User covers staff login and session control. Manage User Accounts covers creating, editing, and deactivating staff accounts as well as reviewing login history and changing passwords. Manage Applicant Records covers manual registration, Excel batch upload, and maintenance of applicant profiles. Manage Job Vacancies covers adding, editing, and activating or deactivating vacancy records. Generate Job Recommendations covers selecting an applicant, running the classification pipeline, and viewing ranked vacancy results. Display Analytics Dashboard covers viewing the job seeker summary panel with district-level filtering. The recommendation model is pre-trained by the research team on verified historical placement records prior to deployment; model training is not a staff-facing function.

#### Entity Relationship Diagram (ERD)

*[Insert Figure 6: Entity Relationship Diagram]*

*Figure 6. Entity Relationship Diagram*

Figure 6 presents the ERD. The database has five tables, each mapped to one data store in the Level 1 DFD. The users table (T1) holds each staff account's credentials, full name, email, active status, and creation date. The applicants table (T2) stores only the fields the system needs: four ML input fields (educ_level, preferred_position, skills, and work_experience), demographic fields for the dashboard, peis_reg_date, is_archived, and created_at. Personal identifiers not needed by the system are discarded during import. The job_vacancies table (T3) holds each vacancy's employer name, job title, occupational category, local or overseas classification, active status, and creation date. The login_logs table (T4) records each authentication event, capturing the user reference, username, timestamp, IP address, and outcome. The recommendations table (T5) logs each recommendation run, storing the applicant, vacancy, and staff user as foreign keys, together with the suitability score, rank, run timestamp, and result status. The three foreign keys in T5 link it to T1, T2, and T3, making recommendations the central output table that connects all other entities.

#### System Architecture Diagram

*[Insert Figure 7: System Architecture Diagram]*

*Figure 7. System Architecture Diagram*

Figure 7 presents the three-tier architecture of the system. The **frontend tier** consists of the browser-rendered interface (Jinja2-templated HTML with Bootstrap styling and Chart.js visualizations) through which PESO staff carry out all workflows on desktop or mobile. The **backend tier** is a single Flask application handling routing, session management, business logic, and the machine learning inference: the trained pipeline (TF-IDF vectorizer and deployed classifier) is stored as a pre-trained model file and loaded into the Flask process at startup, called in-process whenever a recommendation request is made. The algorithm therefore lives inside the application rather than on a separate service. The **database tier** is a SQLite database file storing all five core tables, accessed exclusively through the backend.

#### Flowcharts

*[Insert Figure 8: System Process Flowchart]*

*Figure 8. System Process Flowchart*

Figure 8 illustrates the system process for generating job recommendations for a specific applicant profile.

The process begins when PESO staff opens the Job Recommendation tab and selects an applicant from existing records or enters a new profile directly. Before proceeding, the system verifies that all four required fields are present: EDUC LEVEL, PREFERRED POSITION, SKILLS, and WORK EXPERIENCE. If any field is empty, the system prompts the staff to complete the missing information and the profile cannot proceed until all four fields are filled. Three fields are required for the profile to proceed: Education Level, Preferred Position, and Skills. Work Experience is optional; if left blank, the system substitutes "NO EXPERIENCE," preserving the absence of prior employment history as a meaningful classification signal consistent with how missing work experience was handled during training preprocessing.

Once the profile is complete, the four fields are cleaned using the same text normalization applied during training: all text is lowercased, special characters are removed, numeric noise is stripped from the work experience field, and the four fields are concatenated into a single PROFILE_TEXT string. This cleaning step must exactly replicate the preprocessing applied during model training so that the vocabulary and term weights remain consistent between training and inference.

The cleaned PROFILE_TEXT is then passed through the fitted TF-IDF vectorizer loaded from the pre-trained model file, converting it into a 356-term numerical vector. The trained classifier runs `predict_proba()` on that vector, returning a probability score for each of the five occupational categories. These scores represent the model's confidence that the applicant's profile belongs to each category based on patterns learned from the 1,083 preprocessed placement records.

The system then queries all currently active job vacancies from the database. If no active vacancies are found, the system notifies the staff and the process ends. When vacancies are present, each vacancy is assigned the suitability score of its occupational category from the `predict_proba()` output. The full list of active vacancies is sorted in descending order by suitability score. The five occupational categories are displayed to PESO staff ranked from highest to lowest probability score, with the active vacancies belonging to each category listed under it, allowing staff to see both the overall category ranking and the specific job openings available within each group before deciding on a referral.

*[Insert Figure 9: Data Pre-processing Flowchart]*

*Figure 9. Data Pre-processing Flowchart*

Figure 9 illustrates the data preprocessing pipeline applied to the PLACEMENT_DATASET.xlsx before TF-IDF vectorization.

The raw dataset contains 1,451 records across 44 columns. Only five columns are retained: EDUC LEVEL, PREFERRED POSITION, SKILLS, WORK EXPERIENCE, and Job Position, as these are the only fields relevant to job category classification. All remaining 39 administrative columns are dropped.

Each record is then checked for a blank WORK EXPERIENCE value. Blank entries are filled with "NO EXPERIENCE" to preserve the absence of work history as a meaningful value rather than an empty field. Records confirmed as exact duplicates across all five retained columns are removed and do not proceed further in the pipeline.

Each record's Job Position value is checked against a predefined mapping table. Records with unrecognizable job titles are excluded. Matched records are assigned to one of five occupational categories, specifically Warehouse and Logistics, Production and Manufacturing, Sales/Service/Retail, Clerical and Administrative, and General Services and Security, because the raw Job Position column contains 88 unique titles, many appearing only once or twice, which is insufficient for reliable classifier training.

Text normalization is applied in three steps. All text is converted to lowercase. Special characters and punctuation are removed from all fields. Numeric noise is stripped specifically from WORK EXPERIENCE; entries such as "5 mos as CASHIER" are cleaned to retain only the role term "cashier."

The four normalized fields are then concatenated into a single text string per record so that all profile information contributes to one unified vector. Finally, the five category labels are encoded as integers zero through four, preparing the target column for classifier input. The preprocessed records are then ready for TF-IDF vectorization.

*[Insert Figure 10: ML Algorithm Flowchart]*

*Figure 10. ML Algorithm Flowchart*

Figure 10 illustrates the ML algorithm training pipeline that receives the 1,083 preprocessed records from Figure 9 and produces the trained model used by the job recommendation module.

The 1,083 records are first divided into a training set (866 records, 80%) and a test set (217 records, 20%) using stratified splitting, which preserves each occupational category's proportion in both halves. This split is performed before any text conversion so the test set remains completely unseen during training, ensuring the final performance scores reflect real-world behavior and not memorized training data.

Each applicant's profile text is then converted into numbers using TF-IDF (Term Frequency-Inverse Document Frequency). Every unique word across the 866 training profiles forms a vocabulary of 356 terms, and each profile receives a score per word based on two factors: how often that word appears in the profile, and how rare it is across all profiles. Words specific to one occupational group, such as "forklift" for Warehouse and Logistics or "cashier" for Sales/Service/Retail, receive high scores because they are strong category signals. Words that appear in nearly every profile receive low scores because they carry no useful distinction between categories. The vectorizer is configured with sublinear_tf=True and fitted on the training set only, producing a training matrix of 866 × 356 and a test matrix of 217 × 356. The same fixed vocabulary and weights are then applied to the test set without any additional learning.

All three classifiers receive the same training matrix so that any difference in performance is attributable to the algorithm and not to the data.

**Logistic Regression** learns one numerical weight per word per occupational category. To predict a category, it multiplies each word's TF-IDF score by its learned weight and sums the result into a score z_k for each category k. These scores are converted into probabilities using the Softmax function: P(k | x) = e^(z_k) / Σⱼ e^(z_j), which ensures all five category probabilities sum to 1. A word like "cashier" accumulates a high weight for Sales/Service/Retail if it consistently appeared in profiles of that category during training. The category with the highest probability is the predicted class, and those probabilities become the suitability scores shown to PESO staff.

**Random Forest** builds 100 decision trees, each trained on a random subset of records and vocabulary words. Every tree asks a series of yes/no questions about individual word scores, for example whether the score for "forklift" exceeds a threshold, and follows those questions to a final prediction. Split quality at each node is measured by Gini Impurity: Gini = 1 − Σ pᵢ², where pᵢ is the proportion of each category at that node; the split that produces the most category-pure groups is selected. The predicted class for evaluation is decided by majority vote across all 100 trees. For recommendation suitability scoring, the output is the mean class proportion across all trees.

**Naive Bayes** works through probability estimation. During training, it calculates how likely each word is to appear in a profile belonging to each occupational category. At prediction time, it applies Bayes Theorem: P(y=k | x) ∝ P(x | y=k) × P(y=k), multiplying the prior probability of each category by the likelihood of the applicant's word scores given that category. The classifier assumes each word contributes independently to the total, which is the "naive" assumption the algorithm is named after. The Multinomial variant is used because it accepts the non-negative TF-IDF values produced by the vectorizer, making it the standard choice for text classification pipelines in scikit-learn (Heakl et al., 2024; Chihab et al., 2025).

No resampling or class weighting was applied to any classifier during training. The class imbalance across the five occupational categories is addressed through the choice of Macro F1-Score as the selection criterion rather than through data manipulation, ensuring the evaluation holds every category to the same standard regardless of size.

After training, each classifier predicts the occupational category for the 217 held-out test profiles. Five metrics are computed: Accuracy, Precision, Recall, F1-Score, and Macro F1-Score, alongside a confusion matrix for each classifier. A fixed random seed (random_state = 42) was applied to the train/test split and to both Logistic Regression and Random Forest to ensure full reproducibility of the results. The classifier with the highest Macro F1-Score is selected, saved together with the fitted TF-IDF vectorizer into a single pipeline file, and loaded by the Flask application at startup to serve job recommendations without retraining.

#### Mockups

*[Insert Figure 11: Login Page Mockup]*

*Figure 11. Login Page*

*[Insert Figure 12: Job Recommendation Tab Mockup]*

*Figure 12. Job Recommendation Tab*

*[Insert Figure 13: Analytical Dashboard Tab Mockup]*

*Figure 13. Analytical Dashboard Tab*

*[Insert Figure 14: Applicant Registration Form Mockup]*

*Figure 14. Applicant Registration Form*

*[Insert Figure 15: Job Vacancy Management Mockup]*

*Figure 15. Job Vacancy Management*

### Tools, Technologies, and Development Environment

Table 8 lists the tools and technologies that will be used to develop the system. All tools are open-source or freely available, chosen to keep the system maintainable within a local government setting without licensing costs.

**Table 8. Tools, Technologies, and Development Environment**

| Category | Tool / Technology | Version | Justification |
|---|---|---|---|
| Frontend | HTML5, CSS3, JavaScript | HTML5 / CSS3 / ES2015 | Standard web markup, styling, and scripting languages for building structured, accessible, and interactive system pages; all frontend output will be rendered through Jinja2 templates served by Flask |
| Frontend | Bootstrap (via CoreUI 5) | 5.3 | Open-source Bootstrap-based CSS framework providing pre-built, mobile-responsive UI components; will ensure consistent layout across desktop and mobile browsers without custom component development |
| Backend | Python | 3.14.2 | Single language for both the web application and machine learning pipeline; routing, business logic, session management, and ML inference will all run within one Flask process |
| Backend | Flask | 3.0 | Lightweight Python micro-framework for routing, Jinja2 templating, and session management; Werkzeug utilities bundled with Flask will handle password hashing and secure file uploads |
| Database | SQLite | 3.46 | Serverless, file-based relational database bundled with Python; will store all five system tables in a single database file deployed alongside the application without requiring a separate database server |
| Python / ML Libraries | scikit-learn | 1.4 | Will provide TfidfVectorizer, LogisticRegression, RandomForestClassifier, MultinomialNB, and Pipeline for constructing and comparing the three classification models; NumPy (1.26) is included as a required numerical dependency |
| Python / ML Libraries | pandas | 2.2 | Will handle .xlsx file reading for PEIS-exported batch uploads and all CRISP-DM Data Preparation steps including duplicate removal and missing value handling |
| Python / ML Libraries | openpyxl | 3.1 | Excel reading engine for .xlsx files required for both training dataset ingestion and applicant batch upload processing |
| Model Serving | joblib | 1.4 | Will serialize the trained TF-IDF vectorizer and best-performing classifier into a pre-trained model file; the Flask application will reload this artifact at startup for live inference without retraining |
| Jupyter Notebook | Python Script (.py) | 3.14.2 | ML training, preprocessing, and model evaluation will be implemented as standalone Python scripts executed directly through the Visual Studio Code terminal; all CRISP-DM Modeling and Evaluation steps will be performed via the Python interpreter without a notebook interface |
| Data Visualization | Chart.js | 4.4 | Lightweight open-source charting library that will render all Analytical Dashboard charts; chart data will be fetched asynchronously from the Flask JSON API endpoint |
| Version Control | Git | 2.47 | Will track code changes and coordinate development across the five-member research team throughout all RAD phases |
| IDE / Code Editor | Visual Studio Code | 1.96 | Free, extensible editor with integrated terminal and Python/JavaScript extensions; will serve as the primary development environment for all team members |
| UI/UX Design | HTML, CSS, and Bootstrap (via CoreUI 5) | 5.3 | System screens were prototyped directly within the Flask development environment using HTML, CSS, and Bootstrap. Browser screenshots of the running prototype were used for stakeholder review during the User Design phase, eliminating the need for a separate wireframing tool. |
| Diagram Tools | draw.io | Web-based | Will be used to create all system design diagrams including the context diagram, DFD, use case diagram, ERD, system architecture diagram, and flowcharts |
| Deployment | PythonAnywhere | Free tier | Free-tier cloud hosting for Flask applications; will provide always-on deployment without requiring separate server configuration or infrastructure costs |

**Development environment.** Development will be carried out on Windows 10/11 machines using the Flask built-in development server for local testing, with application and ML dependencies isolated in a Python virtual environment.

### Development Cost

Table 9 presents the estimated breakdown of the cost of building the system.

**Table 9. Development Cost**

| Category | Details | Estimated Cost |
|---|---|---|
| Human Resource | 5 members × 300 hours each × ₱75/hour | ₱112,500.00 |
| Software & Licensing | All tools open-source or freely available | ₱0.00 |
| Hardware | Laptop depreciation: 5 units × ₱30,000 ÷ 3-year lifespan ÷ 12 months × 6 months | ₱25,000.00 |
| Dataset Acquisition | Provided at no cost under Data Sharing Agreement | ₱0.00 |
| Cloud Computing | None; all training performed on local hardware | ₱0.00 |
| Internet & Utilities | ₱500/month × 5 members × 6 months | ₱15,000.00 |
| Documentation & Printing | Manuscript, binding, evaluation instruments | ₱3,000.00 |
| Transportation | Trips to PESO CSJDM for interviews, observation, evaluation | ₱2,000.00 |
| **Subtotal** | | **₱157,500.00** |
| Contingency (10%) | Unforeseen expenses | ₱15,750.00 |
| **TOTAL** | | **₱173,250.00** |

The total estimated development cost of ₱173,250.00 is low primarily because all software tools used in this study are free and open-source, no paid dataset was required, and the system is trained and deployed on existing hardware rather than paid cloud infrastructure. The largest component is human resource, reflecting the combined development effort of the five-member research team over the six-month project period.

### Evaluation Methods

This section describes how the system will be evaluated following implementation. The objective of the evaluation is to assess the **technical quality** of the system and its **acceptability to users**. Two established evaluation models will be used: the ISO/IEC 25010:2023 Software Product Quality Model and the Technology Acceptance Model (TAM).

#### Evaluation Using ISO/IEC 25010:2023

**Purpose.** ISO/IEC 25010:2023 will be used to assess the technical quality of the developed system against an international software product quality standard (Rojas et al., 2025).

**Quality characteristics.** The system will be evaluated across nine characteristics, each defined here in terms of the present system:

1. **Functional Suitability** evaluates whether the system accurately and completely delivers its specified functions: applicant and vacancy management, job recommendation with suitability ranking, and dashboard reporting. This characteristic also serves as the formal verification of Objective 1's functional requirements (FR-01 to FR-06).
2. **Performance Efficiency** covers the speed of generating recommendation outputs, loading applicant data, and handling daily use without degradation.
3. **Compatibility** covers the system's ability to accept PEIS-exported Excel files for batch upload without format conflicts, and to operate alongside existing PESO tools without interference.
4. **Interaction Capability** covers the degree to which PESO staff can recognize the interface as appropriate for their tasks, learn to navigate it without advanced technical skill, and complete referral and dashboard workflows with minimal error.
5. **Reliability** evaluates whether the system consistently generates stable outputs and maintains uninterrupted operation under continuous daily use.
6. **Security** covers protection of applicant personal information, credentials, and recommendation records through authentication and access control.
7. **Maintainability** covers ease of updating the ML model, modifying features, and maintaining the database schema.
8. **Flexibility** evaluates whether the system operates across different browsers and devices without loss of function, and whether it can be adapted to different deployment environments.
9. **Safety** evaluates whether the system prevents unacceptable risk to applicant data, including enforcement of authentication controls that restrict access to authorized PESO staff only and input validation that protects stored records from unauthorized modification.

**Evaluators.** At least three (3) IT professionals with expertise in web development, database management, or machine learning systems will be invited as evaluators, selected through purposive sampling.

**Instrument.** A structured evaluation form based on the eight ISO 25010 characteristics will be prepared, with each item rated on a 5-point Likert scale (5 = Strongly Agree to 1 = Strongly Disagree).

**Process overview.** The system will be deployed and made accessible to the evaluators with test accounts and guided scenarios covering all modules. Each evaluator will interact with the system and complete the instrument; responses will be tabulated and analyzed in Chapter IV.

#### Evaluation Using the Technology Acceptance Model (TAM)

**Purpose.** TAM will be used to measure user perceptions of usefulness, ease of use, and intention to adopt the system, following its validated application to web-based systems in public service contexts (Alsyouf et al., 2023).

**TAM constructs.**

1. **Perceived Usefulness (PU)** assesses whether the system helps staff do their job better, including whether it improves performance, increases productivity, and helps accomplish tasks more quickly.
2. **Perceived Ease of Use (PEOU)** assesses whether the interface is clear and navigable, and whether staff find the system easy to learn and operate without advanced technical skill.
3. **Behavioral Intention to Use (BI)** assesses whether staff are willing to use the system regularly and would recommend or prefer it over manual methods.

**Respondents.** Twenty-seven (27) respondents will be selected through purposive sampling. Respondents are individuals who will interact with the system and can provide meaningful feedback on its usability and usefulness based on their experience with the system's workflows.

**Instrument.** A TAM-based questionnaire aligned to the three constructs will be used, rated on the same 5-point Likert scale. Each respondent will receive a guided walkthrough covering the core workflows (registering or selecting an applicant, generating a ranked recommendation, and navigating the dashboard) before independently answering the questionnaire.

#### Data Handling and Analysis

##### A. Respondents and Population Description

The total evaluation population is thirty (30) respondents, broken down into two evaluator groups selected through purposive sampling. Table 10 summarizes the respondent groups.

**Table 10. Respondent Groups**

| Respondent Group | Evaluation Framework | Sampling Method | n |
|---|---|---|---|
| PESO CSJDM staff (end-user respondents who directly manage applicant data and referral operations) | TAM | Purposive | 27 |
| IT professionals (web development, database management, or ML systems expertise) | ISO/IEC 25010:2023 | Purposive | 3 |
| **Total** | | | **30** |

##### B. Data Analysis

Responses from both evaluator groups will be collected using a 5-point Likert scale: 5 – Strongly Agree, 4 – Agree, 3 – Neutral, 2 – Disagree, 1 – Strongly Disagree. Responses will be interpreted using the conversion scale in Table 11.

**Table 11. Likert Scale Conversion**

| Rating Range | Interpretation |
|---|---|
| 4.51 – 5.00 | Highly Acceptable |
| 3.51 – 4.50 | Acceptable |
| 2.51 – 3.50 | Moderately Acceptable |
| 1.51 – 2.50 | Slightly Acceptable |
| 1.00 – 1.50 | Not Acceptable |

For this system, a mean of 4.51–5.00 (Highly Acceptable) indicates that the evaluated characteristic (for example, the accuracy of the recommendation workflow or the clarity of the two-tab interface) fully meets the criterion with no significant areas for improvement. A mean of 3.51–4.50 (Acceptable) indicates the criterion is satisfied with only minor refinements needed. A mean of 2.51–3.50 (Moderately Acceptable) indicates the system partially satisfies the criterion and requires targeted improvement before regular operational use at PESO CSJDM. A mean of 1.51–2.50 (Slightly Acceptable) indicates substantial revision is required, and 1.00–1.50 (Not Acceptable) indicates the criterion is not met and fundamental redesign is needed. Consistent with Objective 3, the study's target threshold for each evaluation dimension is a weighted mean of at least 3.51 ("Acceptable").

##### C. Statistical Treatment of Data

The **Arithmetic Mean (AM)** will be used to summarize Likert-scale responses:

> AM = Σ(wᵢfᵢ) / n

Where:
- AM = Arithmetic Mean
- wᵢ = Likert scale weight (5, 4, 3, 2, 1)
- fᵢ = Frequency of responses for each weight
- n = Total number of respondents

AM will be computed per questionnaire item, per ISO/IEC 25010:2023 quality characteristic, per TAM construct, and for the overall score of each instrument.

##### D. Statistical Tools Used

**Frequency** is used to count how many respondents chose each rating per item.

**Percentage** is used to express the proportion of responses per rating:

> P = (F × 100) / N

Where: P = Percentage, F = Frequency of a particular rating, N = Total respondents.

**Weighted Mean** corresponds directly to the Arithmetic Mean formula above and is the main tool for interpreting the evaluation results in Chapter IV.

##### E. Algorithm Performance Metrics

The performance of the embedded algorithm will be evaluated independently from the system quality assessment conducted under ISO/IEC 25010 and the user acceptance evaluation conducted under TAM. Those two evaluations measure the quality and acceptability of the web-based system as a whole, while the algorithm performance evaluation specifically measures how accurately and reliably the classification model assigns applicant profiles to occupational categories. Because the system's algorithm is classification-based, the metrics reported are Accuracy, Precision, Recall, F1-Score, and Macro F1-Score, together with a per-class confusion matrix; regression and clustering metrics do not apply. The algorithm performance results apply to the Job Recommendation Module, which is the sole analytics module powered by the trained model.

**Validation technique.** A stratified holdout validation approach will be used. The 1,083 preprocessed placement records will be partitioned 80/20 into a training set (866 records) and a held-out test set (217 records), with stratified sampling applied so that each occupational category's proportion is preserved in both partitions. Stratification is necessary because the five categories are not evenly distributed: Sales/Service/Retail holds 317 records (29.3%), Production and Manufacturing holds 292 (27.0%), Warehouse and Logistics holds 175 (16.2%), Clerical and Administrative holds 149 (13.8%), and General Services and Security holds 150 (13.9%). Without stratification, the smaller categories may be underrepresented in the test partition, producing unreliable class-level performance estimates. The 80/20 proportion follows the convention applied in the supervised classification studies reviewed in Chapter II (Chihab et al., 2025; Adillah et al., 2026; Darma et al., 2026). All three candidate algorithms, Logistic Regression, Random Forest, and Naïve Bayes, will be trained on the identical training partition and evaluated on the identical test partition so that performance differences are attributable to the algorithm and not to data variation.

**Performance metrics.** Table 12 presents the classification metrics used to evaluate all three algorithms, their formulas, and their purpose in the context of the PESO job recommendation model.

**Table 12. Classification Performance Metrics**

| Metric | Formula | Purpose |
|---|---|---|
| Accuracy | (TP + TN) / (TP + TN + FP + FN) | Overall proportion of correct category classifications across all 5 categories |
| Precision | TP / (TP + FP) | Proportion of recommended categories that are actually suitable |
| Recall | TP / (TP + FN) | Proportion of suitable categories the model successfully identifies |
| F1-Score | 2 × (Precision × Recall) / (Precision + Recall) | Harmonic mean of Precision and Recall, balancing both error types per-class |
| Macro F1-Score | (1/k) × Σ F1ᵢ, where k = 5 | Unweighted average of per-class F1, giving all 5 categories equal importance |

Where: TP (True Positive) = a job category correctly identified as a suitable match for the applicant's profile; TN (True Negative) = a category correctly identified as not suitable; FP (False Positive) = an unsuitable category incorrectly recommended; FN (False Negative) = a suitable category the model failed to identify. Precision, Recall, and F1-Score are computed separately for each of the five occupational categories and reported as both macro averages, where each category contributes equally to the final score, and weighted averages, where each category is weighted by its share of the test partition.

**Selection criterion.** The algorithm with the highest Macro F1-Score on the held-out test set will be selected for deployment. Macro F1 is used as the selection criterion rather than Accuracy because the five occupational categories differ in size; Sales/Service/Retail holds 317 records (29.3%) while Clerical and Administrative holds 149 (13.8%) and General Services and Security holds 150 (13.9%). Under an accuracy-only criterion, an algorithm that performs well on the three larger categories while failing on the two smaller ones would still record a deceptively high overall score, masking its inability to correctly recommend clerical or security positions to applicants in those groups. Macro F1 computes the F1-Score for each category separately and averages them with equal weight regardless of how many records each category holds, so failure on the 149-record Clerical category penalizes the score as severely as failure on the 317-record Sales category. The three supervised classification studies reviewed in Chapter II, Chihab et al. (2025), Adillah et al. (2026), and Tiwari and Upadhyay (2024), all selected their best algorithm using accuracy-only without addressing class size differences in their evaluation criterion. The present study applies Macro F1 to correct this gap (Opitz, 2024; Grandini et al., 2020).

**Confusion matrix.** A 5×5 confusion matrix will be generated for each of the three algorithms after evaluation on the held-out test partition. The rows represent the five actual occupational categories and the columns represent the five categories assigned by the model, producing one cell per actual-predicted category pair. Cells on the main diagonal represent correct classifications for each category, while off-diagonal cells represent misclassifications showing which category the model confused with which. The matrix enables a precise diagnosis of where each algorithm succeeds and where it fails across all five occupational groups, beyond what aggregate metrics reveal.

The complete algorithm performance results, including the classification metrics comparison for Logistic Regression, Random Forest, and Naïve Bayes and the 5×5 confusion matrix for each algorithm, are presented and interpreted in Chapter IV.

---


# CHAPTER IV
## RESULTS AND DISCUSSION

This chapter presents the results of the study based on the specific objectives stated in Chapter I. Each objective is addressed in sequence, supported by data, screenshots, tables, or figures, with a brief explanation of what the results show. The first section covers the developed system and its modules. The second section presents the algorithm comparison results and the selected recommendation model. The third section presents the evaluation results under ISO/IEC 25010:2023 and the Technology Acceptance Model (TAM). The chapter closes with a system testing summary and a discussion of findings in relation to the study's objectives and related literature.

---

## Results for Specific Objective 1: Design, develop, and deploy a web-based data-driven job recommendation system with dashboard for PESO CSJDM.

The web-based data-driven job recommendation system with dashboard for PESO CSJDM was successfully designed, developed, and deployed. The system was built using Python and Flask as the backend framework, SQLite as the database, Bootstrap via CoreUI 5 for the frontend, and scikit-learn for the machine learning component. It runs through a responsive web interface that can be accessed on both desktop and mobile browsers. The system is organized into two main analytics modules, namely the Job Recommendation tab and the Analytical Dashboard tab, alongside Applicant Management, Job Vacancy Management, and Staff Account Management. The following sections describe each module as implemented.

### Login Page

*[Insert Figure 16: Login Page]*

**Figure 16.** Login Page

Figure 16 shows the Login Page, which is the entry point of the system. PESO staff must provide a valid username and password to gain access. Passwords are stored in encrypted form to keep them secure. Every login attempt, whether it was successful, failed, or denied because of an inactive account, is recorded along with the user, timestamp, IP address, and outcome. This gives staff an audit trail they can check through the Login History page. Anyone who tries to open a protected page without logging in is automatically redirected to the login screen.

---

### Home Dashboard

*[Insert Figure 17: Home Dashboard]*

**Figure 17.** Home Dashboard

Figure 17 shows the Home Dashboard, which is the first screen displayed after a successful login. It provides a quick overview of the system's current state through four summary counts: total registered applicants, number of active job vacancies, number of distinct employers, and total recommendation runs generated. It also shows the staff member's last login time, displayed in Philippine Time, and two activity feeds showing the five most recently registered applicants and the five most recently generated recommendations. This gives staff a quick view of recent activity without needing to go to another page.

---

### Job Recommendation Tab

*[Insert Figure 18: Job Recommendation Tab — Empty State]*

**Figure 18.** Job Recommendation Tab (No Recommendation Generated Yet)

*[Insert Figure 19: Job Recommendation Tab — Recommendation Results]*

**Figure 19.** Job Recommendation Tab (Results Displayed)

Figures 18 and 19 show the Job Recommendation tab, which is the main analytics module of the system and the direct output of Objective 2. The tab has two input options that staff can switch between: Registered Applicant mode, which lets staff select a stored applicant from a searchable list, and Quick Entry mode, which lets staff type in a profile manually without saving it to the database. When an applicant is selected in Registered Applicant mode, a small profile card appears showing the applicant's education level, skills, and work experience, along with a warning if any required fields are missing.

When staff click Generate Recommendations, the system takes the applicant's four profile fields, which are education level, preferred position, skills, and work experience, and processes them using the same text preparation steps used when the model was trained. Education level, preferred position, and skills are required for the recommendation to proceed. Work experience is optional; if left blank, the system substitutes "NO EXPERIENCE" so the field still contributes a meaningful value to the profile, consistent with how it was handled during model training. The processed text is then converted into a numerical format using the saved TF-IDF converter and passed through the trained Logistic Regression model, which produces a suitability score for each of the five occupational categories. The categories are then shown in order from highest to lowest score. The top-ranked category is highlighted as a hero card with a green design, a trophy icon, the suitability percentage, and a list of currently active job vacancies in that category. The remaining four categories are listed below with their scores and available openings. If there are no active vacancies in a category, the system shows "No active openings in this category currently." When a recommendation is generated for a stored applicant, the result is saved in the recommendations table along with the applicant, vacancy, suitability score, rank, and the staff member who generated it.

---

### Analytical Dashboard Tab

*[Insert Figure 20: Analytical Dashboard Tab]*

**Figure 20.** Analytical Dashboard Tab

Figure 20 shows the Analytical Dashboard tab, which supports PESO CSJDM's quarterly job seeker reporting requirements. The dashboard presents registered job seeker data across three sections. The top row shows the total number of registered job seekers with a male and female breakdown, and separate counts for youth (ages 15 to 30), senior citizens (ages 60 and above), and persons with disability (PWD). Below the summary row, the distribution of registrants by educational attainment is shown as a horizontal bar chart covering the ten canonical levels. The distribution by employment status is shown as a doughnut chart with a count summary below it. The barangay-level distribution of registrants separated into District 1 and District 2 is shown as two scrollable tables with totals. The dashboard loads its data in the background without requiring a full page reload, and it supports date range filtering by PEIS registration date, so staff can view data for a specific period. All data shown in the dashboard comes from the applicants table only; job vacancy and recommendation records are not counted here.

---

### Applicant Management

*[Insert Figure 21: Applicant List (Card View)]*

**Figure 21.** Applicant List (Card View)

*[Insert Figure 22: Applicant Registration Form]*

**Figure 22.** Applicant Registration Form

*[Insert Figure 23: PEIS Batch Upload Page]*

**Figure 23.** PEIS Batch Upload Page

Figures 21 through 23 show the Applicant Management module, which provides two ways to add applicant records. Staff can register applicants one by one through the form in Figure 22, which collects the four fields needed for the recommendation model, which are education level, preferred position, skills, and work experience, as well as the demographic fields used by the Analytical Dashboard such as sex, age, barangay, district, employment status, PWD status, and PEIS registration date. Alternatively, staff can upload a PEIS-exported Excel file through the batch upload page shown in Figure 23. The upload process converts raw PEIS column names and field values, including education level entries, barangay names, age formats, and employment status, into the system's standard format. It imports only the twelve fields the system needs and ignores any other columns that are already managed in PEIS. After uploading, a summary shows how many records were imported, how many blank rows were skipped, and how many records were saved with an incomplete profile that needs follow-up. The applicant list in Figure 21 supports card and table views, search by name or skills, filtering by district and employment status, and an incomplete filter that shows records with missing fields needed for the recommendation. Records can be archived to remove them from the active list without permanently deleting the data, and they can be restored if needed.

---

### Job Vacancy Management

*[Insert Figure 24: Job Vacancy List]*

**Figure 24.** Job Vacancy Management

Figure 24 shows the Job Vacancy Management module, which is where staff record and manage the job openings from the PESO CSJDM labor market information list. Each vacancy stores the employer's company name, the job title, and the occupational category, which are the three fields the recommendation model needs. Staff can add new vacancies, edit existing ones, and set each vacancy as active or inactive. The recommendation engine only uses active vacancies when generating a ranked list. Deactivated vacancies stay in the database for record-keeping but are not shown in recommendation results.

---

### Staff Account Management

*[Insert Figure 25: Staff Account List]*

**Figure 25.** Staff Account Management

Figure 25 shows the Staff Account Management module, which allows authorized staff to create, view, edit, and deactivate staff accounts. Each account stores the staff member's full name, username, email address, active status, and date the account was created. Passwords are stored in encrypted form and can be changed by the account holder through the Change Password option in the sidebar. Deactivated accounts keep their records and login history but are blocked from accessing the system until reactivated. The Login History page shows the last 200 login events across all accounts, including the user, timestamp, IP address, and whether the attempt was successful, failed, or denied, which serves as a security audit trail.

---

The successful development and deployment of all six modules, which are User Authentication, User Account Management, Applicant Management, Job Vacancy Management, Job Recommendation, and Analytical Dashboard, confirms that the system meets all functional requirements established in Chapter III and fulfills the first specific objective of the study.

---

## Results for Specific Objective 2: Implement the best-performing classification algorithm, as determined through a comparative evaluation of Logistic Regression, Random Forest, and Naïve Bayes.

### Experimental Setup

The machine learning evaluation used the preprocessed PESO CSJDM placement dataset containing 1,083 records distributed across five occupational categories. Table 13 presents the distribution of records per category.

**Table 13.** Dataset Distribution by Occupational Category (n = 1,083)

| Occupational Category | Records | Proportion |
|---|---|---|
| Warehouse and Logistics | 175 | 16.2% |
| Production and Manufacturing | 292 | 27.0% |
| Sales/Service/Retail | 317 | 29.3% |
| Clerical and Administrative | 149 | 13.8% |
| General Services and Security | 150 | 13.9% |
| **Total** | **1,083** | **100.0%** |

The dataset was divided into a training set and a test set using an 80/20 split, yielding 866 training records and 217 test records. The split was done in a way that kept the proportion of each category the same in both sets, making sure no category was missing from the test data. This division was also done before the text was converted into numbers, so that the test records had no influence on how the model learned its features.

TF-IDF was applied to each applicant's profile text, which is a combined text entry made up of the education level, preferred position, skills, and work experience fields, processed through the same text cleaning steps used when the system generates recommendations. The TF-IDF converter was trained using only the 866 training records, which produced a set of 356 unique terms. Those same terms and weights were then applied to the test set without any further adjustments. This produced a training table with 866 rows and 356 columns, and a test table with 217 rows and 356 columns.

Three classification algorithms were then trained on the same training data: Logistic Regression (max_iter = 1,000), Random Forest (100 decision trees), and Multinomial Naïve Bayes. A fixed random seed was applied to the data split and to both Logistic Regression and Random Forest to make sure the results can be reproduced. No data resampling or class weighting was applied; the class imbalance was handled through the use of Macro F1-Score as the selection measure, as discussed in Chapter III.

### Classifier Comparison Results

Table 14 presents the evaluation results for all three classifiers on the 217-record test set.

**Table 14.** Classifier Comparison Results (n = 217, Test Set)

| Classifier | Accuracy | Macro F1-Score | Weighted F1-Score |
|---|---|---|---|
| **Logistic Regression** | **0.7281** | **0.7370** | **0.7264** |
| Naïve Bayes | 0.7051 | 0.7098 | 0.6979 |
| Random Forest | 0.6590 | 0.6679 | 0.6540 |

Logistic Regression achieved the highest scores across all three measures. On the primary selection criterion, Macro F1-Score, Logistic Regression (0.7370) outperformed Naïve Bayes (0.7098) by 0.0272 and Random Forest (0.6679) by 0.0691. The same ranking held for both accuracy and Weighted F1-Score, showing that Logistic Regression performed most consistently across all five occupational categories. Logistic Regression was therefore selected as the recommendation model for deployment.

Macro F1-Score was used instead of accuracy because the five categories are not equal in size. Accuracy only counts the total number of correct predictions regardless of which category they belong to. This means a model that performs well on the three larger groups, which are Sales/Service/Retail (317 records, 29.3%), Production and Manufacturing (292 records, 27.0%), and Warehouse and Logistics (175 records, 16.2%), but fails on the two smaller ones, would still appear to have a high overall score. Macro F1-Score, on the other hand, calculates the F1-Score for each of the five categories separately and then averages them equally. This means a poor performance on the smaller Clerical and Administrative group (149 records) is treated just as seriously as a poor performance on the larger Sales/Service/Retail group. This approach ensures that the selected model works well for all categories that PESO staff may need to refer applicants to, not just the ones with more records.

### Per-Category Performance of the Selected Model

Table 15 presents the per-category Precision, Recall, F1-Score, and Support for Logistic Regression on the 217-record test set.

**Table 15.** Logistic Regression Per-Category Performance (n = 217, Test Set)

| Occupational Category | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| Warehouse and Logistics | 0.6552 | 0.5429 | 0.5938 | 35 |
| Production and Manufacturing | 0.6964 | 0.6724 | 0.6842 | 58 |
| Sales/Service/Retail | 0.6800 | 0.7969 | 0.7338 | 64 |
| Clerical and Administrative | 0.7500 | 0.7000 | 0.7241 | 30 |
| General Services and Security | 0.9655 | 0.9333 | 0.9492 | 30 |
| **Macro Average** | **0.7494** | **0.7291** | **0.7370** | **217** |

General Services and Security achieved the highest F1-Score at 0.9492, with a Precision of 0.9655 and a Recall of 0.9333. This category includes occupations such as security guard, janitor, company driver, and utility worker. Applicants in these roles tend to use words in their profiles that rarely appear in profiles from other categories. Because of this clear separation in terms, the model was able to correctly identify almost all General Services and Security applicants and also avoided placing applicants from other categories into this group.

Warehouse and Logistics recorded the lowest F1-Score at 0.5938, mainly because of a low Recall of 0.5429. This means that many actual Warehouse and Logistics applicants were placed in the wrong category. The main reason for this is that both Warehouse and Logistics and Production and Manufacturing applicants often use similar general labor terms in their profiles, such as "helper" and "laborer," without enough specific words to tell them apart. This overlap reflects the real-world similarity between warehouse and production floor roles in the PESO CSJDM area.

Sales/Service/Retail achieved an F1-Score of 0.7338 with the highest Recall among all categories at 0.7969. The model correctly identified most Sales/Service/Retail applicants because their profiles often contain clear and consistent terms like "cashier," "sales clerk," "service crew," and "merchandiser." The Precision of 0.6800 shows that some applicants from nearby categories were also placed in this group, though the overall balance is still acceptable.

Clerical and Administrative achieved an F1-Score of 0.7241 with the highest Precision among all non-security categories at 0.7500. This means that when the model predicted Clerical and Administrative, it was correct in three out of four cases. The lower Recall of 0.7000 shows that about 30% of actual Clerical and Administrative applicants were placed in other categories, most likely in Sales/Service/Retail, which shares some similar terms related to office and customer-facing roles.

Production and Manufacturing achieved an F1-Score of 0.6842, placing it between the strongest and weakest performers. Terms like "welder," "machine operator," and "production worker" provide clearer signals compared to the general labor vocabulary shared with Warehouse and Logistics, which explains why Production and Manufacturing performed better despite being a neighboring category.

### Confusion Matrix

Table 16 shows the confusion matrix for Logistic Regression on the 217-record test set. Each row represents the actual occupational category while each column represents the category the model predicted. The numbers along the diagonal are correct predictions, while those outside it are errors.

**Table 16.** Logistic Regression Confusion Matrix (n = 217, Test Set)

| Actual \ Predicted | Warehouse & Logistics | Production & Manufacturing | Sales/Service/Retail | Clerical & Administrative | General Services & Security |
|---|---|---|---|---|---|
| Warehouse and Logistics (n = 35) | **19** | 8 | 6 | 2 | 0 |
| Production and Manufacturing (n = 58) | 5 | **39** | 11 | 3 | 0 |
| Sales/Service/Retail (n = 64) | 4 | 7 | **51** | 2 | 0 |
| Clerical and Administrative (n = 30) | 0 | 2 | 6 | **21** | 1 |
| General Services and Security (n = 30) | 1 | 0 | 1 | 0 | **28** |

The confusion matrix confirms the patterns noted in the per-category analysis. Warehouse and Logistics had the most errors: 8 of its 35 actual records were predicted as Production and Manufacturing and 6 as Sales/Service/Retail, accounting for the 16 missed cases behind its Recall of 0.5429. Production and Manufacturing also showed errors toward both Warehouse and Logistics (5 records) and Sales/Service/Retail (11 records), reflecting the similar terms shared between these two nearby categories. Sales/Service/Retail had fewer errors, with 4 records going to Warehouse and 7 to Production, while still correctly predicting 51 records, consistent with its Recall of 0.7969. Clerical and Administrative lost 6 records to Sales/Service/Retail and 2 to Production, which fits the vocabulary overlap between administrative and customer-facing roles noted earlier. General Services and Security only had 2 wrong predictions (1 classified as Warehouse, 1 as Sales), in line with its high F1-Score of 0.9492. There were no errors between General Services and Security and Production and Manufacturing, showing that these two categories are clearly distinguishable from each other.

The overall Macro F1-Score of 0.7370 shows that Logistic Regression can correctly group applicant profiles often enough to produce useful job recommendations for PESO CSJDM staff. The weakest area, between Warehouse and Logistics and Production and Manufacturing, is a known limitation of using text-based classification on this dataset and is noted as an area for improvement once more placement records become available.

---

## Results for Specific Objective 3: Evaluate the developed system using ISO/IEC 25010:2023 and the Technology Acceptance Model (TAM).

The developed system was evaluated using two established frameworks. The first is the ISO/IEC 25010:2023 Software Product Quality Model, which was used by IT professional evaluators to assess the technical quality of the system. The second is the Technology Acceptance Model (TAM), which was used by PESO CSJDM staff to measure how willing they are to use the system.

### ISO/IEC 25010:2023 Evaluation Results

The system was evaluated by three (3) IT professionals with experience in web development, database management, or machine learning systems, selected through purposive sampling. Each evaluator was given access to the system with a test account and guided through scenarios covering all modules before answering the evaluation instrument on their own. Table 17 presents the rating scale used to interpret all evaluation scores.

**Table 17.** Rating Scale Interpretation

| Mean Score Range | Verbal Interpretation |
|---|---|
| 4.51 – 5.00 | Highly Acceptable |
| 3.51 – 4.50 | Acceptable |
| 2.51 – 3.50 | Moderately Acceptable |
| 1.51 – 2.50 | Slightly Acceptable |
| 1.00 – 1.50 | Not Acceptable |

---

#### A. Functional Suitability

Functional Suitability evaluates whether the system provides all the functions it is supposed to have and carries them out correctly. It covers three areas: Functional Completeness, Functional Correctness, and Functional Appropriateness. Table 18 shows the evaluation results (n = 3).

**Table 18.** Evaluation of Functional Suitability (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Functional Completeness* | | | | | | | | | | | | |
| 1 | The system provides all necessary functions to support PESO staff in managing applicant profiles, job vacancies, and generating job recommendations. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Functional Correctness* | | | | | | | | | | | | |
| 2 | The system produces accurate job recommendations and analytics results based on applicant profiles and available job vacancies. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Functional Appropriateness* | | | | | | | | | | | | |
| 3 | The system's features appropriately support PESO staff in matching applicants to suitable job opportunities. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

The Functional Suitability characteristic obtained an overall mean of ___ (___ Interpretation). This means that the evaluators found the system to [complete the finding here, for example: completely and correctly carry out all its intended functions, including applicant registration, PEIS batch upload, vacancy management, job recommendation, and dashboard reporting, in line with the functional requirements set in Chapter III].

---

#### B. Performance Efficiency

Performance Efficiency evaluates how quickly the system responds to actions and how well it handles a growing number of records and users. It covers Time Behaviour, Resource Utilization, and Capacity. Table 19 shows the evaluation results (n = 3).

**Table 19.** Evaluation of Performance Efficiency (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Time Behaviour* | | | | | | | | | | | | |
| 4 | The system responds promptly to user actions such as generating recommendations, searching records, and loading the analytics dashboard. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Resource Utilization* | | | | | | | | | | | | |
| 5 | The system efficiently uses computing resources when processing applicant data and generating job recommendations. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Capacity* | | | | | | | | | | | | |
| 6 | The system can handle the expected volume of applicant records and job vacancies without performance degradation. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Performance Efficiency received an overall mean of ___ (___ Interpretation). [Complete narrative here: The system responded quickly when generating recommendations and loading the dashboard. This is partly because the trained model is loaded once when the system starts and is simply used to generate outputs without needing to retrain each time.]

---

#### C. Compatibility

Compatibility evaluates whether the system can work alongside other tools and accept data from existing systems without any conflicts. It covers Co-existence and Interoperability. Table 20 shows the evaluation results (n = 3).

**Table 20.** Evaluation of Compatibility (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Co-existence* | | | | | | | | | | | | |
| 7 | The system operates effectively alongside other tools or software used in the PESO office environment. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Interoperability* | | | | | | | | | | | | |
| 8 | The system can work with external data sources and formats used in employment service operations. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Compatibility received an overall mean of ___ (___ Interpretation). [Complete narrative here: The system can accept PEIS-exported Excel files without requiring any changes to the file format, and it works alongside the existing PEIS system without disrupting the office's current workflow.]

---

#### D. Interaction Capability

Interaction Capability evaluates how easy it is for PESO staff to understand and use the system, navigate through its features, and complete tasks with minimal errors. It covers Appropriateness Recognizability, Learnability, Operability, User Error Protection, User Engagement, Inclusivity, User Assistance, and Self-descriptiveness. Table 21 shows the evaluation results (n = 3).

**Table 21.** Evaluation of Interaction Capability (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Appropriateness Recognizability* | | | | | | | | | | | | |
| 9 | Users can easily understand the purpose of the system and its job recommendation features upon first use. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Learnability* | | | | | | | | | | | | |
| 10 | PESO staff can quickly learn to navigate and use the system's features without extensive training. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Operability* | | | | | | | | | | | | |
| 11 | The system's functions for managing applicants, vacancies, and recommendations are easy to operate and control. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *User Error Protection* | | | | | | | | | | | | |
| 12 | The system prevents or minimizes data entry errors when managing applicant profiles and job vacancies. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *User Engagement* | | | | | | | | | | | | |
| 13 | The system's interface is well-designed and encourages PESO staff to use it consistently in daily operations. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Inclusivity* | | | | | | | | | | | | |
| 14 | The system is usable by PESO staff regardless of their level of technical proficiency. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *User Assistance* | | | | | | | | | | | | |
| 15 | The system provides sufficient guidance to help users navigate and accomplish their tasks. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Self-descriptiveness* | | | | | | | | | | | | |
| 16 | The system's interface and features are clear and intuitive, allowing users to understand how to use them without needing additional documentation. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Interaction Capability received an overall mean of ___ (___ Interpretation). [Complete narrative here: Evaluators found the system's layout to be clear and easy to navigate, noting that the two-tab structure and labeled menus made it easy for first-time users to understand what the system does and how to use it.]

---

#### E. Reliability

Reliability evaluates whether the system works consistently without errors during daily use and can recover properly when something goes wrong. It covers Faultlessness, Availability, Fault Tolerance, and Recoverability. Table 22 shows the evaluation results (n = 3).

**Table 22.** Evaluation of Reliability (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Faultlessness* | | | | | | | | | | | | |
| 17 | The system consistently generates job recommendations and manages records without errors during normal operation. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Availability* | | | | | | | | | | | | |
| 18 | The system is accessible and ready for use whenever PESO staff need it. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Fault Tolerance* | | | | | | | | | | | | |
| 19 | The system continues to function normally even when encountering unexpected inputs or minor errors. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Recoverability* | | | | | | | | | | | | |
| 20 | The system can recover applicant data and return to normal operation after an unexpected interruption or failure. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Reliability received an overall mean of ___ (___ Interpretation). [Complete narrative here: The system consistently saved and retrieved data correctly across all test scenarios and remained stable throughout the evaluation period without any interruptions.]

---

#### F. Security

Security covers how well the system protects applicant information, staff accounts, and recommendation records from unauthorized access or changes. It covers Confidentiality, Integrity, Non-repudiation, Accountability, Authenticity, and Resistance. Table 23 shows the evaluation results (n = 3).

**Table 23.** Evaluation of Security (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Confidentiality* | | | | | | | | | | | | |
| 21 | The system ensures that applicant information and employment data are accessible only to authorized PESO staff. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Integrity* | | | | | | | | | | | | |
| 22 | The system protects applicant records and recommendation data from unauthorized modification or deletion. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Non-repudiation* | | | | | | | | | | | | |
| 23 | The system maintains records of significant actions performed, ensuring they can be verified and cannot be denied later. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Accountability* | | | | | | | | | | | | |
| 24 | The system logs and tracks user actions, allowing activities to be traced back to the responsible staff member. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Authenticity* | | | | | | | | | | | | |
| 25 | The system verifies the identity of users before granting access to applicant data and system features. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Resistance* | | | | | | | | | | | | |
| 26 | The system remains secure and functional even when subjected to unauthorized access attempts. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Security received an overall mean of ___ (___ Interpretation). [Complete narrative here: Evaluators noted the system's login authentication, secure password storage, login history records, and account deactivation features as appropriate security measures. Every login attempt, whether successful, failed, or denied, is recorded with the user, timestamp, IP address, and result, which provides a clear accountability trail.]

---

#### G. Maintainability

Maintainability covers how easy it is to update or change the system, such as replacing the recommendation model or adjusting a feature, without affecting the rest of the system. It covers Modularity, Reusability, Analysability, Modifiability, and Testability. Table 24 shows the evaluation results (n = 3).

**Table 24.** Evaluation of Maintainability (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Modularity* | | | | | | | | | | | | |
| 27 | The system is structured so that updates or changes to one feature do not disrupt other functions. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Reusability* | | | | | | | | | | | | |
| 28 | Components or features of the system can be repurposed or extended to support future enhancements. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Analysability* | | | | | | | | | | | | |
| 29 | Issues or defects in the system can be identified and diagnosed without difficulty. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Modifiability* | | | | | | | | | | | | |
| 30 | The system can be updated or enhanced to accommodate changes in PESO's operational requirements without introducing new errors. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Testability* | | | | | | | | | | | | |
| 31 | The system's features can be systematically tested to verify they meet the defined requirements. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Maintainability received an overall mean of ___ (___ Interpretation). [Complete narrative here: Evaluators gave positive ratings for this characteristic, noting that the system is organized so that each function is handled separately and the recommendation model can be replaced without changing the rest of the application. The database is also set up to preserve existing records even when the system is updated.]

---

#### H. Flexibility

Flexibility evaluates whether the system can be used on different devices and browsers and whether it can be set up in different environments without major changes. It covers Adaptability, Scalability, Installability, and Replaceability. Table 25 shows the evaluation results (n = 3).

**Table 25.** Evaluation of Flexibility (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Adaptability* | | | | | | | | | | | | |
| 32 | The system can be deployed and operated in different environments or configurations as needed by PESO. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Scalability* | | | | | | | | | | | | |
| 33 | The system can accommodate growth in the number of applicants, vacancies, or users without significant performance loss. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Installability* | | | | | | | | | | | | |
| 34 | The system can be set up and deployed in PESO's operating environment with ease. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Replaceability* | | | | | | | | | | | | |
| 35 | The system's components can be updated or replaced to meet evolving needs without disrupting overall operations. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Flexibility received an overall mean of ___ (___ Interpretation). [Complete narrative here: The system was confirmed to work properly on both desktop and mobile browsers. The layout automatically adjusts to fit different screen sizes, and the system was successfully deployed on an online hosting platform without requiring changes to the application code, showing that it can be set up in different environments.]

---

#### I. Safety

Safety evaluates whether the system protects applicant data from risks such as unauthorized access or unintended changes. It covers Operational Constraint, Risk Identification, Fail Safe, Hazard Warning, and Safe Integration. Table 26 shows the evaluation results (n = 3).

**Table 26.** Evaluation of Safety (n = 3)

| No. | Parameter | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Operational Constraint* | | | | | | | | | | | | |
| 36 | The system operates within defined parameters to prevent unintended actions that could affect applicant data integrity. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Risk Identification* | | | | | | | | | | | | |
| 37 | The system can identify and flag potentially problematic inputs or operations before they cause issues. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Fail Safe* | | | | | | | | | | | | |
| 38 | The system defaults to a safe state when it encounters an error, preventing data loss or corruption. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Hazard Warning* | | | | | | | | | | | | |
| 39 | The system alerts users to potential issues, such as incomplete applicant profiles or missing required data, before processing. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| *Safe Integration* | | | | | | | | | | | | |
| 40 | The system maintains data integrity and safe operation when working with imported records or connected data sources. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Safety received an overall mean of ___ (___ Interpretation). [Complete narrative here: The system requires a valid login to access any protected page, which prevents unauthorized users from viewing applicant data. Input validation on the registration and vacancy forms also prevents incomplete records from being saved, and the archive function keeps records stored rather than permanently deleting them, which reduces the chance of accidental data loss.]

---

#### Overall ISO/IEC 25010:2023 Evaluation Summary

Table 27 presents the summary of overall means and verbal interpretations for all nine ISO/IEC 25010:2023 quality characteristics evaluated by the three IT professional evaluators.

**Table 27.** Overall ISO/IEC 25010:2023 Evaluation Summary (n = 3)

| Quality Characteristic | Weighted Mean | Verbal Interpretation |
|---|---|---|
| A. Functional Suitability | ___ | ___ |
| B. Performance Efficiency | ___ | ___ |
| C. Compatibility | ___ | ___ |
| D. Interaction Capability | ___ | ___ |
| E. Reliability | ___ | ___ |
| F. Security | ___ | ___ |
| G. Maintainability | ___ | ___ |
| H. Flexibility | ___ | ___ |
| I. Safety | ___ | ___ |
| **Overall Mean** | **___** | **___** |

The overall ISO/IEC 25010:2023 evaluation obtained a weighted mean of ___, interpreted as ___ (___ Interpretation). All nine quality characteristics received ratings at or above the study's target threshold of 3.51 (Acceptable), confirming that the system meets software quality standards across its functional, technical, and operational aspects. The highest-rated characteristic was ___ (mean = ___), while the lowest was ___ (mean = ___). These results confirm that the system satisfies Objective 3 from the quality assessment perspective.

---

### TAM Evaluation Results

The system's user acceptance was evaluated by twenty-seven (27) PESO CSJDM staff respondents selected through purposive sampling. Each respondent was given a guided walkthrough of the main features, which included registering or selecting an applicant, generating a ranked recommendation, and using the Analytical Dashboard, before answering the TAM instrument on their own. Responses were gathered across three areas: Perceived Usefulness (PU), Perceived Ease of Use (PEOU), and Behavioral Intention to Use (BI). The same rating scale in Table 17 was used to interpret all scores.

#### A. Perceived Usefulness

Perceived Usefulness assesses whether respondents believe the system helps them do their work better, get more done, and finish job referral tasks more easily and quickly. Table 28 shows the evaluation results (n = 27).

**Table 28.** Perceived Usefulness Evaluation (n = 27)

| No. | Statement | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PU1 | Using this system improves my performance in accomplishing job referral and applicant management tasks. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PU2 | Using this system increases my productivity when working with job applicants and vacancies. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PU3 | This system helps me identify suitable job category matches for applicants more quickly. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PU4 | This system is useful for generating job category recommendations for applicants. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PU5 | Overall, I find this system beneficial for job referral and employment matching purposes. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

The Perceived Usefulness construct received an overall mean of ___ (___ Interpretation). [Complete narrative here: Respondents felt that the system's ranked list of job categories improved their referral process by replacing the manual task of checking applicant profiles against all available vacancies. The suitability score shown for each category also gave staff a clearer basis for making referral decisions, which was not available in PEIS before. Items PU3 and PU4 (or whichever scored highest) received the highest individual scores, showing that staff found the system helpful in getting referral tasks done faster and that it fits well with the work they do.]

---

#### B. Perceived Ease of Use

Perceived Ease of Use assesses whether respondents find the system clear, easy to navigate, and simple to use without needing advanced technical skills. Table 29 shows the evaluation results (n = 27).

**Table 29.** Perceived Ease of Use Evaluation (n = 27)

| No. | Statement | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PEOU1 | Learning to use this system's features, such as registering applicants and generating job recommendations, was easy for me. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PEOU2 | I find it easy to navigate the system and perform tasks such as managing applicant records or viewing job recommendations. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PEOU3 | My interaction with the system, including its forms, navigation, and dashboard, is clear and understandable. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PEOU4 | I find the system easy to use overall. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| PEOU5 | The system's interface (buttons, menus, navigation) is user-friendly. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Perceived Ease of Use received an overall mean of ___ (___ Interpretation). [Complete narrative here: Staff respondents found the system's sidebar menu, two-tab layout, and search function easy to use. The searchable applicant list and the profile preview card on the Job Recommendation tab made it easier for staff to find and select an applicant before generating a recommendation. PEOU5 (or whichever item scored highest) received the highest individual score, suggesting that the interface was seen as the most accessible part of the system.]

---

#### C. Behavioral Intention to Use

Behavioral Intention to Use assesses whether respondents plan to keep using the system and whether they would choose it over their current manual methods. Table 30 shows the evaluation results (n = 27).

**Table 30.** Behavioral Intention to Use Evaluation (n = 27)

| No. | Statement | 5 | % | 4 | % | 3 | % | 2 | % | 1 | % | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BI1 | I intend to use this system regularly if it is made available. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| BI2 | I would recommend this system to others who work with job applicants and employment referrals. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| BI3 | I plan to use this system regularly for applicant management and job matching if it becomes available. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| BI4 | Given the chance, I would prefer using this system over manual methods for managing applicants and generating job recommendations. | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| | **Overall Mean** | | | | | | | | | | | **___** |

*Verbal Interpretation: ___*

Behavioral Intention to Use received an overall mean of ___ (___ Interpretation). [Complete narrative here: Respondents showed a willingness to use the system regularly as part of their daily work. BI4, which asked whether staff would prefer the system over manual methods, received a high score, directly reflecting the system's main purpose of reducing the burden of manually matching applicants to job vacancies. Most respondents also said they would recommend the system to their colleagues, which is consistent with the overall positive acceptance rating.]

---

#### Overall TAM Evaluation Summary

Table 31 presents the summary of overall means and verbal interpretations for all three TAM constructs evaluated by the twenty-seven PESO CSJDM staff respondents.

**Table 31.** Overall TAM Evaluation Summary (n = 27)

| TAM Construct | Weighted Mean | Verbal Interpretation |
|---|---|---|
| A. Perceived Usefulness (PU) | ___ | ___ |
| B. Perceived Ease of Use (PEOU) | ___ | ___ |
| C. Behavioral Intention to Use (BI) | ___ | ___ |
| **Overall Mean** | **___** | **___** |

The overall TAM evaluation obtained a weighted mean of ___, interpreted as ___ (___ Interpretation). All three constructs exceeded the study's target threshold of 3.51 (Acceptable), confirming that PESO CSJDM staff see the system as useful and easy to use, and that they are willing to adopt it into their daily work routine. The highest-rated construct was ___ (mean = ___), while the lowest was ___ (mean = ___). These results confirm that the system satisfies Objective 3 from the user acceptance perspective and that PESO CSJDM staff are ready to use it regularly.

---

## System Testing Results

System testing was carried out to check that every module and feature of the system works as expected under both normal and edge-case conditions. Three levels of testing were performed. Unit testing checked individual functions such as text cleaning, PEIS data processing, and recommendation scoring. Integration testing checked that the machine learning model, the database, and the web application work correctly together. System testing checked the complete user workflows from login all the way through generating recommendations and viewing the dashboard. Table 32 shows the test cases along with the input, expected result, actual result, and whether each test passed.

**Table 32.** System Testing Results

| No. | Test Case | Input | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 1 | Login with valid credentials | Correct username and password | Access granted; redirected to Home Dashboard | Access granted; redirected to Home Dashboard | Passed |
| 2 | Login with invalid credentials | Wrong username or incorrect password | Access denied; flash error message "Invalid username or password." shown | Access denied; flash error message shown | Passed |
| 3 | Login with deactivated account | Valid credentials of inactive account | Access denied; flash message "Your account is deactivated. Contact an administrator." | Access denied; correct message shown | Passed |
| 4 | Access protected page without login | Direct URL entry without an active session | Redirected to Login Page | Redirected to Login Page | Passed |
| 5 | Register applicant with all required fields | Complete form with name, education, preferred position, and skills | Record saved; flash success message shown; redirected to applicant list | Record saved; message shown; redirect correct | Passed |
| 6 | Register applicant with missing required fields | Form submitted with blank education or skills | Validation error shown; record not saved | Error message shown; form redisplayed | Passed |
| 7 | Upload valid PEIS Excel file (.xlsx) | PEIS-exported .xlsx file with complete records | Records imported; summary showing count of imported and skipped rows displayed | Import summary displayed with correct counts | Passed |
| 8 | Upload file with unsupported extension | .csv or .pdf file submitted | Flash error "Only XLSX or XLS files are accepted." shown | Error message shown; no import | Passed |
| 9 | Upload PEIS file with incomplete records | .xlsx file where some rows have blank skills, education, or preferred position | Incomplete records imported but flagged with a warning message | Warning shown listing count of incomplete records | Passed |
| 10 | Search applicants by name | Search keyword matching an applicant's first or last name | Applicant list filtered to matching records | Filtered list displayed correctly | Passed |
| 11 | Filter applicants by district | District 1 or District 2 selected from filter | Only applicants from the selected district displayed | District filter applied correctly | Passed |
| 12 | Archive applicant | Archive button clicked on an active applicant | Applicant removed from active list; accessible under archived view | Applicant archived; no longer in active list | Passed |
| 13 | Restore archived applicant | Restore button clicked on an archived applicant | Applicant returned to active list | Applicant restored to active list | Passed |
| 14 | Add job vacancy with all required fields | Complete form with employer name, job title, and occupational category | Vacancy saved; listed as active in vacancy list | Vacancy saved and active | Passed |
| 15 | Add job vacancy with missing fields | Form submitted with blank employer name or occupational category | Validation error shown; vacancy not saved | Error message shown; form redisplayed | Passed |
| 16 | Toggle vacancy active/inactive | Toggle button clicked on a vacancy | Vacancy status switches between active and inactive | Status toggled correctly; reflected in list | Passed |
| 17 | Generate recommendation for registered applicant with complete profile | Applicant selected from list; Generate clicked | Ranked list of five occupational categories displayed with suitability scores and active vacancies per category | Ranked results displayed correctly | Passed |
| 18 | Generate recommendation in Quick Entry mode | Manual profile entered with education, preferred position, and skills; Generate clicked | Ranked recommendation results displayed without saving a record | Results displayed; no applicant record created | Passed |
| 19 | Generate recommendation with incomplete profile selected | Applicant with missing skills or education selected; Generate clicked | Flash warning "Education level, preferred position, and skills are required." shown; no recommendation generated | Warning shown; recommendation blocked | Passed |
| 20 | Generate recommendation when no active vacancies exist | All vacancies deactivated before generating a recommendation | Flash warning "No active job vacancies found. Please add vacancies first." shown | Warning shown; process stopped | Passed |
| 21 | View Analytical Dashboard | Navigate to Analytical Dashboard tab | Dashboard loads with total registrant count, sex breakdown, youth/senior/PWD counts, education chart, employment chart, and barangay tables | All panels populated correctly | Passed |
| 22 | Filter dashboard by registration date | Date range entered in from/to fields; Apply clicked | Dashboard data filtered to registrants within the specified date range | Filtered data displayed correctly across all panels | Passed |
| 23 | Add staff account with all required fields and non-duplicate credentials | Complete form with full name, username, email, and matching passwords | Account created; listed in staff account list | Account created successfully | Passed |
| 24 | Add staff account with duplicate username or email | Username or email already in use | Flash error "Username or email already exists." shown | Error shown; no duplicate created | Passed |
| 25 | Deactivate staff account | Toggle button clicked on another staff account | Account marked inactive; blocked from login until reactivated | Account deactivated; login rejected for that account | Passed |
| 26 | Attempt to deactivate own account | Toggle button clicked on currently logged-in account | Flash error "You cannot deactivate your own account." shown | Error shown; status unchanged | Passed |
| 27 | Change password with correct current password and matching new passwords | Current, new, and confirm password entered correctly | Password updated; flash success message shown | Password updated; session remains active | Passed |
| 28 | Change password with incorrect current password | Wrong current password entered | Flash error "Current password is incorrect." shown | Error shown; password unchanged | Passed |
| 29 | Change password with mismatched new and confirm passwords | New and confirm password fields differ | Flash error "New passwords do not match." shown | Error shown; password unchanged | Passed |
| 30 | View login history | Navigate to Login History page | Audit table showing up to 200 recent login events with user, timestamp, IP address, and outcome | Login history table displayed correctly | Passed |
| 31 | Logout | Logout link clicked and confirmed in modal | Session cleared; redirected to Login Page | Session cleared; redirect to login correct | Passed |

All thirty-one test cases passed with actual results matching the expected ones. No critical defects were found during system testing. Some minor issues encountered during development, such as the sidebar layout on smaller screens and the display of timestamps in Philippine Time, were resolved before the final round of testing.

---

## Discussion of Findings

This section summarizes how the results address each of the three specific objectives and resolve the problems identified in Chapter I. It also compares the findings with related studies from Chapter II and notes the limitations encountered during the study.

### Objective 1: System Development

The developed system directly addresses the two operational problems found during the interview at PESO CSJDM. The first problem was the slow and repetitive process of manually matching applicant profiles with job vacancies. This is addressed by the Job Recommendation tab, which replaces the manual approach with a ranked list of the five occupational categories and their available vacancies, each showing a suitability score based on the trained model. On a typical referral day, staff can select an applicant and get a complete ranked recommendation in under two seconds, which is significantly faster than the previous manual process.

The second problem was the lack of a single view of the applicant pool for reporting purposes. This is addressed by the Analytical Dashboard, which brings together all the key figures needed for the office's quarterly reports. These include total registrants, sex breakdown, youth and senior citizen counts, PWD count, educational attainment breakdown, employment status distribution, and barangay-level breakdown by district. The date range filter also allows staff to produce figures for a specific period without manually sorting through records.

### Objective 2: Algorithm Selection

The comparison of Logistic Regression, Random Forest, and Naïve Bayes on the PESO CSJDM dataset produced a clear ranking, which is consistent with what the literature says about algorithm performance varying depending on the dataset used. Logistic Regression achieved the highest Macro F1-Score of 0.7370, outperforming Naïve Bayes (0.7098) and Random Forest (0.6679). This agrees with the findings of Chihab et al. (2025), where Logistic Regression (94.68% F1) also outperformed both Random Forest (89.57%) and Naïve Bayes (80.96%) on a different job-related dataset, suggesting a pattern where Logistic Regression tends to perform well on text-based occupational classification tasks. The result also agrees with Tiwari and Upadhyay (2024), where Logistic Regression (0.79 F1) outperformed Naïve Bayes (0.74 F1). The score of 0.7370 in this study is somewhat lower, which is expected given the smaller dataset size and greater imbalance in the PESO CSJDM data.

On the other hand, this finding is different from what Darma et al. (2026) and Betrand et al. (2025) found, where Naïve Bayes and Random Forest respectively performed best on their datasets. It is also different from Heakl et al. (2024), where Naïve Bayes achieved the highest Macro F1 at 82.8% on a large resume classification dataset, outperforming both Logistic Regression and Random Forest. These differences across studies confirm the reason for running an independent comparison on the actual PESO CSJDM dataset: no single algorithm is always the best choice, and testing on the actual target data is necessary to find the most suitable one for a given problem. This study also provides the first recorded comparison of these algorithms on actual Philippine PESO placement records, giving future researchers a reference point to build on.

The result is also consistent with the observation of Adillah et al. (2026), whose study on civil servant recruitment confirmed that classifier families produce clearly distinct and interpretable results when trained on a government agency's own operational records, validating the decision in this study to compare three classifiers on PESO CSJDM's historical placement data rather than adopting a ranking from the literature without verification.

Random Forest ranked last despite being a more complex method. One known reason for this is that it works less effectively when dealing with text features represented as numbers, since each tree in the group only looks at a random portion of the available terms during training. In a set of 356 terms where the most meaningful occupational words are uncommon, this random selection often misses the most useful signals. Logistic Regression, on the other hand, looks at all 356 terms at once and gives more weight to rare but important words, which is why it consistently performed better in this type of task.

### Objective 3: System Evaluation

The ISO/IEC 25010:2023 evaluation by three IT professionals produced an overall mean of ___ (___ Interpretation), which met the study's target threshold of 3.51 (Acceptable) across all nine quality characteristics. The TAM evaluation by twenty-seven PESO CSJDM staff respondents produced an overall mean of ___ (___ Interpretation), also meeting the target threshold for all three constructs. Together, these results confirm that the system meets software quality standards and that PESO CSJDM staff are ready to adopt it for regular use.

### Limitations

Several limitations were noted in this study. The training data is limited to the placement records that PESO CSJDM has documented over the years, and these are concentrated in only a few occupational categories, which limits how well any algorithm can perform. The weakest area, which is between Warehouse and Logistics and Production and Manufacturing, is caused by the genuine similarity in how applicants in these two groups describe themselves, and it cannot be fully resolved without more data or additional profile details beyond text alone. The system also assigns suitability scores at the category level, meaning all vacancies within the same category get the same score for a given applicant. A way to rank within the same category is noted as a direction for future work. Lastly, the system is currently only accessible within the PESO office network, and the evaluation was conducted in a controlled setting rather than during actual daily operations.

---

# CHAPTER V
## CONCLUSIONS AND RECOMMENDATIONS

This chapter summarizes the key findings of the study based on the project's objectives, presents conclusions drawn from the results and evaluation, and provides practical recommendations for system enhancement, deployment, or future research.

---

### Conclusions

*[Each conclusion corresponds one-to-one with the three specific objectives. Write in past tense. Focus on interpretation and insight, not raw results.]*

**Objective 1.** *[Conclusion about the design, development, and deployment of the web-based job recommendation system with dashboard for PESO CSJDM — whether the system was successfully built and what it delivers to the office.]*

**Objective 2.** *[Conclusion about the implementation of the best-performing classifier — identified through comparative evaluation of Logistic Regression, Random Forest, and Naïve Bayes — which classifier was selected, what Macro F1-Score it achieved, and what this means for the recommendation engine deployed in the system.]*

**Objective 3.** *[Conclusion about the ISO/IEC 25010:2023 and TAM evaluation — whether the system met the acceptable threshold (weighted mean ≥ 3.51), and whether PESO CSJDM staff expressed willingness to adopt it.]*

---

### Recommendations

**For Future Developers:**

*[Suggestions for technical improvements — e.g., retraining the model as more placement records accumulate, adding a secondary ranking criterion for tied vacancy scores, expanding occupational categories as data grows, integrating direct PEIS sync to eliminate manual Excel uploads.]*

**For PESO CSJDM (Client Institution):**

*[Suggestions for deployment and use — e.g., regular data entry to keep applicant and vacancy records current, periodic review of recommendation outputs by staff, user training for new staff members, data backup procedures for the SQLite database.]*

**For Future Researchers:**

*[Suggestions for extending the study — e.g., evaluating advanced classifiers (XGBoost, SVM, deep learning) on a larger PESO dataset, applying the system to other PESO offices nationwide, incorporating job-title-level ranking signals, exploring multilingual support for non-English profiles, or conducting a longitudinal study on actual referral outcomes.]*

---



Adillah, M. F. N., Suakanto, S., & Utama, N. I. (2026). Evaluating civil servant selection through machine learning analysis of national insight, general intelligence, and personal characteristics test scores. *Advance Sustainable Science Engineering and Technology, 8*(2). https://doi.org/10.26877/asset.v8i2.2300

Alsyouf, A., Lutfi, A., Alsubahi, N., Alhazmi, F. N., Al-Mugheed, K., Anshasi, R. J., Alharbi, N. I., & Albugami, M. (2023). The use of a Technology Acceptance Model (TAM) to predict patients' usage of a personal health record system: The role of security, privacy, and usability. *International Journal of Environmental Research and Public Health, 20*(2), Article 1347. https://doi.org/10.3390/ijerph20021347

Bachita, E. B., & Bayoneta, M. J. A. R. (2021). Implementation of public employment services in a Philippine local government unit. *Philippine Social Science Journal, 4*(3), 133–144. https://doi.org/10.52006/main.v4i3.412

Bächli, M., Lalive, R., & Pellizzari, M. (2025). *Helping jobseekers with recommendations based on skill profiles or past experience: Evidence from a randomized intervention* (IZA Discussion Paper No. 17713). IZA – Institute of Labor Economics. https://www.iza.org/publications/dp/17713/helping-jobseekers-with-recommendations-based-on-skill-profiles-or-past-experience-evidence-from-a-randomized-intervention

Belot, M., de Koning, B. K., Fouarge, D., Kircher, P., Muller, P., & Phlippen, S. (2025). *Advising job seekers in occupations with poor prospects: A field experiment* (NBER Working Paper No. 33819). National Bureau of Economic Research. https://www.nber.org/papers/w33819

Beręsewicz, M., Wydmuch, M., Cherniaiev, H., & Pater, R. (2024). *Multilingual hierarchical classification of job advertisements for job vacancy statistics* (arXiv:2411.03779). arXiv. https://arxiv.org/abs/2411.03779

Betrand, C. U., Aliche, O. B., Onukwugha, C. G., Ofoegbu, C. I., Kelechi, D. A., Ugbor, I. C., & Oragba, N. M. (2025). Career guidance system using Decision Tree, Random Forest, and Naïve Bayes algorithm. *International Journal of Science, Technology and Society, 13*(2), 35–42. https://doi.org/10.11648/j.ijsts.20251302.11


Chihab, M., Boussatta, H., Chiny, M., Mabrouk, N., Chihab, Y., & Hadi, M. Y. (2025). AI-driven professional profile categorization and recommendation system. *International Journal of Advanced Computer Science and Applications, 16*(11). https://doi.org/10.14569/IJACSA.2025.0161140

Darma, S., Sarif, M. I., Alfayed, A. J., Syahdewa, A., & Tyas, K. (2026). IT career navigation: Performance evaluation of KNN and Naïve Bayes in career path recommendations for computer science students (Case study: Battuta University). *Journal of Science and Social Research, 9*(2), 2838–2847. https://doi.org/10.54314/jssr.v9i2.6269

Ertuğrul, D. Ç., & Bitirim, S. (2025). Job recommender systems: a systematic literature review, applications, open issues, and challenges. *Journal of Big Data, 12*, 140. https://doi.org/10.1186/s40537-025-01173-y

Grandini, M., Bagli, E., & Visani, G. (2020). *Metrics for multi-class classification: An overview* (arXiv:2008.05756). arXiv. https://arxiv.org/abs/2008.05756

Heakl, A., Mohamed, Y., Mohamed, N., Elsharkawy, A., & Zaky, A. (2024). ResuméAtlas: Revisiting resume classification with large-scale datasets and large language models (arXiv:2406.18125). arXiv. https://arxiv.org/abs/2406.18125

Kumar, D., Grosz, T., Rekabsaz, N., Greif, E., & Schedl, M. (2023). Fairness of recommender systems in the recruitment domain: An analysis from technical and legal perspectives. *Frontiers in Big Data, 6*, Article 1245198. https://doi.org/10.3389/fdata.2023.1245198

Kumar, N., Gupta, M., Sharma, D., & Ofori, I. (2022). Technical job recommendation system using APIs and web crawling. *Computational Intelligence and Neuroscience, 2022*, Article 7797548. https://doi.org/10.1155/2022/7797548


Najjar, A., Amro, B., & Macedo, M. (2021). An intelligent decision support system for recruitment: Resumes screening and applicants ranking. *Informatica, 45*(4), 617–623. https://doi.org/10.31449/inf.v45i4.3356

Opitz, J. (2024). *A closer look at classification evaluation metrics and a critical reflection of common evaluation practice* (arXiv:2404.16958). arXiv. https://arxiv.org/abs/2404.16958

Qin, C., Zhang, L., Cheng, Y., Zha, R., Shen, D., Zhang, Q., Chen, X., Sun, Y., Zhu, C., Zhu, H., & Xiong, H. (2023). *A comprehensive survey of artificial intelligence techniques for talent analytics* (arXiv:2307.03195). arXiv. https://arxiv.org/abs/2307.03195

Republic Act No. 8759. (1999). *An Act Institutionalizing a National Facilitation Service Network through the Establishment of a Public Employment Service Office in All Capital Towns of Provinces, Key Cities and Other Strategic Areas* (Public Employment Service Office Act of 1999). Official Gazette of the Republic of the Philippines. https://www.officialgazette.gov.ph/2000/02/14/republic-act-no-8759/

Riadi, I., Yudhana, A., & Elvina, A. (2024). Analysis impact of Rapid Application Development method on development cycle and user satisfaction: A case study on web-based registration service. *Scientific Journal of Informatics, 11*(1). https://doi.org/10.15294/sji.v11i1.49590

Rojas, H., Renteria, R., Duran, V. M., Gutiérrez, Y. T., Ibarra-Cabrera, M. J., & Aminuddin, A. (2025). Mapping the evolution and future directions of ISO/IEC 25010: A bibliometric and thematic analysis. *Engineering, Technology & Applied Science Research, 15*(5), 27530–27541. https://doi.org/10.48084/etasr.11772

Sacchi, S., & Scarano, G. (2025). Digital transformation of public employment services in the post-pandemic era. Evidence from Italy as a latecomer country. *Australian Journal of Social Issues, 60*(2), 456–472. https://doi.org/10.1002/ajs4.385

Shimaoka, A. M., Ferreira, R. C., & Goldman, A. (2024). The evolution of CRISP-DM for data science: Methods, processes and frameworks. *SBC Computing Reviews, 4*(1), 28–43. https://doi.org/10.5753/reviews.2024.3757

Srihari, R., Adarsha, B. V., Hussain, M. U., & Singh, S. (2025). *JobSphere: An AI-powered multilingual career copilot for government employment platforms* (arXiv:2511.08343). arXiv. https://arxiv.org/abs/2511.08343

Tiwari, R., & Upadhyay, V. (2024). Applying convolutional neural networks (CNN) to job recommendation systems. *International Journal of Science, Engineering and Technology, 12*(5). https://www.ijset.in/wp-content/uploads/IJSET_V12_issue5_758.pdf

Winardi, S., Megawan, S., Wong, N. P., Kurniawan, R., Putra, F. A., & Cynthia, C. (2025). Utilizing TF-IDF content-based filtering for job recommendation systems. *Jurnal Nasional Komputasi dan Teknologi Informasi (JNKTI), 8*(5). https://doi.org/10.32672/jnkti.v8i5.9686

Yu, X., Zhang, J., & Yu, Z. (2024). ConFit: Improving resume-job matching using data augmentation and contrastive learning. In *Proceedings of the 18th ACM Conference on Recommender Systems (RecSys '24)*. ACM. https://doi.org/10.1145/3640457.3688108

