import { getAuth } from "https://www.gstatic.com/firebasejs/9.9.1/firebase-auth.js";
import { collection, doc, setDoc, getFirestore, getDoc, FieldValue, updateDoc } from "https://www.gstatic.com/firebasejs/9.9.1/firebase-firestore.js";
import { getStorage, ref, uploadBytes } from "https://www.gstatic.com/firebasejs/9.9.1/firebase-storage.js";

const auth = getAuth();
const db = getFirestore();
const stor = getStorage();
const itemsRef = collection(db, "item-info");
const pksRef = doc(db, "pks", "item-info");

const docSnap = await getDoc(pksRef);
//const increment = db.FieldValue.increment(1);

console.log("in item add");
const addItemBtn = document.querySelector('#btn');
    addItemBtn.addEventListener('click', e => {
    e.preventDefault();

    var file = document.getElementById("photo").files[0];
    const new_name = document.querySelector('#name').value;
    const new_price = document.querySelector('#price').value;
    const new_desc = document.querySelector('#itemDesc').value;

    setDoc(doc(itemsRef, String(docSnap.data().id + 1)), {
        name: String(new_name),
        id: Number(docSnap.data().id + 1),
        price: new_price,
        description: new_desc,
        seller_id: auth.currentUser.uid,
        active: 1
    });
    const imgRef = ref(stor, 'itemImages/' + String(docSnap.data().id + 1));
    uploadBytes(imgRef, file)

    updateDoc(pksRef, "id", Number(docSnap.data().id + 1));
});

console.log("in item add");