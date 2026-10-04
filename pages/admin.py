from django.contrib import admin

from .models import Report


def close_reports(modeladmin, request, queryset):
    updated = queryset.update(status=Report.STATUS_CLOSED)
    modeladmin.message_user(request, f"{updated} report(s) marked as closed.")


close_reports.short_description = "Mark selected reports as closed"


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "severity", "owner", "created_at", "updated_at")
    list_filter = ("status", "severity")
    search_fields = ("title", "owner", "summary")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    actions = [close_reports]
