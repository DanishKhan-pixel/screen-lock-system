# Screen Lock & User Session Management — Assessment Report

## Summary

Implemented a production-oriented **Screen Lock** feature in a Django web app.
An authenticated user can lock the application from any page, unlock it with a
6-digit PIN, and is logged out after 3 consecutive wrong PINs. The lock is
enforced **server-side**, so it cannot be bypassed by refresh, browser
navigation, direct URLs, or API calls.

**Stack:** Python 3.12 · Django 6.1 (MVT) · PostgreSQL · Django auth + sessions.

## Core idea

Authentication and lock are kept separate:

- **Authentication** = who you are (login / logout).
- **Screen Lock** = whether you can use the app right now (locked / unlocked).

While locked, the user stays authenticated (`request.user.is_authenticated` is
still `True`); only access to protected pages is blocked.

## How it works

1. User clicks **Lock workspace** → current page URL is saved, session flagged locked.
2. A dedicated **Lock Screen** shows one 6-digit PIN field.
3. Correct PIN → unlock and redirect back to the original page (query string kept).
4. Wrong PIN → counter increments; on the 3rd wrong attempt the session is
   invalidated (Django `logout()`) and the user is sent to the login page.
5. A correct PIN before the 3rd attempt resets the counter.

State lives in the Django **session** (server-side), never in the browser:

| Session key | Purpose |
|-------------|---------|
| `screen_lock_locked` | Locked flag |
| `screen_lock_return_url` | Safe URL to return to after unlock |
| `screen_lock_failed_attempts` | Consecutive wrong-PIN counter (max 3) |

## Security measures

- **PIN hashed** with Django's password hashers (`make_password` / `check_password`) — never stored or shown in plain text, templates, JS, logs, or API responses.
- **Server-side validation**: exactly 6 numeric digits (HTML attributes are only hints).
- **Central middleware** (`ScreenLockMiddleware`) blocks every protected route while locked; only the lock/unlock, login, logout, and static/media routes are allowed.
- **API/AJAX** requests get `403` instead of data while locked.
- **No cache**: authenticated responses send `Cache-Control: no-store`, so Back button cannot reveal a cached page.
- **Safe redirect**: return URL validated with `url_has_allowed_host_and_scheme` (no open redirect).
- **Generic errors**: no leak of whether a PIN is configured.

### Bypass attempts and why they fail

| Attempt | Result |
|---------|--------|
| Refresh the lock page | Still locked (session) |
| Browser Back to a protected page | Redirected to lock screen |
| Type a protected URL directly | Redirected to lock screen |
| Call an authenticated API | `403 Screen is locked` |
| Edit frontend/JS state | Ignored — server owns the state |
| Open another tab | Same session → still locked |

## Requirement coverage

**Part A — Screen Lock:** lock from any page, dedicated lock screen, single
6-digit numeric field, validate against configured PIN, correct PIN returns to
the original page, no full re-login required. ✔

**Part B — Failed attempts:** track per-session failures, logout + redirect to
login after 3 wrong, reset counter on a correct PIN, standard login required
afterwards. ✔

## Testing

**57 automated tests** pass, covering:

- Locking from every authenticated page and session persistence
- PIN validation (5/7 digits, letters, symbols, empty all rejected)
- Successful unlock + original URL and query-string restore
- Failed attempts: 1st/2nd stay locked, 3rd logs out; counter reset
- Bypass routes: refresh, Back, direct URL, POST, API/AJAX, admin
- CSRF, session isolation between users, PIN never exposed

```
python manage.py test   →   Ran 57 tests   OK
```

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# create PostgreSQL db "lock-secreen" / user root, then:
python manage.py migrate
python manage.py seed_demo      # demo user: danish / password123 / PIN 123456
python manage.py runserver
```

Full details: `README.md` and `docs/SCREEN_LOCK.md`.
