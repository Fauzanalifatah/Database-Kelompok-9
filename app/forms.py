from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegistrationForm(forms.Form):
    username = forms.CharField(
        label="Nama pengguna",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contoh: fauzan123",
                "autocomplete": "username",
            }
        ),
    )
    first_name = forms.CharField(
        label="Nama depan",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan nama depan",
                "autocomplete": "given-name",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "nama@email.com",
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label="Kata sandi",
        strip=False,
        help_text="Gunakan minimal 8 karakter dengan kombinasi yang mudah Anda ingat.",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan kata sandi",
                "autocomplete": "new-password",
            }
        ),
    )
    password_confirmation = forms.CharField(
        label="Konfirmasi kata sandi",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ketik ulang kata sandi",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Nama pengguna tersebut sudah digunakan.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email tersebut sudah terdaftar.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("password_confirmation")

        if password and confirmation and password != confirmation:
            self.add_error(
                "password_confirmation",
                "Konfirmasi kata sandi tidak cocok.",
            )
        if password:
            try:
                validate_password(
                    password,
                    User(
                        username=cleaned_data.get("username", ""),
                        email=cleaned_data.get("email", ""),
                    ),
                )
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, commit=True):
        user = User(
            username=self.cleaned_data["username"],
            first_name=self.cleaned_data["first_name"],
            email=self.cleaned_data["email"],
        )
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
