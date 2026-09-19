from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import SetPinForm

from .forms import ProfileForm
from .models import Report


def home(request):
    if request.user.is_authenticated:
        return redirect("pages:dashboard")
    return redirect("accounts:login")


@login_required
def dashboard(request):
    reports = Report.objects.all()
    status_counts = {
        row["status"]: row["total"]
        for row in reports.values("status").annotate(total=Count("id"))
    }
    return render(
        request,
        "pages/dashboard.html",
        {
            "user_count": User.objects.count(),
            "pin_configured": bool(request.user.profile.pin_hash),
            "report_total": reports.count(),
            "active_reports": status_counts.get(Report.STATUS_ACTIVE, 0),
            "review_reports": status_counts.get(Report.STATUS_REVIEW, 0),
            "recent_reports": reports[:5],
        },
    )


@login_required
def reports(request):
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page") or 1

    qs = Report.objects.all()
    if status in dict(Report.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(owner__icontains=query))

    page_obj = Paginator(qs, 8).get_page(page_number)
    return render(
        request,
        "pages/reports.html",
        {
            "status": status,
            "page": page_number,
            "query": query,
            "page_obj": page_obj,
            "statuses": Report.STATUS_CHOICES,
        },
    )


@login_required
def users(request):
    query = request.GET.get("q", "").strip()
    qs = User.objects.select_related("profile").order_by("username")
    if query:
        qs = qs.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    return render(request, "pages/users.html", {"people": qs, "query": query})


@login_required
def profile(request):
    form = ProfileForm(instance=request.user, profile=request.user.profile)
    return render(request, "pages/profile.html", {"form": form})


@login_required
@require_POST
def update_profile(request):
    form = ProfileForm(request.POST, instance=request.user, profile=request.user.profile)
    if form.is_valid():
        form.save()
        profile = request.user.profile
        profile.job_title = form.cleaned_data.get("job_title", "")
        profile.department = form.cleaned_data.get("department", "")
        profile.save(update_fields=["job_title", "department"])
        messages.success(request, "Profile updated.")
        return redirect("pages:profile")
    return render(request, "pages/profile.html", {"form": form})


@login_required
def settings_page(request):
    form = SetPinForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        profile = request.user.profile
        profile.set_pin(form.cleaned_data["pin"])
        profile.save(update_fields=["pin_hash"])
        messages.success(request, "Screen lock PIN updated.")
        return redirect("pages:settings")
    return render(
        request,
        "pages/settings.html",
        {
            "form": form,
            "pin_configured": bool(request.user.profile.pin_hash),
        },
    )


@login_required
def api_status(request):
    return JsonResponse(
        {
            "username": request.user.username,
            "authenticated": request.user.is_authenticated,
        }
    )
