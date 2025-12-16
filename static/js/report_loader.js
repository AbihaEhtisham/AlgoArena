document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("aiLoadingOverlay");
  if (!overlay) return;

  // Show loader immediately
  overlay.style.display = "flex";

  // Fake "agent thinking" delay for impact
  // You can tune 900–1600ms
  setTimeout(() => {
    overlay.style.display = "none";
  }, 1200);
});
