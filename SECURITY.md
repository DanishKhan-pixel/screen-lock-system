# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | ✅ Yes    |
| Older   | ❌ No     |

## Reporting a Vulnerability

If you discover a security issue in Aegis, **please do not open a public GitHub issue**.

Instead, send a private disclosure to the maintainers with:

1. A clear description of the vulnerability.
2. Steps to reproduce (including any relevant request/response payloads).
3. The potential impact.
4. Any suggested remediation, if you have one.

We aim to acknowledge receipt within **48 hours** and provide a remediation timeline within **7 days**.

## Security Design Notes

- Screen-lock PINs are stored as **salted hashes** using Django's `make_password` (PBKDF2-SHA256 by default). Raw PINs are never persisted.
- All authenticated responses include `Cache-Control: no-store` headers to prevent sensitive page caching.
- The lock middleware enforces redirection at the WSGI layer, covering all views uniformly.
- After **3 consecutive incorrect PIN attempts** the session is fully logged out.
- URL-based redirect targets are validated with `url_has_allowed_host_and_scheme` to prevent open-redirect attacks.
