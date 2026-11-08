import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from app.forms import RegistrationForm
from app.models import UserPengguna


GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_PROFILE_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _google_configuration_error(request):
    messages.error(
        request,
        "Login Google belum dikonfigurasi. Hubungi administrator.",
    )
    return redirect("app:login")


def google_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return _google_configuration_error(request)

    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state
    query = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return redirect(f"{GOOGLE_AUTHORIZATION_URL}?{query}")


def _google_request(url, data=None, access_token=None):
    headers = {"Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    body = urlencode(data).encode() if data is not None else None
    request = Request(url, data=body, headers=headers)
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def google_callback(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.GET.get("error"):
        messages.error(request, "Login Google dibatalkan.")
        return redirect("app:login")

    expected_state = request.session.pop("google_oauth_state", None)
    if not expected_state or not secrets.compare_digest(
        expected_state, request.GET.get("state", "")
    ):
        messages.error(request, "Sesi login Google tidak valid. Silakan coba lagi.")
        return redirect("app:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Kode login Google tidak ditemukan.")
        return redirect("app:login")

    try:
        token_data = _google_request(
            GOOGLE_TOKEN_URL,
            {
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Google tidak mengembalikan access token.")
        profile = _google_request(
            GOOGLE_PROFILE_URL,
            access_token=access_token,
        )
        email = profile.get("email", "").strip().lower()
        if not email or not profile.get("email_verified", False):
            raise ValueError("Email Google tidak tersedia atau belum terverifikasi.")
    except (HTTPError, URLError, ValueError, json.JSONDecodeError) as error:
        messages.error(request, f"Login Google gagal: {error}")
        return redirect("app:login")

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        username_base = email.split("@", 1)[0][:120] or "pengguna"
        username = username_base
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{username_base[:(150 - len(str(suffix)))]}{suffix}"
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=profile.get("given_name", "")[:150],
            last_name=profile.get("family_name", "Pengguna")[:150],
        )
        UserPengguna.objects.create(user=user, telp="")
    elif not user.is_active:
        messages.error(request, "Akun ini tidak aktif.")
        return redirect("app:login")

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "Login Google berhasil. Selamat datang.")
    return redirect("home")


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
        return redirect("home")

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
            return redirect("home")
        form.add_error(None, "Email atau password salah.")

    return render(
        request,
        "app/login.html",
        {"title": "Login", "heading": "Login", "form": form},
    )


def registerView(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.last_name = "Pengguna"
        user.save()
        login(request, user)
        messages.success(
            request,
            "Registrasi berhasil. Selamat datang di Losari Computer.",
        )
        return redirect("home")

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
