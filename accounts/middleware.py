from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from .services import is_locked

EXEMPT_URL_NAMES = frozenset(
    {
        "accounts:lock_screen",
        "accounts:activate_lock",
        "accounts:logout",
        "accounts:login",
    }
)


def _has_asset_prefix(path, prefix):
    if not prefix or prefix == "/":
        return False
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return path.startswith(prefix)


def _is_exempt(request):
    if _has_asset_prefix(request.path, settings.STATIC_URL):
        return True
    if _has_asset_prefix(request.path, getattr(settings, "MEDIA_URL", "")):
        return True
    try:
        match = resolve(request.path_info)
    except Resolver404:
        return False
    return match.view_name in EXEMPT_URL_NAMES


def _wants_json(request):
    if request.path.startswith("/api/"):
        return True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept and "text/html" not in accept


class ScreenLockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and is_locked(request):
            if not _is_exempt(request):
                if _wants_json(request):
                    return JsonResponse({"detail": "Screen is locked."}, status=403)
                return redirect("accounts:lock_screen")

        response = self.get_response(request)
        if user is not None and user.is_authenticated:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response

