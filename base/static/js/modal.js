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
