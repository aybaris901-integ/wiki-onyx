// Access tokens last 15 minutes, so a 401 is routine: refresh, then retry the request once.
// Refresh tokens rotate and reuse ends the session, so parallel requests must share one refresh.
// Without this, a page making 3 calls at token expiry logs the user out. See PR #6.
export function createApi({ fetch, getToken, refresh }) {
  let refreshing = null;

  function refreshOnce() {
    refreshing ??= refresh().finally(() => {
      refreshing = null;
    });
    return refreshing;
  }

  async function send(path, options) {
    return fetch(path, {
      ...options,
      headers: { "content-type": "application/json", authorization: `Bearer ${getToken()}`, ...options.headers },
    });
  }

  async function request(path, options = {}) {
    let response = await send(path, options);
    if (response.status === 401 && (await refreshOnce())) {
      response = await send(path, options);
    }
    const body = await response.json().catch(() => null);
    return { status: response.status, body };
  }

  return {
    payInvoice: (invoiceId, idempotencyKey) =>
      request(`/api/invoices/${invoiceId}/pay`, {
        method: "POST",
        headers: { "idempotency-key": idempotencyKey },
        body: JSON.stringify({ method: "card" }),
      }),
    paymentStatus: (invoiceId) => request(`/api/invoices/${invoiceId}/payment-status`),
  };
}
