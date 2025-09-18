document.addEventListener("DOMContentLoaded", function () {
  const getStartedBtn = document.getElementById("log-out-btn");

  if (getStartedBtn) {
      getStartedBtn.addEventListener("click", function () {
          window.location.href = "../html/login.html"; 
      });
  }
});