import assert from "node:assert/strict";
import { test } from "node:test";
import { createCheckout } from "../src/checkout.js";

test("watches status until the payment settles", async () => {
  const statuses = ["pending", "succeeded"];
  const seen = [];
  const api = {
    payInvoice: async () => ({ status: 200, body: { status: "pending" } }),
    paymentStatus: async () => ({ status: 200, body: { status: statuses.shift() } }),
  };
  await createCheckout({ api, invoiceId: "inv_1", onStatus: (s) => seen.push(s), wait: async () => {} }).pay();
  assert.deepEqual(seen, ["pending", "succeeded"]);
});
