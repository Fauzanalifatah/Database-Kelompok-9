from django.contrib import messages
from django.shortcuts import redirect, render

from .decorators_admin import admin_required
from .form_admin import formProfile
from .models import UserAdmin


@admin_required
def profile_admin(request):
    try:
        useradmin = UserAdmin.objects.get(username=request.user)
    except UserAdmin.DoesNotExist:
        useradmin = UserAdmin(username=request.user)

    if request.method == "POST":
        form = formProfile(
            request.POST,
            request.FILES,
            instance=useradmin,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profil Anda berhasil diperbarui.")
            return redirect("app:profile_admin")
        messages.error(request, "Gagal memperbarui profil. Periksa isian form.")
    else:
        form = formProfile(instance=useradmin)

    context = {
        "title": "Profil Admin",
        "heading": "Edit Profil Admin",
        "useradmin": useradmin,
        "photo": useradmin.photo if getattr(useradmin, "photo", None) else None,
        "form": form,
    }
    return render(request, "admin_super/profile_admin.html", context)
