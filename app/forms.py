from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Nama pengguna",
            "first_name": "Nama depan",
            "last_name": "Nama belakang",
            "email": "Email",
        }
        widgets = {
            field: forms.TextInput(attrs={"class": "form-control"})
            for field in ("username", "first_name", "last_name")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["class"] = "form-control"
        self.fields["password1"].label = "Kata sandi"
        self.fields["password2"].label = "Konfirmasi kata sandi"
