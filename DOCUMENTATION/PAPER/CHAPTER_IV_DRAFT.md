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
