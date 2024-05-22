function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function showFlash(status, message) {
  const flash = document?.getElementById("flash");
  flash.style.backgroundColor = status ? "green" : "red";
  flash.innerHTML = message;
  try {
    flash.style.top = "70px";
    setTimeout(() => {
      if (flash) flash.style.top = "-112px";
    }, 4000);
  } catch (error) {
    console.error(error);
  }
}

const modal = document.querySelectorAll(".modal");
const openModal = document.querySelectorAll(".openBtn");
const closeModal = document.querySelectorAll(".closeBtn");
const del = document.querySelectorAll(".del-btn");
const confirmBtn = document.querySelectorAll(".confirm-btn");
const startingBalance = document.getElementById("starting-balance");
const startingBalanceModal = document.getElementById("setStartingBalance");

startingBalanceModal.addEventListener("cancel", (event) => {
  event.preventDefault();
});

document.getElementById("st-bal-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const response = await fetch("/update-profile", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({
        startBal: document.getElementById("st-bal-val").value,
      }),
    });
    if (response.ok) showFlash(1, "Starting balance updated successfully");
    else showFlash(0, "An error occurred");
  } catch (error) {
    console.error(error);
  } finally {
    startingBalanceModal.close();
    document.querySelector("body").style.overflow = "auto";
  }
});

if (startingBalance.value == "None") {
  startingBalanceModal.showModal();
  document.querySelector("body").style.overflow = "hidden";
}

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
  receipt,
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
  const receiptLink = document.getElementById("expenseReceiptLink");
  if (!receipt) {
    receiptLink.classList.add("hidden");
  } else {
    receiptLink.classList.remove("hidden");
  }
  receiptLink.href = `http://127.0.0.1:8000/media/${receipt}`;
};
