from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .forms import validate_six_digit_pin
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    new_pin = forms.CharField(
        label="Set screen lock PIN",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "off", "inputmode": "numeric"}),
        help_text="Enter a 6-digit PIN. Leave blank to keep the current PIN.",
    )

    class Meta:
        model = UserProfile
        exclude = ("pin_hash",)

    def clean_new_pin(self):
        pin = self.cleaned_data.get("new_pin")
        if pin:
            return validate_six_digit_pin(pin)
        return pin

    def save(self, commit=True):
        profile = super().save(commit=False)
        pin = self.cleaned_data.get("new_pin")
        if pin:
            profile.set_pin(pin)
        if commit:
            profile.save()
        return profile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileForm
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ("user", "has_pin")
    search_fields = ("user__username", "user__email")

    @admin.display(boolean=True, description="PIN configured")
    def has_pin(self, obj):
        return bool(obj.pin_hash)
