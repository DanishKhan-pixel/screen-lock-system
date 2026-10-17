from django import forms
from django.contrib.auth.models import User


class ProfileForm(forms.ModelForm):
    job_title = forms.CharField(required=False, max_length=80)
    department = forms.CharField(required=False, max_length=80)
    phone = forms.CharField(required=False, max_length=30, label="Phone")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input"}),
            "last_name": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
        }

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop("profile", None)
        super().__init__(*args, **kwargs)
        self.fields["job_title"].widget.attrs["class"] = "input"
        self.fields["department"].widget.attrs["class"] = "input"
        self.fields["phone"].widget.attrs["class"] = "input"
        if profile and not self.is_bound:
            self.fields["job_title"].initial = profile.job_title
            self.fields["department"].initial = profile.department
            self.fields["phone"].initial = profile.phone


class ReportForm(forms.ModelForm):
    class Meta:
        from .models import Report
        model = Report
        fields = ["title", "status", "severity", "owner", "summary", "note"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Brief incident title"}
            ),
            "status": forms.Select(attrs={"class": "input"}),
            "severity": forms.Select(attrs={"class": "input"}),
            "owner": forms.TextInput(
                attrs={"class": "input", "placeholder": "Assigned responder or team"}
            ),
            "summary": forms.TextInput(
                attrs={"class": "input", "placeholder": "One-line operational summary"}
            ),
            "note": forms.Textarea(
                attrs={
                    "class": "input",
                    "rows": 4,
                    "placeholder": "Detailed investigation logs or findings",
                }
            ),
        }
