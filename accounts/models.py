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
    phone = models.CharField(max_length=30, blank=True, help_text="Optional contact number.")

    def set_pin(self, raw_pin):
        self.pin_hash = make_password(raw_pin)

    def clear_pin(self):
        """Remove the stored PIN, effectively disabling the screen lock."""
        self.pin_hash = ""

    def check_pin(self, raw_pin):
        if not self.pin_hash:
            return False
        return check_password(raw_pin, self.pin_hash)

    @property
    def pin_configured(self):
        """Returns True if the user has set a screen lock PIN."""
        return bool(self.pin_hash)

    @property
    def avatar_initials(self):
        """Returns up to two uppercase initials derived from the user's name."""
        user = self.user
        parts = [user.first_name, user.last_name]
        initials = "".join(p[0] for p in parts if p)
        if not initials:
            initials = user.username[:2]
        return initials.upper()[:2]

    def __str__(self):
        return f"Profile for {self.user}"
