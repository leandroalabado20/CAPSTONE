var SCALE = ['5 - Strongly Agree', '4 - Agree', '3 - Neutral', '2 - Disagree', '1 - Strongly Disagree'];

function addRating(form, label) {
  form.addMultipleChoiceItem().setTitle(label).setChoiceValues(SCALE).setRequired(true);
}

function createTAMForm() {
  var form = FormApp.create('Technology Acceptance Model (TAM) Evaluation Instrument');
  form.setDescription(
    'Web-Based Data-Driven Job Recommendation System with Dashboard for PESO CSJDM\n\n' +
    'Dear Respondent, please evaluate the system you just used by rating each statement below based on your honest experience and observation. ' +
    'Your responses will be treated with strict confidentiality and used solely for academic research purposes.\n\n' +
    'Rating Scale: 5 - Strongly Agree | 4 - Agree | 3 - Neutral | 2 - Disagree | 1 - Strongly Disagree'
  );

  form.addTextItem().setTitle('Capstone Project Title').setRequired(true);
  form.addTextItem().setTitle('Researchers/Proponents').setRequired(true);

  // Respondent Profile
  form.addSectionHeaderItem().setTitle('Respondent Profile');
  form.addTextItem().setTitle('Age').setRequired(true);
  form.addMultipleChoiceItem().setTitle('Sex').setChoiceValues(['Male', 'Female', 'Prefer not to say']).setRequired(true);
  form.addTextItem().setTitle('Year Level / Position').setRequired(true);
  form.addTextItem().setTitle('Frequency of System Use').setRequired(true);

  // A. Perceived Usefulness
  form.addSectionHeaderItem().setTitle('A. Perceived Usefulness (PU)\nThis measures whether the user believes the system helps them accomplish tasks effectively.');
  addRating(form, 'PU1. Using this system improves my performance in accomplishing job referral and applicant management tasks.');
  addRating(form, 'PU2. Using this system increases my productivity when working with job applicants and vacancies.');
  addRating(form, 'PU3. This system helps me identify suitable job category matches for applicants more quickly.');
  addRating(form, 'PU4. This system is useful for generating job category recommendations for applicants.');
  addRating(form, 'PU5. Overall, I find this system beneficial for job referral and employment matching purposes.');

  // B. Perceived Ease of Use
  form.addSectionHeaderItem().setTitle('B. Perceived Ease of Use (PEOU)\nThis measures whether the user finds the system simple and easy to operate.');
  addRating(form, 'PEOU1. Learning to use this system\'s features, such as registering applicants and generating job recommendations, was easy for me.');
  addRating(form, 'PEOU2. I find it easy to navigate the system and perform tasks such as managing applicant records or viewing job recommendations.');
  addRating(form, 'PEOU3. My interaction with the system, including its forms, navigation, and dashboard, is clear and understandable.');
  addRating(form, 'PEOU4. I find the system easy to use overall.');
  addRating(form, 'PEOU5. The system\'s interface (buttons, menus, navigation) is user-friendly.');

  // C. Behavioral Intention to Use
  form.addSectionHeaderItem().setTitle('C. Behavioral Intention to Use (BI)\nThis measures whether the user intends to continue using the system going forward.');
  addRating(form, 'BI1. I intend to use this system regularly if it is made available.');
  addRating(form, 'BI2. I would recommend this system to others who work with job applicants and employment referrals.');
  addRating(form, 'BI3. I plan to use this system regularly for applicant management and job matching if it becomes available.');
  addRating(form, 'BI4. Given the chance, I would prefer using this system over manual methods for managing applicants and generating job recommendations.');

  // D. Open-Ended Questions
  form.addSectionHeaderItem().setTitle('D. Open-Ended Questions (Optional)');
  form.addParagraphTextItem().setTitle('1. What did you like most about the system?');
  form.addParagraphTextItem().setTitle('2. What improvements would you suggest?');

  Logger.log('TAM share link: ' + form.getPublishedUrl());
  Logger.log('TAM edit link: ' + form.getEditUrl());
}
