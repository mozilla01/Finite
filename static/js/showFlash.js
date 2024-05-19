export default function showFlash(status, message) {
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
