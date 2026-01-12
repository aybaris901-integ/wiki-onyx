import { createApi } from "./api.js";
import { createCheckout } from "./checkout.js";

const invoiceId = new URLSearchParams(location.search).get("invoice");
const statusLine = document.querySelector("#status");
document.querySelector("#invoice-id").textContent = invoiceId;

const api = createApi({ fetch: window.fetch.bind(window), getToken: () => sessionStorage.getItem("access_token") });
const checkout = createCheckout({ api, invoiceId, onStatus: (status) => (statusLine.textContent = status) });

document.querySelector("#pay").addEventListener("click", () => checkout.pay());
