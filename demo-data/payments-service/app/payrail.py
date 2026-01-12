"""Thin client for the PayRail payment gateway."""
from dataclasses import dataclass

import httpx


class GatewayTimeout(Exception):
    """PayRail did not answer in time. The charge may or may not have gone through."""


@dataclass
class ChargeResult:
    payment_id: str
    status: str  # pending | succeeded | failed


class PayRailClient:
    def __init__(self, base_url: str, api_key: str, http: httpx.Client | None = None):
        self._http = http or httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )

    def charge(self, *, amount_cents: int, currency: str, reference: str, method: str) -> ChargeResult:
        return self._parse(
            self._request(
                "POST",
                "/payments",
                json={
                    "amount": amount_cents,
                    "currency": currency,
                    "reference": reference,
                    "method": method,
                },
            )
        )

    def get_payment(self, payment_id: str) -> ChargeResult:
        return self._parse(self._request("GET", f"/payments/{payment_id}"))

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise GatewayTimeout(path) from exc
        if response.status_code == 504:
            raise GatewayTimeout(path)
        response.raise_for_status()
        return response

    @staticmethod
    def _parse(response: httpx.Response) -> ChargeResult:
        body = response.json()
        return ChargeResult(payment_id=body["id"], status=body["status"])
