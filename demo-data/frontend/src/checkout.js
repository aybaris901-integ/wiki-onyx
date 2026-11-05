const POLL_INTERVAL_MS = 5000;

// One key per payment attempt, kept in sessionStorage so that a double click, a retry or a page
// reload all reuse it. The server then charges at most once. We only start a new attempt after an
// answer that definitely means "not charged"; after a 5xx or a network error we don't know, so the
// key must be kept. See PR #5 and INC-2026-007.
function attemptKeys(storage, invoiceId, newKey) {
  const name = `pay-attempt:${invoiceId}`;
  return {
    current() {
      let key = storage.getItem(name);
      if (!key) {
        key = newKey();
        storage.setItem(name, key);
      }
      return key;
    },
    finish() {
      storage.removeItem(name);
    },
  };
}

export function createCheckout({
  api,
  invoiceId,
  onStatus,
  storage = sessionStorage,
  newKey = () => crypto.randomUUID(),
  wait = (ms) => new Promise((r) => setTimeout(r, ms)),
}) {
  const keys = attemptKeys(storage, invoiceId, newKey);
  let submitting = false;

  async function watch() {
    for (;;) {
      const { body } = await api.paymentStatus(invoiceId);
      onStatus(body?.status ?? "unknown");
      if (body?.status !== "pending") return body?.status;
      await wait(POLL_INTERVAL_MS);
    }
  }

  return {
    async pay() {
      if (submitting) return;
      submitting = true;
      try {
        const { status, body } = await api.payInvoice(invoiceId, keys.current());
        if (status === 402) {
          keys.finish();
          return onStatus("declined");
        }
        if (status === 409 && body?.detail !== "invoice already paid") {
          return onStatus("Your payment is still being checked. Please don't pay again yet.");
        }
        if (status >= 500) return onStatus("We couldn't confirm your payment. Try again to check on it.");
        if (status >= 400) return onStatus(body?.detail ?? "failed");
        keys.finish();
        return await watch();
      } finally {
        submitting = false;
      }
    },
  };
}
