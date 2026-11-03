// Firebase web config for GE4u. These values are public by design (Firebase web apps
// ship them to the browser); access is controlled by Authentication + firebase/firestore.rules.
// Fill in from Firebase console → Project settings → Your apps → Web app.
export const firebaseConfig = {
  apiKey: "AIzaSyDHDIM-bipduL9izcy2VQSyoQ9kj64-CdU",
  authDomain: "medical-english-b8ff5.firebaseapp.com",
  projectId: "medical-english-b8ff5",
  storageBucket: "medical-english-b8ff5.firebasestorage.app",
  messagingSenderId: "163209716601",
  appId: "1:163209716601:web:23cd99ea06db32aa4e85a8",
};
export const firebaseReady = !Object.values(firebaseConfig).some((v) => String(v).startsWith("ADD_"));
