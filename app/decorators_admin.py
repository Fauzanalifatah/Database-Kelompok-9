from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserAdmin


def check_useradmin(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("app:login")

        useradmin = UserAdmin.objects.filter(username=request.user).first()
        if not useradmin:
            messages.error(request, "Profil admin belum tersedia.")
            return redirect("app:profile_admin")

        if not useradmin.photo or not useradmin.telp:
            messages.error(request, "Lengkapi data admin Anda terlebih dahulu.")
            return redirect("app:profile_admin")

        request.useradmin = useradmin
        return view_func(request, *args, **kwargs)

    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("app:login")

        is_admin = (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.last_name == "Super Admin"
        )
        if not is_admin:
            messages.error(request, "Anda tidak memiliki akses sebagai admin.")
            return redirect("app:dashboard")

        return view_func(request, *args, **kwargs)

    return wrapped_view
