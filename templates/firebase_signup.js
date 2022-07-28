import { getAuth, createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/9.9.1/firebase-auth.js";
import { collection, doc, setDoc, getFirestore } from "https://www.gstatic.com/firebasejs/9.9.1/firebase-firestore.js";

const auth = getAuth();
const db = getFirestore();
const usersRef = collection(db, "user-info");

console.log("in sign up");
const signupBtn = document.querySelector('#btn');
    signupBtn.addEventListener('click', e => {
    e.preventDefault();

    const username = document.querySelector("#userName").value;
    const new_email = document.querySelector('#email').value;
    const new_password = document.querySelector('#password').value;
    const zip = document.querySelector('#address').value;

    createUserWithEmailAndPassword(auth, new_email, new_password).then(() => {
    console.log('User signed up!');
    console.log(auth.currentUser.uid)
    setDoc(doc(usersRef, auth.currentUser.uid), {
        email: String(new_email),
        id: auth.currentUser.uid,
        name: username,
        zip_code: zip
    });

  });
});

console.log("in sign up");