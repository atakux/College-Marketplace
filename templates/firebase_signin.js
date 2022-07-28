import { getAuth, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/9.9.1/firebase-auth.js";


const auth = getAuth();


console.log("in sign in");

const loginBtn = document.querySelector('#btn');
    loginBtn.addEventListener('click', e => {
    e.preventDefault();

    const email = document.querySelector('#email').value;
    const password = document.querySelector('#password').value;

    signInWithEmailAndPassword(auth, email, password)
    .then(cred => {
      console.log('Logged in user!');
      window.location.href = '/signup.html';
    })
    .catch(error => {
      console.log(error.message);
    })
});

console.log("in sign in");