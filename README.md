# repay_sync

A small Django 5 + DRF service exploring the data model and workflow behind loan-repayment collection — the operational layer collection officers and supervisors actually use.

## What it covers

- **Customers** — basic profile + assignment to a collection officer
- **Interactions** — every call or field visit logged with a typed *disposition* (`PROMISE_TO_PAY`, `REFUSED_TO_PAY`, `PARTIAL_PAYMENT`, `FULL_PAYMENT`, `NOT_REACHABLE`, `WRONG_NUMBER`, `CALL_BACK`, `OTHER`) and a `next_call_date` follow-up
- **Users** — role-aware users (`COLLECTION_OFFICER`, supervisors) with JWT auth via `djangorestframework-simplejwt`
- **Logger** — separate `logger` app capturing user actions and API audit trail (toggle via `LOGGING_DB_ENABLED`)
- **MPTT** — hierarchical relationships for reporting structures

## Stack

Django 5.2 · DRF · SimpleJWT · django-mptt · MySQL (`mysqlclient`) · python-dotenv

## Layout

```
repay_sync/        Django project settings + URL conf (JWT token endpoints)
users/             Custom User model, roles, auth views
customers/         Customer model + officer assignment
interactions/      Interaction model with disposition enum
logger/            user_logger + api_logger (audit trail)
```

## Run locally

```bash
cp sample.env .env                  # fill in DB_NAME / DB_USER / DB_PASSWORD / SECRET_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

API root: `http://localhost:8000/api/` (JWT obtain at `/api/token/`, refresh at `/api/token/refresh/`).

## Status

Personal exploration repo — the production version of this domain lives in private work systems.
