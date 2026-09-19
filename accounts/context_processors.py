from .services import is_locked


def screen_lock(request):
    user = getattr(request, "user", None)
    locked = bool(user is not None and user.is_authenticated and is_locked(request))
    return {"screen_locked": locked}
