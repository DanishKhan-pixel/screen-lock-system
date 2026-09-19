from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "severity", "owner", "created_at")
    list_filter = ("status", "severity")
    search_fields = ("title", "owner", "summary")
