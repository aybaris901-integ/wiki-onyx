import assert from "node:assert/strict";
import { test } from "node:test";
import { createCheckout } from "../src/checkout.js";

function memoryStorage() {
  const items = new Map();
  return {
    getItem: (k) => items.get(k) ?? null,
    setItem: (k, v) => items.set(k, v),
    removeItem: (k) => items.delete(k),
  };
}

function setup(payResponses, statuses = ["succeeded"]) {
  const keysSent = [];
  const seen = [];
  let n = 0;
  const api = {
    payInvoice: async (_id, key) => {
      keysSent.push(key);
      return payResponses.shift();
    },
    paymentStatus: async () => ({ status: 200, body: { status: statuses.shift() } }),
  };
  const checkout = createCheckout({
    api,
    invoiceId: "inv_1",
    onStatus: (s) => seen.push(s),
    storage: memoryStorage(),
    newKey: () => `key_${++n}`,
    wait: async () => {},
  });
  return { checkout, keysSent, seen };
}

const OK = { status: 200, body: { status: "pending" } };

test("watches status until the payment settles", async () => {
  const { checkout, seen } = setup([OK], ["pending", "succeeded"]);
  await checkout.pay();
  assert.deepEqual(seen, ["pending", "succeeded"]);
});

test("a double click sends one request", async () => {
  const { checkout, keysSent } = setup([OK]);
  await Promise.all([checkout.pay(), checkout.pay()]);
  assert.equal(keysSent.length, 1);
});

test("a retry after a gateway error reuses the same key", async () => {
  const { checkout, keysSent } = setup([{ status: 504, body: null }, OK]);
  await checkout.pay();
  await checkout.pay();
  assert.deepEqual(keysSent, ["key_1", "key_1"]);
});

test("a decline starts a new attempt with a new key", async () => {
  const { checkout, keysSent } = setup([{ status: 402, body: { status: "failed" } }, OK]);
  await checkout.pay();
  await checkout.pay();
  assert.deepEqual(keysSent, ["key_1", "key_2"]);
});

test("unknown outcome tells the customer not to pay again and keeps the key", async () => {
  const { checkout, keysSent, seen } = setup([{ status: 409, body: { detail: "in progress" } }, OK]);
  await checkout.pay();
  await checkout.pay();
  assert.match(seen[0], /don't pay again/);
  assert.deepEqual(keysSent, ["key_1", "key_1"]);
});
