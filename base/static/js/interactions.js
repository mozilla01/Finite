"use strict";

function showFlash(status, message) {
  const flash = document?.getElementById("flash");
  flash.style.backgroundColor = status ? "green" : "red";
  flash.innerHTML = message;
  try {
    flash.style.top = "70px";
    setTimeout(() => {
      if (flash) flash.style.top = "-7rem";
    }, 4000);
  } catch (error) {
    console.error(error);
  }
}
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

function nodeScriptReplace(node) {
    if (nodeScriptIs(node) === true ) {
        node.parentNode.replaceChild(nodeScriptClone(node), node);
    }
    else {
        let i = -1, children = node.childNodes;
        while ( ++i < children.length ) {
            nodeScriptReplace( children[i] );
        }
    }

    return node;
}

function nodeScriptClone(node){
        let script  = document.createElement("script");
        script.text = node.innerHTML;

        let i = -1, attrs = node.attributes, attr;
        while (++i < attrs.length) {                                    
              script.setAttribute((attr = attrs[i]).name, attr.value);
        }
        return script;
}

function nodeScriptIs(node) {
        return node.tagName === 'SCRIPT';
}

const formatDate = (date) => {
    let dd = String(date.getDate()).padStart(2, '0');
    let mm = String(date.getMonth() + 1).padStart(2, '0'); //January is 0!
    let yyyy = date.getFullYear();

    const formattedDate = yyyy + '-' + mm + '-' + dd;

    return formattedDate;
}

const renderGraphs = async () => {
    let today = new Date();
    let oneWeekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    let first_date = document.getElementById("start-date").value;
    let second_date = document.getElementById("end-date").value;
    if (!first_date) {
        const date1 = formatDate(oneWeekAgo);
        first_date = date1;
        document.getElementById("start-date").value = date1;
    }
    if (!second_date) {
        const date2 = formatDate(today);
        second_date = date2;
        document.getElementById("end-date").value = date2;
    }
    const csrftoken = getCookie("csrftoken");
    const response = await fetch("/render-graphs", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({first_date: first_date, second_date: second_date }),
    });
    let data = await response.json();
    console.log(data);
    data = JSON.parse(data);
    const graphsDiv = document.getElementById("graphs");
    graphsDiv.innerHTML = '';
    graphsDiv.innerHTML += '<div>'+data.expense_pie+'</div>'; 
    graphsDiv.innerHTML += '<div>'+data.income_pie+'</div>';
    graphsDiv.innerHTML += '<div>'+data.mixed_bar+'</div>';
    graphsDiv.innerHTML += '<div>'+data.category_budgets+'</div>';
    graphsDiv.innerHTML += '<div>'+data.savings+'</div>';
    document.getElementById('transaction-table').innerHTML = data.table;
    nodeScriptReplace(graphsDiv);
}

window.onload = renderGraphs;

document.getElementById('filter-btn').addEventListener('click', (e) => {
    e.preventDefault();
    showFlash(1, "Filtering data...");
    renderGraphs();
});

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


// Update transaction 
document
  .getElementById("transac-ud-form")
  .addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = document.getElementById("transac-id").value;
      const csrftoken = getCookie("csrftoken");
      const amount = document.getElementById("transacAmount").value;
      const category = document.getElementById("categorySelectExpenseForm").value;
      const source = document.getElementById("transacSource").value;
      const date = document.getElementById("transacDate").value;
      const description = document.getElementById("transacDescription").value;
      const receipt = document.getElementById("transacReceipt").files[0];
      const user = document.getElementById("transacUser").value;

    let formData = new FormData();
    formData.append("amount", amount);
    formData.append("date", date);
    formData.append("description", description);
      if (category) {
    formData.append("type", "E");
    formData.append("category", category);
      }
      if (source) {
    formData.append("type", "I");
    formData.append("source", source);
      }
    if (receipt) {
      formData.append("receipt", receipt);
    }
      formData.append("user", user);

    try {
      const response = await fetch("/update-transaction/"+id, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      });
      if (response.ok) {
        showFlash(1, "Transaction updated successfully");
      } else {
        showFlash(0, "Error updating transaction, please try again.");
      }
      const data = await response.json();
      console.log(data);
        document.getElementById("transaction-details").close();
        renderGraphs();
    } catch (error) {
      console.error(error);
    }
  });



// Create category
document
  .getElementById("createCategoryForm")
  .addEventListener("submit", async (e) => {
    console.log("create category");
    e.preventDefault();
    const csrftoken = getCookie("csrftoken");
    const category = document.getElementById("categoryName").value;
    const user = document.getElementById("categoryUser").value;
    try {
      const response = await fetch("/create-category", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ name: category, user: user }),
      });
      if (response.ok) {
        showFlash(1, "Category created successfully");
      } else {
        showFlash(0, "Category already exists");
      }
      const data = await response.json();
      document.getElementById("categorySelectExpenseForm").innerHTML = data;
        document.getElementById('createCategoryModal').close();
    } catch (error) {
      console.error(error);
    }
  });

// Add source
document
  .getElementById("addSourceForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const csrftoken = getCookie("csrftoken");
    const source = document.getElementById("sourceName").value;
    const user = document.getElementById("sourceUser").value;
    try {
      const response = await fetch("/add-source", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ name: source, user: user }),
      });
      if (response.ok) {
        showFlash(1, "Source added successfully");
      } else {
        showFlash(0, "Source already exists");
      }
      const data = await response.json();
      console.log(data);
      document.getElementById("sourceSelectIncomeForm").innerHTML = data;
        document.getElementById("addSourceModal").close();
    } catch (error) {
      console.error(error);
    }
  });

// Add expense
document
  .getElementById("addExpenseForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const csrftoken = getCookie("csrftoken");
    const amount = document.getElementById("expenseAmount").value;
    const category = document.getElementById("categorySelectExpenseForm").value;
    const date = document.getElementById("expenseDate").value;
    const description = document.getElementById("expenseDescription").value;
    const user = document.getElementById("expenseUser").value;
    const receipt = document.getElementById("expenseReceipt").files[0];

    let formData = new FormData();
    formData.append("amount", amount);
    formData.append("category", category);
    formData.append("date", date);
    formData.append("description", description);
    formData.append("type", "E");
    formData.append("user", user);
    if (receipt) {
      formData.append("receipt", receipt);
    }

    try {
      const response = await fetch("/add-transaction", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      });
      if (response.ok) {
        showFlash(1, "Expense added successfully");
      } else {
        showFlash(0, "Error adding expense, please try again.");
      }
      const data = await response.json();
      console.log(data);
        document.getElementById("addExpenseModal").close();
        renderGraphs();
    } catch (error) {
      console.error(error);
    }
  });

// Add income
document
  .getElementById("addIncomeForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const csrftoken = getCookie("csrftoken");
    const amount = document.getElementById("incomeAmount").value;
    const source = document.getElementById("sourceSelectIncomeForm").value;
    const date = document.getElementById("incomeDate").value;
    const description = document.getElementById("incomeDescription").value;
    const user = document.getElementById("incomeUser").value;

    let formData = new FormData();
    formData.append("amount", amount);
    formData.append("source", source);
    formData.append("date", date);
    formData.append("description", description);
    formData.append("type", "I");
    formData.append("user", user);

    try {
      const response = await fetch("/add-transaction", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      });
      if (response.ok) {
        showFlash(1, "Income added successfully");
      } else {
        showFlash(0, "Error adding income, please try again.");
      }
      const data = await response.json();
      console.log(data);
        document.getElementById("addIncomeModal").close();
        renderGraphs();
    } catch (error) {
      console.error(error);
    }
  });
