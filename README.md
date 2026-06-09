# repay_sync

[![test](https://github.com/prajwalmahajan101/repay_sync/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/prajwalmahajan101/repay_sync/actions/workflows/test.yml)

> **Scope: exploration repo.** This sketches the data model and workflow for loan-repayment collection — typed dispositions, audit log, RBAC — at a level useful to *show the shape* of the problem. The production version of this domain lives in private work systems at Optimo Capitals. Don't fork this for a real service; treat it as an annotated reference.

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

Personal exploration repo — the production version of this domain lives in private work systems at Optimo Capitals. No release tag is cut because there is no installable artifact to version; the repo is a frozen-in-time annotated reference, not a starter.

### Scoped-down CI

CI runs `python manage.py check` only — settings + imports + URL conf. The four per-app `tests.py` files are not run because a pre-existing migration-ordering bug (MySQL error 1824, `users_user` referenced before defined) breaks the migrate step. Fixing the FK order is queued, but until it lands, the green badge means "settings parse," not "tests pass."

### Won't ship as a starter

If you want a real Django/DRF starter for a production service, use [`django_boilerplate`](https://github.com/prajwalmahajan101/django_boilerplate) instead — that one is CI-gated, tagged at [`v0.1.0`](https://github.com/prajwalmahajan101/django_boilerplate/releases/tag/v0.1.0), and shipped with a resilience layer, RBAC, JWT, and Postgres rather than the MySQL + minimal-auth setup here.
