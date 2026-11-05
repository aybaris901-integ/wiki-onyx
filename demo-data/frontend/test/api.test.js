import assert from "node:assert/strict";
import { test } from "node:test";
import { createApi } from "../src/api.js";

function reply(status, body = {}) {
  return { status, json: async () => body };
}

function setup({ refreshWorks = true } = {}) {
  let token = "expired";
  let refreshes = 0;
  const api = createApi({
    getToken: () => token,
    refresh: async () => {
      refreshes += 1;
      await new Promise((r) => setTimeout(r, 1));
      if (refreshWorks) token = "fresh";
      return refreshWorks;
    },
    fetch: async (_path, options) =>
      options.headers.authorization === "Bearer fresh" ? reply(200, { status: "pending" }) : reply(401),
  });
  return { api, refreshCount: () => refreshes };
}

test("a 401 refreshes and retries once", async () => {
  const { api } = setup();
  const { status } = await api.paymentStatus("inv_1");
  assert.equal(status, 200);
});

test("parallel 401s share a single refresh", async () => {
  const { api, refreshCount } = setup();
  await Promise.all([api.paymentStatus("a"), api.paymentStatus("b"), api.paymentStatus("c")]);
  assert.equal(refreshCount(), 1);
});

test("a failed refresh returns the 401", async () => {
  const { api } = setup({ refreshWorks: false });
  const { status } = await api.paymentStatus("inv_1");
  assert.equal(status, 401);
});
