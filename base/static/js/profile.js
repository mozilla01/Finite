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
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }
    return cookieValue;
}

let updates = { categories: {} };
document.querySelectorAll("input").forEach((input) => {
    input.addEventListener("input", (e) => {
        if ("mainBal" in e.target.dataset) {
            updates.mainBal = e.target.value;
        } else if (input.type == "file") {
            const file = document.querySelector("#pfp-inp");
            let image = file.files[0];
            const pfpImage = document.getElementById("pfp");
            file.onchange = () => {
                image = file.files[0];
                if (image) {
                    pfpImage.src = URL.createObjectURL(image);
                }
            };
        } else {
            updates.categories[e.target.dataset.catId] = e.target.value;
        }
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
    } catch (error) {
        showFlash(0, error.message);
    }
});
