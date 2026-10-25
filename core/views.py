from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from app.forms import RegistrationForm


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Alamat email"}
        ),
    )
    password = forms.CharField(
        label="Kata sandi",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Kata sandi"}
        ),
    )


def loginView(request):
    if request.user.is_authenticated:
        return redirect("app:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        user = User.objects.filter(email__iexact=email).first()
        username = user.username if user else email
        authenticated_user = authenticate(
            request,
            username=username,
            password=form.cleaned_data["password"],
        )
        if authenticated_user is not None:
            login(request, authenticated_user)
            messages.success(request, "Selamat datang kembali.")
            return redirect(request.GET.get("next") or "app:dashboard")
        form.add_error(None, "Email atau password salah.")

    return render(
        request,
        "app/login.html",
        {"title": "Login", "heading": "Login", "form": form},
    )


def registerView(request):
    if request.user.is_authenticated:
        return redirect("app:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.last_name = "Pengguna"
        user.save()
        messages.success(request, "Registrasi berhasil, silakan login.")
        return redirect("app:login")

    return render(
        request,
        "app/register.html",
        {"title": "Daftar Akun", "heading": "Pendaftaran Akun", "form": form},
    )


@login_required(login_url="app:login")
def LogoutView(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Anda telah berhasil logout.")
        return redirect("app:login")

    return redirect("app:dashboard")
