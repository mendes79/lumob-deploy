document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  toggle.addEventListener("click", function () {
    var isDark = document.documentElement.classList.toggle("dark");
    localStorage.setItem("lumob-theme", isDark ? "dark" : "light");
  });
});
