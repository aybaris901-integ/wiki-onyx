export function createApi({ fetch, getToken }) {
  async function request(path, options = {}) {
    const response = await fetch(path, {
      ...options,
      headers: { "content-type": "application/json", authorization: `Bearer ${getToken()}`, ...options.headers },
    });
    const body = await response.json().catch(() => null);
    return { status: response.status, body };
  }

  return {
    payInvoice: (invoiceId) =>
      request(`/api/invoices/${invoiceId}/pay`, { method: "POST", body: JSON.stringify({ method: "card" }) }),
    paymentStatus: (invoiceId) => request(`/api/invoices/${invoiceId}/payment-status`),
  };
}
