# Changelog

All notable changes to **Aegis** are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `note` TextField on `Report` for detailed investigation notes (migration `0003`).
- `phone` field on `UserProfile` for optional contact number (migration `0003`).
- `aegis_tags` template tag library: `severity_icon`, `status_label`, `severity_css`, `initials` filters/tags.
- `clear_locks` management command to force-unlock active DB sessions (`--dry-run` supported).
- `api/me/` JSON endpoint returning the authenticated user's full profile.
- `updated_at` auto-tracking field and `get_absolute_url` on `Report` model.
- `avatar_initials` and `pin_configured` convenience properties on `UserProfile`.
- UTC lock timestamp stored in session; exposed via context processor as `lock_since`.
- `failed_pin_attempts` exposed via context processor for richer lock-screen UI.
- `report_detail` view, URL pattern (`reports/<pk>/`), and template.
- `api/reports/` JSON endpoint returning summary data for all incident reports.

### Changed
- Dashboard and reports-list tables now link report titles to the detail page.
- Reports list uses `status_label` and `severity_icon` from `aegis_tags`.
- User directory cards show avatar initials circle and phone number.
- `update_profile` view now saves the `phone` field.
- `MAX_FAILED_ATTEMPTS` is now configurable via `SCREEN_LOCK_MAX_ATTEMPTS` env var in Django settings.
- `screen_lock` context processor conditionally includes `lock_since` and `failed_pin_attempts` when locked.
- `seed_demo` command populates the new `note` field with realistic investigation text.
- `.env.example` updated: section headers, `POSTGRES_DB` typo fixed, `SCREEN_LOCK_MAX_ATTEMPTS` documented.

---

## [0.1.0] – 2026-09-05

### Added
- Initial Django project scaffold with PostgreSQL backend.
- `UserProfile` model with 6-digit screen-lock PIN (hashed via `make_password`).
- `ScreenLockMiddleware` redirecting locked sessions to the lock screen.
- Lock / unlock session service layer with configurable max failed attempts.
- Dashboard, reports list, user directory, profile, and security settings pages.
- Admin integration with inline PIN management.
- Demo data seed command (`seed_demo`).
