from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserPengguna


def check_userpengguna(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("app:login")

        userpengguna = UserPengguna.objects.filter(
            user=request.user
        ).first()
        request.userpengguna = userpengguna

        if (
            not userpengguna
            or not userpengguna.photo
            or not userpengguna.gender
        ):
            messages.error(request, "Lengkapi data Anda terlebih dahulu.")
            return redirect("app:profile_pengguna")

        return view_func(request, *args, **kwargs)

    return wrapped_view


def pengguna_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("app:login")

        if request.user.last_name != "Pengguna":
            messages.error(request, "Anda tidak memiliki akses sebagai pengguna.")
            return redirect("app:dashboard")

        return view_func(request, *args, **kwargs)

    return wrapped_view
