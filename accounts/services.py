import datetime

from django.contrib.auth import logout
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

SESSION_LOCKED = "screen_lock_locked"
SESSION_RETURN_URL = "screen_lock_return_url"
SESSION_FAILED_ATTEMPTS = "screen_lock_failed_attempts"
SESSION_LOCK_TIMESTAMP = "screen_lock_timestamp"
MAX_FAILED_ATTEMPTS = 3

INCORRECT_PIN_MESSAGE = "The PIN you entered is incorrect."


def is_locked(request):
    return bool(request.session.get(SESSION_LOCKED))


def failed_attempts(request):
    try:
        return int(request.session.get(SESSION_FAILED_ATTEMPTS) or 0)
    except (TypeError, ValueError):
        return 0


def lock_timestamp(request):
    """Return the datetime when the session was locked, or None."""
    ts = request.session.get(SESSION_LOCK_TIMESTAMP)
    if ts:
        try:
            return datetime.datetime.fromisoformat(ts)
        except (TypeError, ValueError):
            return None
    return None


def default_return_url():
    return reverse("pages:dashboard")


def safe_return_url(request, url):
    if url and url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return url
    return default_return_url()


def lock_session(request, return_url):
    if not is_locked(request):
        request.session[SESSION_RETURN_URL] = safe_return_url(request, return_url)
        request.session[SESSION_FAILED_ATTEMPTS] = 0
        request.session[SESSION_LOCK_TIMESTAMP] = datetime.datetime.now(
            tz=datetime.timezone.utc
        ).isoformat()
    request.session[SESSION_LOCKED] = True


def unlock_session(request):
    return_url = request.session.pop(SESSION_RETURN_URL, None)
    request.session.pop(SESSION_LOCKED, None)
    request.session.pop(SESSION_LOCK_TIMESTAMP, None)
    request.session[SESSION_FAILED_ATTEMPTS] = 0
    return safe_return_url(request, return_url)


def record_failed_attempt(request):
    attempts = failed_attempts(request) + 1
    request.session[SESSION_FAILED_ATTEMPTS] = attempts
    return attempts


def user_pin_matches(user, pin):
    profile = getattr(user, "profile", None)
    if profile is None or not profile.pin_hash:
        return False
    return profile.check_pin(pin)


def logout_after_failed_attempts(request):
    logout(request)
