import { collection, doc, setDoc, getFirestore, getDoc, FieldValue } from "https://www.gstatic.com/firebasejs/9.9.1/firebase-firestore.js";

const db = getFirestore();
const itemsRef = collection(db, "item-info");
const pksRef = doc(db, "pks", "item-info");
const docSnap = await getDoc(pksRef);
const increment = FieldValue.increment(1);

console.log("in item add");
const addItemBtn = document.querySelector('#btn');
    addItemBtn.addEventListener('click', e => {
    e.preventDefault();

    const new_name = document.querySelector('#name').value;
    const new_price = document.querySelector('#price').value;
    const new_desc = document.querySelector('#itemDesc').value;

    setDoc(doc(itemsRef, Number(docSnap.data().id)), {
        name: String(new_name),
        id: Number(docSnap.data().id),
        price: new_price,
        description: new_desc,
        seller_id: auth.currentUser.uid,
        active: 1
    });

    pksRef.update({ id: increment});
});

console.log("in item add");