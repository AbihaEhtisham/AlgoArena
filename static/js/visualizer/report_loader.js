document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("aiLoadingOverlay");
  if (!overlay) return;

  // show overlay briefly
  overlay.style.display = "flex";

  setTimeout(() => {
    overlay.style.transition = "opacity 220ms ease";
    overlay.style.opacity = "0";
    setTimeout(() => overlay.remove(), 250);
  }, 1100);
});
