import getCookie from "../../static/js/csrf.js";
import showFlash from "../../static/js/showFlash.js";

let updates = { categories: {} };
console.log("Hello from profile.js");
document.querySelectorAll("input").forEach((input) => {
  input.addEventListener("input", (e) => {
    console.log(e);
    if ("mainBal" in e.target.dataset) {
      updates.mainBal = e.target.value;
    } else {
      updates.categories[e.target.dataset.catId] = e.target.value;
    }
    console.log(updates);
  });
});

document.getElementById("save").addEventListener("click", async () => {
  const csrftoken = getCookie("csrftoken");
  try {
    const response = await fetch("/update-profile", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify(updates),
    });
    const data = await response.json();
    showFlash(1, "Profile updated successfully");
    console.log(data);
  } catch (error) {
    showFlash(0, error.message);
  }
});
