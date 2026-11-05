# Engineering onboarding guide

**Last updated:** 2026-03-09 by Alex Chen

Welcome to Acme! We build invoicing and payments software for B2B companies.

## Your first day

1. Get added to GitHub and the password vault. Ask Sam.
2. Join Slack: #eng-payments, #infra, #incidents.
3. Clone the repo and run the tests for the service you'll work on.

## Services

| Service | What it does | Ask |
|---|---|---|
| payments-service | Charges invoices through PayRail | Alex |
| auth | Login, sessions (Redis), JWT access tokens (60 minutes) | Maria |
| notifications | Email receipts | Maria |
| frontend | Invoicing web app | Priya |

## Running tests

```
cd payments-service
pip install -r requirements.txt
pytest
```

The frontend uses `npm test`.

## Trying a charge locally

```
curl -X POST localhost:8000/invoices/inv_1/pay -d '{"method": "card"}'
```

## Deploying

TODO: Sam to write this.

## PayRail

TODO: Alex to write up how PayRail behaves and what to watch out for. Ask Alex in the meantime.

## On-call

TODO
