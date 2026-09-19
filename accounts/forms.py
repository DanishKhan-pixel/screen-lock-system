from django import forms

PIN_FORMAT_ERROR = "Enter a valid 6-digit PIN."


def _pin_widget(autofocus=False):
    attrs = {
        "inputmode": "numeric",
        "pattern": "[0-9]{6}",
        "autocomplete": "off",
        "maxlength": "6",
        "minlength": "6",
        "class": "pin-input",
    }
    if autofocus:
        attrs["autofocus"] = True
    return forms.PasswordInput(attrs=attrs)


def validate_six_digit_pin(value):
    if not value or not value.isdigit() or len(value) != 6:
        raise forms.ValidationError(PIN_FORMAT_ERROR)
    return value


class ScreenLockForm(forms.Form):
    pin = forms.CharField(
        label="Unlock PIN",
        min_length=6,
        max_length=6,
        widget=_pin_widget(autofocus=True),
        error_messages={
            "required": PIN_FORMAT_ERROR,
            "min_length": PIN_FORMAT_ERROR,
            "max_length": PIN_FORMAT_ERROR,
        },
    )

    def clean_pin(self):
        return validate_six_digit_pin(self.cleaned_data["pin"])


class SetPinForm(forms.Form):
    current_pin = forms.CharField(
        label="Current PIN",
        required=False,
        widget=forms.PasswordInput(
            attrs={"inputmode": "numeric", "autocomplete": "off", "class": "pin-input"}
        ),
    )
    pin = forms.CharField(
        label="New PIN",
        min_length=6,
        max_length=6,
        widget=_pin_widget(),
        error_messages={
            "required": PIN_FORMAT_ERROR,
            "min_length": PIN_FORMAT_ERROR,
            "max_length": PIN_FORMAT_ERROR,
        },
    )
    confirm_pin = forms.CharField(
        label="Confirm PIN",
        min_length=6,
        max_length=6,
        widget=_pin_widget(),
        error_messages={
            "required": PIN_FORMAT_ERROR,
            "min_length": PIN_FORMAT_ERROR,
            "max_length": PIN_FORMAT_ERROR,
        },
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        has_pin = bool(getattr(getattr(user, "profile", None), "pin_hash", ""))
        if has_pin:
            self.fields["current_pin"].required = True
        else:
            self.fields["current_pin"].widget = forms.HiddenInput()

    def clean_pin(self):
        return validate_six_digit_pin(self.cleaned_data["pin"])

    def clean_confirm_pin(self):
        return validate_six_digit_pin(self.cleaned_data["confirm_pin"])

    def clean(self):
        cleaned = super().clean()
        pin = cleaned.get("pin")
        confirm = cleaned.get("confirm_pin")
        if pin and confirm and pin != confirm:
            self.add_error("confirm_pin", "PINs do not match.")

        profile = getattr(self.user, "profile", None)
        if profile and profile.pin_hash:
            current = cleaned.get("current_pin")
            if not current or not profile.check_pin(current):
                self.add_error("current_pin", "Current PIN is incorrect.")
        return cleaned
