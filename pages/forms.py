from django import forms
from django.contrib.auth.models import User


class ProfileForm(forms.ModelForm):
    job_title = forms.CharField(required=False, max_length=80)
    department = forms.CharField(required=False, max_length=80)

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
        if profile and not self.is_bound:
            self.fields["job_title"].initial = profile.job_title
            self.fields["department"].initial = profile.department
