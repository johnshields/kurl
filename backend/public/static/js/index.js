async function loadApiInfo() {
  try {
    const res = await fetch("/api");
    const data = await res.json();
    if (data.service) {
      document.getElementById("page-title").textContent = data.service;
      document.getElementById("api-name").textContent = data.service;
    }
    if (data.description) {
      document.getElementById("api-description").innerHTML = `<strong>${data.description}</strong>`;
    }
  } catch (err) {
    console.error("Failed to load API info:", err);
  }
}

async function showApiStatus() {
  const out = document.getElementById("api-result");
  const header = document.getElementById("api-header");
  try {
    header.style.display = "block";
    out.textContent = "Loading...";
    out.style.display = "block";
    const res = await fetch("/api");
    out.textContent = JSON.stringify(await res.json(), null, 2);
  } catch (err) {
    out.textContent = "Error: " + err.message;
    out.style.display = "block";
  }
}

document.addEventListener("DOMContentLoaded", loadApiInfo);
