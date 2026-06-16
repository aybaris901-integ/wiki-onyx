import { createApi } from "./api.js";
import { createCheckout } from "./checkout.js";

const invoiceId = new URLSearchParams(location.search).get("invoice");
const statusLine = document.querySelector("#status");
document.querySelector("#invoice-id").textContent = invoiceId;

// Resolves to true if we now hold a fresh access token.
async function refresh() {
  const response = await fetch("/api/auth/refresh", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ refresh_token: sessionStorage.getItem("refresh_token") }),
  });
  if (!response.ok) {
    location.assign("/login");
    return false;
  }
  const tokens = await response.json();
  sessionStorage.setItem("access_token", tokens.access_token);
  sessionStorage.setItem("refresh_token", tokens.refresh_token);
  return true;
}

const api = createApi({
  fetch: window.fetch.bind(window),
  getToken: () => sessionStorage.getItem("access_token"),
  refresh,
});
const checkout = createCheckout({ api, invoiceId, onStatus: (status) => (statusLine.textContent = status) });

document.querySelector("#pay").addEventListener("click", () => checkout.pay());
