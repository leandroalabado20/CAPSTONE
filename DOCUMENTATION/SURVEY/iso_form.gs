var SCALE = ['5 - Strongly Agree', '4 - Agree', '3 - Neutral', '2 - Disagree', '1 - Strongly Disagree'];

function addRating(form, label) {
  form.addMultipleChoiceItem().setTitle(label).setChoiceValues(SCALE).setRequired(true);
}

function createISO25010Form() {
  var form = FormApp.create('ISO/IEC 25010:2023 Software Quality Evaluation Instrument');
  form.setDescription(
    'Web-Based Data-Driven Job Recommendation System with Dashboard for PESO CSJDM\n\n' +
    'Please assess each item using the following rating scale:\n' +
    '5 - Strongly Agree | 4 - Agree | 3 - Neutral | 2 - Disagree | 1 - Strongly Disagree'
  );

  form.addTextItem().setTitle('Capstone Project Title').setRequired(true);
  form.addTextItem().setTitle('Researchers/Proponents').setRequired(true);
  form.addTextItem().setTitle('Evaluator Name').setRequired(true);
  form.addDateItem().setTitle('Date').setRequired(true);

  // A. FUNCTIONAL SUITABILITY
  form.addSectionHeaderItem().setTitle('A. FUNCTIONAL SUITABILITY');
  addRating(form, '1. Functional Completeness\nThe system provides all necessary functions to support PESO staff in managing applicant profiles, job vacancies, and generating job recommendations.');
  addRating(form, '2. Functional Correctness\nThe system produces accurate job recommendations and analytics results based on applicant profiles and available job vacancies.');
  addRating(form, '3. Functional Appropriateness\nThe system\'s features appropriately support PESO staff in matching applicants to suitable job opportunities.');

  // B. PERFORMANCE EFFICIENCY
  form.addSectionHeaderItem().setTitle('B. PERFORMANCE EFFICIENCY');
  addRating(form, '4. Time Behaviour\nThe system responds promptly to user actions such as generating recommendations, searching records, and loading the analytics dashboard.');
  addRating(form, '5. Resource Utilization\nThe system efficiently uses computing resources when processing applicant data and generating job recommendations.');
  addRating(form, '6. Capacity\nThe system can handle the expected volume of applicant records and job vacancies without performance degradation.');

  // C. COMPATIBILITY
  form.addSectionHeaderItem().setTitle('C. COMPATIBILITY');
  addRating(form, '7. Co-existence\nThe system operates effectively alongside other tools or software used in the PESO office environment.');
  addRating(form, '8. Interoperability\nThe system can work with external data sources and formats used in employment service operations.');

  // D. INTERACTION CAPABILITY
  form.addSectionHeaderItem().setTitle('D. INTERACTION CAPABILITY');
  addRating(form, '9. Appropriateness Recognizability\nUsers can easily understand the purpose of the system and its job recommendation features upon first use.');
  addRating(form, '10. Learnability\nPESO staff can quickly learn to navigate and use the system\'s features without extensive training.');
  addRating(form, '11. Operability\nThe system\'s functions for managing applicants, vacancies, and recommendations are easy to operate and control.');
  addRating(form, '12. User Error Protection\nThe system prevents or minimizes data entry errors when managing applicant profiles and job vacancies.');
  addRating(form, '13. User Engagement\nThe system\'s interface is well-designed and encourages PESO staff to use it consistently in daily operations.');
  addRating(form, '14. Inclusivity\nThe system is usable by PESO staff regardless of their level of technical proficiency.');
  addRating(form, '15. User Assistance\nThe system provides sufficient guidance to help users navigate and accomplish their tasks.');
  addRating(form, '16. Self-descriptiveness\nThe system\'s interface and features are clear and intuitive, allowing users to understand how to use them without needing additional documentation.');

  // E. RELIABILITY
  form.addSectionHeaderItem().setTitle('E. RELIABILITY');
  addRating(form, '17. Faultlessness\nThe system consistently generates job recommendations and manages records without errors during normal operation.');
  addRating(form, '18. Availability\nThe system is accessible and ready for use whenever PESO staff need it.');
  addRating(form, '19. Fault Tolerance\nThe system continues to function normally even when encountering unexpected inputs or minor errors.');
  addRating(form, '20. Recoverability\nThe system can recover applicant data and return to normal operation after an unexpected interruption or failure.');

  // F. SECURITY
  form.addSectionHeaderItem().setTitle('F. SECURITY');
  addRating(form, '21. Confidentiality\nThe system ensures that applicant information and employment data are accessible only to authorized PESO staff.');
  addRating(form, '22. Integrity\nThe system protects applicant records and recommendation data from unauthorized modification or deletion.');
  addRating(form, '23. Non-repudiation\nThe system maintains records of significant actions performed, ensuring they can be verified and cannot be denied later.');
  addRating(form, '24. Accountability\nThe system logs and tracks user actions, allowing activities to be traced back to the responsible staff member.');
  addRating(form, '25. Authenticity\nThe system verifies the identity of users before granting access to applicant data and system features.');
  addRating(form, '26. Resistance\nThe system remains secure and functional even when subjected to unauthorized access attempts.');

  // G. MAINTAINABILITY
  form.addSectionHeaderItem().setTitle('G. MAINTAINABILITY');
  addRating(form, '27. Modularity\nThe system is structured so that updates or changes to one feature do not disrupt other functions.');
  addRating(form, '28. Reusability\nComponents or features of the system can be repurposed or extended to support future enhancements.');
  addRating(form, '29. Analysability\nIssues or defects in the system can be identified and diagnosed without difficulty.');
  addRating(form, '30. Modifiability\nThe system can be updated or enhanced to accommodate changes in PESO\'s operational requirements without introducing new errors.');
  addRating(form, '31. Testability\nThe system\'s features can be systematically tested to verify they meet the defined requirements.');

  // H. FLEXIBILITY
  form.addSectionHeaderItem().setTitle('H. FLEXIBILITY');
  addRating(form, '32. Adaptability\nThe system can be deployed and operated in different environments or configurations as needed by PESO.');
  addRating(form, '33. Scalability\nThe system can accommodate growth in the number of applicants, vacancies, or users without significant performance loss.');
  addRating(form, '34. Installability\nThe system can be set up and deployed in PESO\'s operating environment with ease.');
  addRating(form, '35. Replaceability\nThe system\'s components can be updated or replaced to meet evolving needs without disrupting overall operations.');

  // I. SAFETY
  form.addSectionHeaderItem().setTitle('I. SAFETY');
  addRating(form, '36. Operational Constraint\nThe system operates within defined parameters to prevent unintended actions that could affect applicant data integrity.');
  addRating(form, '37. Risk Identification\nThe system can identify and flag potentially problematic inputs or operations before they cause issues.');
  addRating(form, '38. Fail Safe\nThe system defaults to a safe state when it encounters an error, preventing data loss or corruption.');
  addRating(form, '39. Hazard Warning\nThe system alerts users to potential issues, such as incomplete applicant profiles or missing required data, before processing.');
  addRating(form, '40. Safe Integration\nThe system maintains data integrity and safe operation when working with imported records or connected data sources.');

  form.addParagraphTextItem().setTitle('Comments / Suggestions (Optional)');

  Logger.log('ISO 25010 share link: ' + form.getPublishedUrl());
  Logger.log('ISO 25010 edit link: ' + form.getEditUrl());
}
