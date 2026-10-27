# MedVocab Lab

A lightweight Medical English practice site with flashcards, a searchable word bank, a quick quiz, and a daily micro-lesson.

## Features
- Responsive static website; no database or server required.
- Medical vocabulary includes IPA, Vietnamese meaning, definitions and examples.
- Daily lesson page loads `data/daily-lesson.json`.
- GitHub Actions builds and publishes to GitHub Pages on each push and on a daily schedule.
- With no API key, the lesson generator rotates a curated starter bank at no API cost.
- Optional OpenAI API generation can be enabled with a repository secret; API usage may incur charges.

## Publish
1. Open repository **Settings → Pages**.
2. Choose **GitHub Actions** as the deployment source if it is not selected.
3. Open **Actions → Daily lesson and deploy**. A push to `main` should trigger the workflow automatically.
4. After a successful deployment, find the exact public URL in **Settings → Pages** or the deploy job summary.

The scheduled run is configured for 23:00 UTC (06:00 Vietnam time). GitHub scheduled workflows may be delayed.

## Optional AI generation
1. Create an API key in OpenAI Platform and review billing and usage limits.
2. Add a repository secret named `OPENAI_API_KEY` under **Settings → Secrets and variables → Actions**.
3. Run the workflow manually and inspect the log. If the API request fails, the generator uses the curated fallback bank.

Never put API keys in source files. Do not enable paid API generation unless you accept possible charges.

## Limitations
- This is an educational prototype, not clinical decision support.
- AI-generated medical content must be reviewed by a qualified subject-matter expert before official use.
- No checkout, payment, email delivery, customer analytics, or guaranteed revenue is included.
- GitHub Pages and Actions limits depend on GitHub's current plan and policies.

## GE4u Dental English pilot
- Product overview: [ge4u-dental-english.html](ge4u-dental-english.html)
- Interactive practice tool: [dental-english-practice.html](dental-english-practice.html)
- Dental vocabulary dataset: [data/dental-english-pack.json](data/dental-english-pack.json)
- The web page supports browser Print → Save as PDF.

The pilot contains 30 dental English terms across five topic areas and 10 multiple-choice questions. The product page is a preview only: payment collection and automatic delivery have not been enabled.


## GE4u order intake and private admin deployment

The live GE4u website submits order requests to the Order Intake Apps Script web app. Deployment URLs are managed in Google Apps Script and must match the URLs configured in the website source.

- Order Intake endpoint: https://script.google.com/macros/s/AKfycbwUfx0ac8xLA-C0B8OyTanGwNlM3Cp_LCr4Trsj-QmSBkK93Nh72Qeb98J3s2IH7OB0sQ/exec
- Private Admin Dashboard endpoint: https://script.google.com/macros/s/AKfycbxV51p_aGq-oD9gbBQvMK91P0ZJuYmBl8StH15s0N6rX0pIKRMLqYMJ0d3fHbMgTWBz/exec
- Order notification recipient configured in `google-apps-script/Code.gs`: `ge4u.health.sciences@gmail.com`

### Required Google Apps Script configuration

1. In the **Order Intake** Apps Script project, set Script Property `GE4U_ORDERS_SHEET_ID` to the ID of the private Google Spreadsheet.
2. In the **Admin Dashboard** Apps Script project, set the same `GE4U_ORDERS_SHEET_ID` value. Both projects must point to the same spreadsheet.
3. Ensure the spreadsheet has an `Orders` tab with the header row expected by `google-apps-script/Code.gs`. Run `setupPrivateSheets()` from the Admin project to create missing tabs and headers if appropriate; inspect existing data before changing any headers.
4. Deploy Order Intake as a web app that executes as the owner and is accessible to anyone, since customers submit without signing in. Keep the Admin Dashboard restricted to the authorized administrator; do not make it public.
5. After editing Apps Script source, deploy a new version in that Apps Script project. Updating GitHub does not itself update a deployed Apps Script version.
6. Submit one test request and verify all three outcomes separately: (a) confirmation page/order ID, (b) a new row in the private `Orders` tab, and (c) notification email at `ge4u.health.sciences@gmail.com`. A confirmation page alone does not prove that the Sheet write or email succeeded.

The order endpoint records a purchase request only. It does not verify bank transfers or mean the customer has paid. Verify payment manually before delivering paid material. Do not store credentials, OTPs, or banking login details in order records.


## GE4u 31-day course: student accounts and saved progress

The page `ge4u-31-day-plan.html` is designed to use Firebase Authentication (email/password) and Cloud Firestore to store each learner's study reflections, self-assessment, quiz results and completion status. Records belong to `users/{Firebase UID}/lessons/{discipline-day}`; Firestore Security Rules restrict each account to its own records. Browser localStorage is not the source of truth.

**Setup is required before student login works:**

1. Create/select a Firebase project in the Firebase Console.
2. In **Authentication → Sign-in method**, enable **Email/Password**.
3. In **Firestore Database**, create the database.
4. Publish the rules from `firebase/firestore.rules` in Firestore → Rules.
5. Register a Web App in Firebase project settings and copy its `apiKey`, `authDomain`, `projectId`, and `appId` into the `firebaseConfig` object in `ge4u-31-day-plan.html`, replacing all `ADD_FIREBASE_...` placeholders.
6. Add the deployed website's domain under Firebase Authentication → Settings → Authorized domains.
7. Test account creation, sign-in, reflection save, progress save, sign-out and sign-in again. Confirm data persists in Firestore and one user cannot read another user's records.

Until steps 1–6 are completed, the page intentionally disables account creation/sign-in and does not claim that student data is being saved. Do not put service-account private keys in the website or GitHub. Firebase web-app configuration is client-side; access control must be enforced by Firestore Security Rules.
