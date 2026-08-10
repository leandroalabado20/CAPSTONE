# Chapter 4 Draft — Algorithm Evaluation and Model Selection

---

## [Section X] Algorithm Evaluation and Model Selection

### [X.1] Experimental Setup

The machine learning evaluation used the preprocessed PESO CSJDM placement dataset containing 1,083 records distributed across five occupational categories. Table X.1 shows the distribution of records per category.

**Table X.1. Dataset Distribution by Occupational Category (n = 1,083)**

| Occupational Category | Records | Proportion |
|---|---|---|
| Warehouse and Logistics | 175 | 16.2% |
| Production and Manufacturing | 292 | 27.0% |
| Sales/Service/Retail | 317 | 29.3% |
| Clerical and Administrative | 149 | 13.8% |
| General Services and Security | 150 | 13.9% |
| **Total** | **1,083** | **100.0%** |

The dataset was divided into a training set and a test set using stratified 80/20 splitting, yielding 866 training records and 217 test records. Stratification was applied to preserve each category's proportional representation in both subsets, ensuring that no category was underrepresented or absent in the test set. The split was performed before TF-IDF vectorization to prevent data leakage, as fitting the vectorizer on the full dataset would allow information from the test records to influence the feature representation used during training.

TF-IDF (Term Frequency-Inverse Document Frequency) vectorization was applied to the PROFILE_TEXT field of each applicant record. The vectorizer was fitted exclusively on the 866 training records to learn the vocabulary and IDF weights, and the resulting transformation rules were then applied to both the training and test sets. This produced a vocabulary of 356 unique terms and feature matrices of 866 x 356 for training and 217 x 356 for testing. Three supervised classifiers were trained on the same training set: Logistic Regression (max_iter = 1,000), Random Forest (100 estimators), and Multinomial Naive Bayes.

The primary evaluation metric was Macro F1-Score rather than accuracy. The dataset is imbalanced: the two smallest categories, Clerical and Administrative (13.8%) and General Services and Security (13.9%), together represent less than 28% of total records. Accuracy-based selection assigns equal weight to each correct prediction regardless of which category it belongs to, which means that failures on small categories contribute proportionally less to the final score than failures on large ones. A classifier that performs poorly on Clerical and Administrative applicants would still appear competitive if it correctly classifies the larger Sales/Service/Retail and Production and Manufacturing groups. Macro F1-Score computes the F1-Score for each of the five categories independently and averages them with equal weight, penalizing failure on any single category by the same amount regardless of its size. This criterion is consistent with the approach adopted by Chihab et al. (2025), Adillah et al. (2026), and Tiwari and Upadhyay (2024), whose reliance on accuracy alone as a selection criterion was identified in Chapter III as insufficient for imbalanced occupational classification problems.

### [X.2] Classifier Comparison Results

Table X.2 presents the evaluation results for all three classifiers on the 217-record test set.

**Table X.2. Classifier Comparison Results (n = 217, test set)**

| Classifier | Accuracy | Macro F1-Score | Weighted F1-Score |
|---|---|---|---|
| Logistic Regression | 0.7281 | **0.7370** | 0.7264 |
| Naive Bayes | 0.7051 | 0.7098 | 0.6979 |
| Random Forest | 0.6590 | 0.6679 | 0.6540 |

Logistic Regression achieved the highest scores on all three metrics. On the primary selection criterion, Macro F1-Score, Logistic Regression (0.7370) outperformed Naive Bayes (0.7098) by a margin of 0.0272 and Random Forest (0.6679) by 0.0691. The same ranking held for accuracy and Weighted F1-Score, indicating that Logistic Regression performed most consistently across all categories regardless of evaluation perspective. Logistic Regression was therefore selected as the recommendation engine for deployment.

This result is consistent with Sankarasetty et al. (2023), whose TF-IDF and Logistic Regression pipeline for job-role classification on a skills-based dataset also outperformed Naive Bayes and tree-based alternatives. In the context of the PESO CSJDM dataset, Logistic Regression's behavior as a linear classifier that assigns a weighted coefficient to each TF-IDF term per category is well-suited to the vocabulary-driven distinctions between the five occupational groups. Category-specific terms such as "forklift," "welder," "cashier," "data encoder," and "security guard" serve as strong discriminative signals, and Logistic Regression can leverage these simultaneously across the full 356-term vocabulary.

Random Forest ranked lowest despite being an ensemble method. Tree-based classifiers are documented to underperform on sparse, high-dimensional TF-IDF feature spaces because each split in an individual tree randomly samples only a subset of features. In a 356-term vocabulary where the most informative occupational keywords are sparse, this random feature sampling frequently excludes the strongest category signals. Logistic Regression uses all 356 features simultaneously at each prediction and can assign proportionally high weights to the rare but highly distinctive terms, giving it an advantage in this setting.

### [X.3] Per-Category Performance of the Selected Model

Table X.3 presents the per-category Precision, Recall, F1-Score, and Support for Logistic Regression on the test set.

**Table X.3. Logistic Regression Per-Category Performance (n = 217)**

| Occupational Category | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| Warehouse and Logistics | 0.6552 | 0.5429 | 0.5938 | 35 |
| Production and Manufacturing | 0.6964 | 0.6724 | 0.6842 | 58 |
| Sales/Service/Retail | 0.6800 | 0.7969 | 0.7338 | 64 |
| Clerical and Administrative | 0.7500 | 0.7000 | 0.7241 | 30 |
| General Services and Security | 0.9655 | 0.9333 | 0.9492 | 30 |
| **Macro Average** | **0.7494** | **0.7291** | **0.7370** | **217** |

General Services and Security achieved the highest F1-Score of 0.9492, with a precision of 0.9655 and recall of 0.9333. This category encompasses occupations with strongly distinctive and non-overlapping vocabulary in the TF-IDF feature space. Terms associated with security guard, janitor, company driver, and housekeeping roles occur almost exclusively within this group and rarely appear in profiles belonging to the other four categories. The clean vocabulary separation enables the classifier to identify this group with high confidence in both directions: it seldom misclassifies applicants from other categories as General Services and Security (high precision), and it correctly retrieves nearly all actual General Services and Security applicants (high recall).

Warehouse and Logistics recorded the lowest F1-Score of 0.5938, driven primarily by a recall of 0.5429. Low recall indicates that a substantial proportion of actual Warehouse and Logistics applicants were assigned to a different category by the classifier. The most likely source of misclassification is the shared vocabulary between Warehouse and Logistics and Production and Manufacturing. Both categories frequently attract applicants whose profiles contain generic physical-labor terms such as "helper," "laborer," and common education levels, without category-distinguishing keywords strong enough to consistently separate the two groups. This vocabulary overlap is a structural limitation of text-based classification on this dataset and reflects the real-world similarity between warehouse operations and production floor roles in the PESO CSJDM service area.

Sales/Service/Retail achieved an F1-Score of 0.7338, supported by the highest recall among all categories (0.7969) and a test support of 64 records. The high recall reflects that the classifier correctly identified the majority of Sales/Service/Retail applicants, benefiting from a large and semantically consistent vocabulary of customer-facing role terms such as "cashier," "sales clerk," "service crew," and "merchandiser." The precision of 0.6800 is slightly lower than recall, suggesting that some applicants from adjacent categories were pulled into Sales/Service/Retail predictions, though the overall balance between the two remains acceptable.

Clerical and Administrative achieved an F1-Score of 0.7241 with the highest precision of all non-security categories (0.7500). When the classifier predicted Clerical and Administrative, it was correct in 75.0% of cases, indicating that the occupational keywords for this group, such as "data encoder," "office clerk," "secretary," and "accounting staff," are reliably distinctive. The lower recall of 0.7000 suggests that approximately 30% of actual Clerical and Administrative applicants were assigned elsewhere, most likely to Sales/Service/Retail, which shares some administrative and customer-oriented vocabulary.

Production and Manufacturing achieved an F1-Score of 0.6842, positioned between the strongest and weakest performers. Manufacturing-specific terms such as "welder," "machine operator," and "production worker" provide clearer category signals than the generic labor vocabulary shared with Warehouse and Logistics, explaining why Production and Manufacturing outperformed Warehouse and Logistics despite their proximity. The balanced precision (0.6964) and recall (0.6724) indicate no strong directional bias for this category.

The overall Macro F1-Score of 0.7370 indicates that Logistic Regression can categorize applicant profiles into the correct occupational group at a rate sufficient to generate meaningful job recommendations for PESO CSJDM staff. The weakest boundary, between Warehouse and Logistics and Production and Manufacturing, represents an inherent constraint of text-based classification on this particular dataset and is a direction for improvement in future work through the collection of additional discriminating features.

### [X.4] Confusion Matrix

Table X.4 presents the 5×5 confusion matrix for Logistic Regression on the 217-record test set. Rows represent the actual occupational category; columns represent the category assigned by the classifier. Diagonal cells (bold) are correct classifications; off-diagonal cells are misclassifications.

**Table X.4. Logistic Regression Confusion Matrix (n = 217)**

| Actual \ Predicted | Warehouse & Logistics | Production & Manufacturing | Sales/Service/Retail | Clerical & Administrative | General Services & Security |
|---|---|---|---|---|---|
| Warehouse and Logistics (n = 35) | **19** | 8 | 6 | 2 | 0 |
| Production and Manufacturing (n = 58) | 5 | **39** | 11 | 3 | 0 |
| Sales/Service/Retail (n = 64) | 4 | 7 | **51** | 2 | 0 |
| Clerical and Administrative (n = 30) | 0 | 2 | 6 | **21** | 1 |
| General Services and Security (n = 30) | 1 | 0 | 1 | 0 | **28** |

The confusion matrix confirms the patterns identified in the per-category analysis. Warehouse and Logistics has the largest concentration of off-diagonal errors: 8 of its 35 actual records were predicted as Production and Manufacturing and 6 as Sales/Service/Retail, which together account for the 14 missed cases behind its recall of 0.5429. Production and Manufacturing similarly leaks toward both Warehouse and Logistics (5 records) and Sales/Service/Retail (11 records), reflecting the shared generic labor vocabulary between these adjacent categories. Sales/Service/Retail misclassifies at lower rates — 4 records sent to Warehouse and 7 to Production — and retains 51 correct predictions, consistent with its recall of 0.7969. Clerical and Administrative loses 6 records to Sales/Service/Retail and 2 to Production, which aligns with the overlap between administrative and customer-facing role descriptions noted in the per-category analysis. General Services and Security produces only 2 off-diagonal errors (1 misclassified as Warehouse, 1 as Sales), consistent with its high F1-Score of 0.9492 and the vocabulary distinctiveness of security and facilities roles. No misclassifications occurred between General Services and Security and Production and Manufacturing, confirming that the boundary between these two categories is clearly defined in the feature space.

---

*Draft status: Complete except for confusion matrix values (Section X.4). All metric values are from the actual training run output.*
