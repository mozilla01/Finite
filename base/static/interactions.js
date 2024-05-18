"use strict";
import getCookie from "../../static/js/csrf.js";
import showFlash from "../../static/js/showFlash.js";

// Create category
document
  .getElementById("createCategoryForm")
  .addEventListener("submit", async (e) => {
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
      const data = await response.json();
      showFlash(1, "Category created successfully");
      document.getElementById("categorySelectExpenseForm").innerHTML = data;
    } catch (error) {
      showFlash(0, error.message);
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
      const data = await response.json();
      console.log(data);
      showFlash(1, "Source added successfully");
      document.getElementById("sourceSelectIncomeForm").innerHTML = data;
    } catch (error) {
      showFlash(0, error.message);
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
    try {
      const response = await fetch("/add-transaction", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({
          amount: amount,
          category: category,
          description: description,
          date: date,
          type: "E",
          user: user,
        }),
      });
      const data = await response.json();
      console.log(data);
      document.getElementById("expense-table").innerHTML += data;
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
    try {
      const response = await fetch("/add-transaction", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({
          amount: amount,
          source: source,
          description: description,
          date: date,
          type: "I",
          user: user,
        }),
      });
      const data = await response.json();
      console.log(data);
      document.getElementById("income-table").innerHTML += data;
    } catch (error) {
      console.error(error);
    }
  });
