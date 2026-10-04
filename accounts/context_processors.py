from .services import failed_attempts, is_locked, lock_timestamp


def screen_lock(request):
    user = getattr(request, "user", None)
    locked = bool(user is not None and user.is_authenticated and is_locked(request))
    ctx = {"screen_locked": locked}
    if locked:
        ctx["lock_since"] = lock_timestamp(request)
        ctx["failed_pin_attempts"] = failed_attempts(request)
    return ctx
