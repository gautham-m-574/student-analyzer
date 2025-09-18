document.addEventListener("DOMContentLoaded", function () {
  const getStartedBtn = document.getElementById("get-started");

  if (getStartedBtn) {
      getStartedBtn.addEventListener("click", function () {
          window.location.href = "../html/login.html"; // Redirect to login page
      });
  }
});
