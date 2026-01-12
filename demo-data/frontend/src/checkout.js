const POLL_INTERVAL_MS = 5000;

export function createCheckout({ api, invoiceId, onStatus, wait = (ms) => new Promise((r) => setTimeout(r, ms)) }) {
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
      const { status, body } = await api.payInvoice(invoiceId);
      if (status >= 500) {
        // Retry once on a gateway error so a blip doesn't fail the payment.
        const retry = await api.payInvoice(invoiceId);
        if (retry.status >= 400) return onStatus("failed");
        return watch();
      }
      if (status >= 400) return onStatus(body?.detail ?? "failed");
      return watch();
    },
  };
}
