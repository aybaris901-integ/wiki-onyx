# Acme demo data (fictional)

Everything under this folder is made up. Acme, its employees, its customers, its incidents and
PayRail (its payment gateway) are invented as demo content for the Company Brain hackathon project.

| Path | What it is |
|---|---|
| `payments-service/` | Charges invoices through PayRail, tracks status, notifies merchants |
| `auth/` | Login, access tokens, sessions |
| `notifications/` | Customer email receipts |
| `frontend/` | Stub of the invoicing web app |
| `docs/` | Slack threads, meeting notes and handoff documents for upload to Onyx |

## Run the tests

```
cd payments-service   # or auth, notifications
pip install -r requirements.txt
pytest

cd frontend
npm test
```
