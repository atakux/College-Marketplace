// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCI3fvdBkSCXLZOql2vxIMyc-p2wsaNTfg",
  authDomain: "college-marketplace-ca5c1.firebaseapp.com",
  projectId: "college-marketplace-ca5c1",
  storageBucket: "college-marketplace-ca5c1.appspot.com",
  messagingSenderId: "1077776867773",
  appId: "1:1077776867773:web:6379918de21574ea0472d4",
  measurementId: "G-JJV31NZ4R9"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);