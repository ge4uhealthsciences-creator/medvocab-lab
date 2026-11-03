// Firebase web config for GE4u. These values are public by design (Firebase web apps
// ship them to the browser); access is controlled by Authentication + firebase/firestore.rules.
// Fill in from Firebase console → Project settings → Your apps → Web app.
export const firebaseConfig = {
  apiKey: "ADD_FIREBASE_API_KEY",
  authDomain: "medical-english-b8ff5.firebaseapp.com",
  projectId: "medical-english-b8ff5",
  appId: "ADD_FIREBASE_APP_ID",
};
export const firebaseReady = !Object.values(firebaseConfig).some((v) => String(v).startsWith("ADD_"));
