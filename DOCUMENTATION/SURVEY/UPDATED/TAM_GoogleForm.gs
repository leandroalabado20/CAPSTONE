/**
 * Google Apps Script: builds the TAM Evaluation Questionnaire as a Google Form.
 *
 * HOW TO USE
 * 1. Go to https://script.google.com  ->  New project.
 * 2. Delete the default code, paste this whole file.
 * 3. Click Run -> choose createTamForm. Authorize when prompted.
 * 4. Open View -> Logs (or Execution log) to get the form Edit URL and public URL.
 *
 * Source: DOCUMENTATION/SURVEY/UPDATED/TAM_Questionnaire_PESO.docx
 */

var SYSTEM_TITLE = "A Web-Based Data-Driven Job Recommendation System with Dashboard for PESO CSJDM";
var SYSTEM_LINK  = "https://pesosystem.pythonanywhere.com";

// Likert column labels (carry the 5..1 scoring for the weighted mean).
var SCALE = [
  "Strongly Agree (5)",
  "Agree (4)",
  "Neutral (3)",
  "Disagree (2)",
  "Strongly Disagree (1)"
];

var SECTIONS = [
  {
    title: "A. Perceived Usefulness (PU)",
    desc:  "This measures whether the user believes the system helps them accomplish tasks effectively.",
    rows: [
      "PU1. Using this system improves my performance in accomplishing job referral and job-matching tasks.",
      "PU2. Using this system increases my productivity when finding and applying to suitable job vacancies.",
      "PU3. This system helps me identify suitable job category matches for a jobseeker more quickly.",
      "PU4. This system is useful for generating job category recommendations for jobseekers.",
      "PU5. Overall, I find this system beneficial for job referral and employment matching purposes."
    ]
  },
  {
    title: "B. Perceived Ease of Use (PEOU)",
    desc:  "This measures whether the user finds the system simple and easy to operate.",
    rows: [
      "PEOU1. Learning to use this system's features, such as registering, encoding a profile, and generating job recommendations, was easy for me.",
      "PEOU2. I find it easy to navigate the system and perform tasks such as encoding a profile or viewing job recommendations.",
      "PEOU3. My interaction with the system, including its forms, navigation, and dashboard, is clear and understandable.",
      "PEOU4. I find the system easy to use overall.",
      "PEOU5. The system's interface (buttons, menus, navigation) is user-friendly."
    ]
  },
  {
    title: "C. Behavioral Intention to Use (BI)",
    desc:  "This measures whether the user intends to continue using the system going forward.",
    rows: [
      "BI1. I intend to use this system regularly if it is made available.",
      "BI2. I would recommend this system to others who are looking for a job or who use PESO services.",
      "BI3. I plan to use this system regularly for job searching and referral if it becomes available.",
      "BI4. Given the chance, I would prefer using this system over manual or walk-in methods for job referral and job searching."
    ]
  }
];

function createTamForm() {
  var form = FormApp.create("Technology Acceptance Model (TAM) Evaluation Questionnaire");

  form.setDescription(
    "Capstone Project: " + SYSTEM_TITLE + "\n\n" +
    "INSTRUCTIONS\n" +
    "1. Before answering, please try the system first here: " + SYSTEM_LINK + "\n" +
    "2. Explore the main features (create an account, encode a profile, view job recommendations, and generate a referral).\n" +
    "3. Then rate each statement based on your honest experience using the system.\n\n" +
    "Rating scale: 5 - Strongly Agree, 4 - Agree, 3 - Neutral, 2 - Disagree, 1 - Strongly Disagree."
  );

  form.setCollectEmail(false);
  form.setProgressBar(true);

  // ----- Respondent Profile -----
  form.addSectionHeaderItem()
      .setTitle("Respondent Profile");

  form.addTextItem()
      .setTitle("Age")
      .setRequired(true);

  form.addMultipleChoiceItem()
      .setTitle("Sex")
      .setChoiceValues(["Male", "Female"])
      .showOtherOption(true)
      .setRequired(true);

  form.addMultipleChoiceItem()
      .setTitle("Role")
      .setChoiceValues(["Jobseeker", "Employer", "PESO staff", "General user"])
      .setRequired(true);

  form.addMultipleChoiceItem()
      .setTitle("Frequency of Use")
      .setChoiceValues(["First time", "Rarely", "Sometimes", "Often", "Daily"])
      .setRequired(true);

  // ----- TAM constructs as grids -----
  for (var i = 0; i < SECTIONS.length; i++) {
    var s = SECTIONS[i];
    form.addSectionHeaderItem()
        .setTitle(s.title)
        .setHelpText(s.desc);

    form.addGridItem()
        .setTitle(s.title)
        .setHelpText(s.desc)
        .setRows(s.rows)
        .setColumns(SCALE)
        .setRequired(true);
  }

  // ----- Open-ended -----
  form.addSectionHeaderItem()
      .setTitle("D. Open-Ended Questions (Optional)");

  form.addParagraphTextItem()
      .setTitle("1. What did you like most about the system?")
      .setRequired(false);

  form.addParagraphTextItem()
      .setTitle("2. What improvements would you suggest?")
      .setRequired(false);

  Logger.log("Form created.");
  Logger.log("Edit URL:   " + form.getEditUrl());
  Logger.log("Public URL: " + form.getPublishedUrl());
}
