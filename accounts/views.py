from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ScreenLockForm
from .services import (
    INCORRECT_PIN_MESSAGE,
    MAX_FAILED_ATTEMPTS,
    is_locked,
    lock_session,
    logout_after_failed_attempts,
    record_failed_attempt,
    unlock_session,
    user_pin_matches,
)


class AppLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "input")
        return form


class AppLogoutView(LogoutView):
    pass


@login_required
@require_POST
def activate_lock(request):
    lock_session(request, request.POST.get("next"))
    return redirect("accounts:lock_screen")


@login_required
def lock_screen(request):
    if not is_locked(request):
        return redirect("pages:dashboard")

    form = ScreenLockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if user_pin_matches(request.user, form.cleaned_data["pin"]):
            return redirect(unlock_session(request))

        attempts = record_failed_attempt(request)
        if attempts >= MAX_FAILED_ATTEMPTS:
            logout_after_failed_attempts(request)
            messages.error(
                request,
                "Too many incorrect PIN attempts. Please sign in again.",
            )
            return redirect("accounts:login")
        form.add_error("pin", INCORRECT_PIN_MESSAGE)

    return render(request, "accounts/lock.html", {"form": form})
