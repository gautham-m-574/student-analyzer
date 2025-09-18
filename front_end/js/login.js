document.getElementById("loginForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  let email = document.getElementById("email").value;
  let password = document.getElementById("password").value;

  let response = await fetch("http://127.0.0.1:5000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
  });

  let result = await response.json();
  alert(result.message);
});
