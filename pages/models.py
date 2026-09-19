from django.db import models


class Report(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_REVIEW = "review"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_REVIEW, "In review"),
        (STATUS_CLOSED, "Closed"),
    ]
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    title = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    owner = models.CharField(max_length=80)
    summary = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
