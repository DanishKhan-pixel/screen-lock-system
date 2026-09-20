# Screen Lock & User Session Management

## In simple words

**Screen Lock = temporarily block application access, without logging the user out.**

Think of it like locking your phone. You are still "signed in" to the phone,
but nobody can use it until the correct PIN is entered. Your apps, tabs, and
place in the app stay exactly where they were.

In this project:

- The user logs in normally (username + password).
- They can press **Lock workspace** on any page.
- The app shows a **Lock Screen** asking for a **6-digit PIN**.
- Correct PIN → back to the exact page they were on.
- 3 wrong PINs → full logout, must log in again.

Two states are kept **separate**:

```
Authentication  →  "who are you?"        (login / logout)
Screen Lock     →  "can you use the app right now?"  (locked / unlocked)
```

While locked: `request.user.is_authenticated` is still **True**, but every
protected page is blocked. This separation is the core idea.

---

## The flow

```
Logged in on /reports/?status=active
        │
        │  click "Lock workspace"
        ▼
   POST /lock/activate/        → save locked=True + return_url in session
        ▼
   /lock/  (Lock Screen: one PIN field)
        │
        ├── correct PIN ──────► unlock → redirect back to /reports/?status=active
        │
        ├── wrong PIN (1st, 2nd) ► stay locked, show error, count++
        │
        └── wrong PIN (3rd) ─────► logout() → redirect to /accounts/login/
```

---

## Where the state lives (server-side)

All lock state is stored in the **Django session**, never in the browser/JS.
The server is always the source of truth.

Session keys (`accounts/services.py`):

| Key | Meaning |
|-----|---------|
| `screen_lock_locked` | `True` while the workspace is locked |
| `screen_lock_return_url` | Safe internal URL to return to after unlock |
| `screen_lock_failed_attempts` | Consecutive wrong-PIN counter (max 3) |

The 6-digit PIN itself is **never** stored in the session or in plain text.
It is stored as a hash on the user's profile.

---

## The pieces (files)

| File | Responsibility |
|------|----------------|
| `accounts/models.py` | `UserProfile.pin_hash` + `set_pin()` / `check_pin()` (Django password hashing) |
| `accounts/forms.py` | `ScreenLockForm` — validates exactly 6 numeric digits, server-side |
| `accounts/services.py` | Session helpers: lock, unlock, count failures, safe return URL |
| `accounts/views.py` | `activate_lock`, `lock_screen` (unlock + failed-attempt logic) |
| `accounts/middleware.py` | `ScreenLockMiddleware` — blocks every protected route while locked |
| `accounts/urls.py` | `/lock/`, `/lock/activate/` (named URLs) |
| `templates/accounts/lock.html` | The Lock Screen UI (single PIN field) |

---

## How the PIN is handled securely

- Stored as a **hash** (`make_password`), never plain text.
- Checked with `check_password` (constant-time), never `==`.
- Never sent to templates, JS, logs, or API responses.
- Validated **server-side** in `ScreenLockForm`: must be exactly 6 digits.
  HTML `maxlength`/`inputmode` are only hints; the form is the real gate.

```python
# accounts/models.py
def set_pin(self, raw_pin):
    self.pin_hash = make_password(raw_pin)

def check_pin(self, raw_pin):
    if not self.pin_hash:
        return False
    return check_password(raw_pin, self.pin_hash)
```

### Setting a PIN

- Users set/change their PIN on the **Security** (settings) page.
- Admins can set it from the Django admin.
- No configured PIN → unlock always fails safely (never silently bypasses).

---

## How bypassing is prevented

`ScreenLockMiddleware` runs on **every request** after authentication. If the
user is authenticated **and** the session is locked, it blocks the request
unless the target is one of a tiny allow-list.

Allowed while locked:

- `accounts:lock_screen` (`/lock/`)
- `accounts:activate_lock` (`/lock/activate/`)
- `accounts:logout`
- `accounts:login`
- real `/static/` and `/media/` assets

Everything else:

- **HTML request** → redirect to `/lock/`
- **API / AJAX request** (`/api/...`, `X-Requested-With`, JSON `Accept`) → `403 {"detail": "Screen is locked."}`

This single choke-point covers all bypass attempts:

| Attempt | Why it fails |
|---------|--------------|
| Refresh `/lock/` | Session still `locked=True` |
| Browser Back to `/reports/` | Middleware re-checks session → redirect to `/lock/` |
| Type `/dashboard/` directly | Same middleware check |
| Direct API call | Returns 403, not data |
| Edit frontend/JS state | Irrelevant — server owns the state |
| Open in another tab | Same session → still locked |

Authenticated responses also send `Cache-Control: no-store` so the browser
cannot show a cached protected page from history.

Loop safety: the Lock Screen and unlock routes are on the allow-list, so the
lock page never redirects to itself.

---

## Failed attempts & logout

`accounts/views.py` → `lock_screen`:

- Wrong PIN → `record_failed_attempt()` increments the session counter.
- Reaching **3** → `logout()` (Django's own), clear lock state, redirect to login.
- Correct PIN before the 3rd → unlock **and** reset counter to `0`.
- Next time they lock, the counter starts fresh at `0`.

Invalid **format** (e.g. `12345`, `abc`) is a form error and does **not**
count as a failed attempt — only a valid 6-digit-but-wrong PIN counts.

The error message is generic ("The PIN you entered is incorrect") so it never
leaks whether a PIN is configured.

---

## Safe return URL (no open redirect)

Before locking, the current full path (with query string) is saved, but only
after validation with Django's `url_has_allowed_host_and_scheme`. Any external
or malformed URL falls back to the dashboard. So a crafted
`?next=https://evil.com` cannot turn unlock into an open redirect.

---

## Requirement mapping

### Part A — Screen Lock

| # | Requirement | How it's met |
|---|-------------|--------------|
| A1 | Lock from any page | `Lock workspace` button in base layout posts current path to `/lock/activate/` |
| A2 | Dedicated Lock Screen | `templates/accounts/lock.html` at `/lock/` |
| A3 | Single numeric PIN field | One `PasswordInput`, `inputmode="numeric"` |
| A4 | Exactly 6 digits | `ScreenLockForm` server-side validation |
| A5 | Validate against configured PIN | `check_pin()` (hash compare) |
| A6 | Correct PIN → dismiss, regain access, return to original page | `unlock_session()` returns saved safe URL |
| A7 | No full re-login on correct PIN | Session is never destroyed on unlock; only lock flag cleared |

### Part B — Failed attempts & logout

| # | Requirement | How it's met |
|---|-------------|--------------|
| B1 | Track failed attempts for current user | `screen_lock_failed_attempts` in session |
| B2 | 3 wrong → invalidate session, logout, redirect to login | `logout()` + redirect to `accounts:login` |
| B3 | Correct PIN before 3rd resets counter | `unlock_session()` sets counter to `0` |
| B4 | After logout, normal login required | Standard Django `LoginView` |

### Technical considerations

| Consideration | How it's met |
|---------------|--------------|
| Secure PIN handling | Hashed with Django password hashers, never plain text |
| Session-state management | Dedicated session keys, cleared correctly on unlock/logout |
| Bypass prevention | `ScreenLockMiddleware` + `Cache-Control: no-store` |
| Auth/authz state | `@login_required` + middleware auth check |
| Lock vs auth separation | `is_authenticated` stays True while locked |
| Input validation | `ScreenLockForm` + generic error messages |

---

## Try it locally

```bash
# 1. Database comes from .env (PostgreSQL: lock-secreen / root)
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo      # demo users + reports

# 2. Run
.venv/bin/python manage.py runserver

# 3. Sign in
#    user: danish   password: password123   PIN: 123456
```

Manual test:

1. Log in, open `/reports/?status=active`.
2. Click **Lock workspace** → you land on `/lock/`.
3. Try `/dashboard/` in the URL bar → bounced back to `/lock/`.
4. Enter a wrong 6-digit PIN twice → still locked.
5. Enter `123456` → back on `/reports/?status=active`, still logged in.
6. Lock again, enter wrong PIN 3 times → logged out at `/accounts/login/`.

Automated tests: `.venv/bin/python manage.py test` (57 tests cover locking,
PIN validation, unlock, failed attempts, and every bypass route).
