from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    pin_hash = models.CharField(max_length=128, blank=True, default="")
    job_title = models.CharField(max_length=80, blank=True)
    department = models.CharField(max_length=80, blank=True)

    def set_pin(self, raw_pin):
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        if not self.pin_hash:
            return False
        return check_password(raw_pin, self.pin_hash)

    def __str__(self):
        return f"Profile for {self.user}"
