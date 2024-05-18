const modal = document.querySelectorAll(".modal");
const openModal = document.querySelectorAll(".openBtn");
const closeModal = document.querySelectorAll(".closeBtn");

openModal.forEach((btn, index) => {
  btn.addEventListener("click", () => {
    modal[index].showModal();
  });
});

closeModal.forEach((btn, i) => {
  btn.addEventListener("click", () => {
    modal[i].close();
  });
});

const showTransactionDetails = async (
  amount,
  source = null,
  category = null,
  description,
  date
) => {
  const transactionDetails = document.getElementById("transaction-details");
  transactionDetails.showModal();
};
