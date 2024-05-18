export default function showFlash() {
  try {
    document.getElementById("flash").style.top = "44px";
    setTimeout(() => {
      if (document?.getElementById("flash"))
        document.getElementById("flash").style.top = "-112px";
    }, 4000);
  } catch (error) {
    console.error(error);
  }
}
