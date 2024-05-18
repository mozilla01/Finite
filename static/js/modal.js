const modal = document.querySelectorAll(".modal");
const openModal = document.querySelectorAll(".openBtn");
const closeModal = document.querySelectorAll(".closeBtn");
const del = document.querySelectorAll(".del-btn");
const confirmBtn = document.querySelectorAll(".confirm-btn");

openModal.forEach((btn, index) => {
  btn.addEventListener("click", (e) => {
    modal[index].showModal();
  });
});

closeModal.forEach((btn, i) => {
  btn.addEventListener("click", () => {
    modal[i].close();
  });
});

del.forEach((btn, i) => {
  btn.addEventListener("click", async () => {
    confirmBtn[i].classList.toggle("hidden");
  });
});

const showTransactionDetails = async (
  id,
  amount,
  source,
  category,
  description,
  date,
) => {
  const transactionDetails = document.getElementById("transaction-details");
  transactionDetails.showModal();
  document.querySelectorAll(".del-id").forEach((inp) => {
    inp.value = id;
  });
  document.getElementById("transacAmount").value = amount;
  if (document.getElementById("transacSource"))
    document.getElementById("transacSource").value = source;
  if (document.getElementById("transacCategory"))
    document.getElementById("transacCategory").value = category;
  document.getElementById("transacDescription").value = description;
  document.getElementById("transacDate").value = date;
};
