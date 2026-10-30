from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .form_pengguna import formProfile
from .models import UserPengguna


@login_required
def profile_pengguna(request):
    userpengguna = UserPengguna.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = formProfile(
            request.POST,
            request.FILES,
            instance=userpengguna,
            user=request.user,
        )
        if form.is_valid():
            with transaction.atomic():
                pengguna = form.save(commit=False)
                pengguna.user = request.user
                pengguna.save()
                request.user.first_name = form.cleaned_data["nama"]
                request.user.email = form.cleaned_data["email"]
                request.user.save(update_fields=["first_name", "email"])
            messages.success(request, "Data pengguna berhasil disimpan.")
            return redirect("app:profile_pengguna")
        messages.error(
            request,
            "Data profil belum lengkap atau terjadi kesalahan pengisian. "
            "Silakan periksa kembali form.",
        )
    else:
        form = formProfile(instance=userpengguna, user=request.user)

    context = {
        "title": "Profil Pengguna",
        "heading": "Profil Saya Losari Computer",
        "userpengguna": userpengguna,
        "photo": (
            userpengguna.photo
            if userpengguna and userpengguna.photo
            else None
        ),
        "form": form,
    }
    return render(request, "pengguna/profil_pengguna.html", context)
