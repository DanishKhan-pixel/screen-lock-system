# Screen Lock System (Aegis)

A Django web application that demonstrates a production-oriented **Screen Lock**
feature for authenticated user sessions.

> **Screen Lock = temporarily block application access, without logging the user out.**
> Like locking your phone: you stay signed in, but nobody can use the app until
> the correct 6-digit PIN is entered.

The app itself ("Aegis") is a small security-operations console (dashboard,
incidents, directory) that exists to show the Screen Lock working inside a
realistic, multi-page authenticated app.

---

## What it does

- Log in with normal username + password.
- Press **Lock workspace** on any page → a dedicated **Lock Screen** appears.
- Enter your **6-digit PIN**:
  - Correct → return to the exact page you were on (query string preserved).
  - 3 wrong in a row → full logout, back to the login page.
- The lock is enforced **server-side** — refresh, Back button, direct URLs, and
  API calls cannot bypass it.

Authentication and lock are two separate states:

```
Authentication  →  "who are you?"                 (login / logout)
Screen Lock     →  "can you use the app now?"      (locked / unlocked)
```

While locked, `request.user.is_authenticated` stays **True**.

Full feature/design write-up: [`docs/SCREEN_LOCK.md`](docs/SCREEN_LOCK.md).

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.12 |
| Framework | Django 6.1 (MVT) |
| Database | PostgreSQL |
| DB driver | psycopg 3 |
| Auth | Django's built-in auth + sessions |

---

## Project layout

```
screen-lock-system/
├── config/            # project settings, root urls, wsgi/asgi
├── accounts/          # auth + Screen Lock (models, forms, services, middleware, views)
├── pages/             # the "Aegis" app pages (dashboard, reports, users, profile, settings)
├── templates/         # base layout + page/lock/login templates
├── static/css/        # app.css (console UI)
├── docs/SCREEN_LOCK.md# feature documentation
├── .env               # local secrets/config (git-ignored)
├── .env.example       # template to copy
└── requirements.txt
```

Key Screen Lock files live in `accounts/`:

| File | Responsibility |
|------|----------------|
| `models.py` | `UserProfile.pin_hash` + `set_pin()` / `check_pin()` |
| `forms.py` | `ScreenLockForm` — validates exactly 6 numeric digits |
| `services.py` | Session helpers: lock, unlock, count failures, safe return URL |
| `middleware.py` | `ScreenLockMiddleware` — blocks protected routes while locked |
| `views.py` | `activate_lock`, `lock_screen` (unlock + failed attempts) |

---

## Setup

### 1. Prerequisites

- Python 3.12+
- PostgreSQL 14+ running locally (`psql` available)

### 2. Get the code and create a virtualenv

```bash
cd screen-lock-system
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the PostgreSQL database and user

Open a superuser `psql` session and run:

```sql
CREATE ROLE root WITH LOGIN PASSWORD 'root' CREATEDB;
CREATE DATABASE "lock-secreen" OWNER root;
```

> The database name is `lock-secreen` (note the spelling). Because of the
> hyphen, connecting from `psql` needs quotes: `\c "lock-secreen"`.
> `CREATEDB` is required so Django can build its test database.

### 4. Configure environment variables

Copy the example file and adjust if needed:

```bash
cp .env.example .env
```

`.env` (already matches the DB created above):

```ini
POSTGRES_DB=lock-secreen
POSTGRES_USER=root
POSTGRES_PASSWORD=root
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
```

`config/settings.py` loads `.env` automatically at startup (no extra package).
Real shell environment variables override `.env` values.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Load demo data (optional but recommended)

```bash
python manage.py seed_demo
```

This creates demo users and incident reports. Main user:

| Field | Value |
|-------|-------|
| Username | `danish` |
| Password | `password123` |
| Screen Lock PIN | `123456` |

(Other users: `ahmed`, `fatima`, `usman`, `ayesha`, `hassan` — same password.)

### 7. (Optional) Create your own admin superuser

```bash
python manage.py createsuperuser
```

### 8. Run the server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in.

---

## Try the Screen Lock

1. Log in as `danish`, open `/reports/?status=active`.
2. Click **Lock workspace** → you land on `/lock/`.
3. Type `/dashboard/` in the URL bar → you are bounced back to `/lock/`.
4. Enter a wrong 6-digit PIN twice → still locked.
5. Enter `123456` → back on `/reports/?status=active`, still logged in.
6. Lock again and enter a wrong PIN 3 times → logged out at `/accounts/login/`.

### Setting / changing a PIN

- In the app: **Security** page (settings).
- In admin: edit the user's profile.

---

## Running tests

```bash
python manage.py test
```

57 tests cover locking, PIN validation, unlock + return URL, failed-attempt
logout, counter reset, and every bypass route (refresh, Back, direct URL, API).

Other useful checks:

```bash
python manage.py check                       # system checks
python manage.py makemigrations --check      # no missing migrations
```

---

## Common commands

| Task | Command |
|------|---------|
| Make migrations | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Show migrations | `python manage.py showmigrations` |
| Seed demo data | `python manage.py seed_demo` |
| Open DB shell | `python manage.py dbshell` |
| Run server | `python manage.py runserver` |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `database "lock-screen" does not exist` | Name is `lock-secreen`. In psql use `\c "lock-secreen"`. |
| `password authentication failed for user "root"` | Recreate role: `ALTER ROLE root WITH LOGIN PASSWORD 'root';` |
| `permission denied to create database` (tests) | Grant it: `ALTER ROLE root CREATEDB;` |
| Server uses old settings after changes | Stop and restart `runserver`. |
| `psycopg` / driver errors | `pip install -r requirements.txt` inside the activated venv. |
