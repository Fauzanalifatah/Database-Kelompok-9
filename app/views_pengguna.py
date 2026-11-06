from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
import re

from django.shortcuts import get_object_or_404, redirect, render

from .form_pengguna import formProfile
from .forms import UserBlogForm
from .models import BlogPengguna, BlogPenggunaImage, UserPengguna


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
        "blogs": BlogPengguna.objects.filter(author=request.user),
        "userpengguna": userpengguna,
        "photo": (
            userpengguna.photo
            if userpengguna and userpengguna.photo
            else None
        ),
        "form": form,
    }
    return render(request, "pengguna/profil_pengguna.html", context)


@login_required
def blog_pengguna(request):
    return render(
        request,
        "pengguna/blog_pengguna.html",
        {
            "title": "Blog Saya",
            "articles": BlogPengguna.objects.filter(author=request.user),
        },
    )


@login_required
def artikel_pengguna_form(request, slug=None):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(
            request,
            "Admin tidak dapat menulis blog pengguna.",
        )
        return redirect("app:dashboard")

    instance = (
        get_object_or_404(BlogPengguna, slug=slug, author=request.user)
        if slug
        else None
    )
    if request.method == "POST":
        form = UserBlogForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            content = article.content or ""
            inline_images = request.FILES.getlist("inline_images")
            for index, uploaded_image in enumerate(inline_images):
                marker = f"[[BLOG_IMAGE_{index}]]"
                if marker not in content:
                    continue
                inline_image = BlogPenggunaImage.objects.create(
                    blog=article,
                    image=uploaded_image,
                )
                image_markup = (
                    f'<img class="blog-inline-image" src="{inline_image.image.url}" '
                    f'alt="Gambar dalam blog {article.title}">'
                )
                content = content.replace(marker, image_markup, 1)
            article.content = re.sub(
                r"<script\b[^>]*>.*?</script>|on\w+\s*=\s*(['\"]).*?\1|"
                r"(?:href|src)\s*=\s*(['\"])\s*javascript:.*?\2",
                "",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            article.save(update_fields=["content", "updated_at"])
            messages.success(request, "Blog berhasil disimpan.")
            return redirect("app:blog_pengguna")
        messages.error(
            request,
            "Blog belum dapat disimpan. Periksa kembali isian Anda.",
        )
    else:
        form = UserBlogForm(instance=instance)
    return render(
        request,
        "pengguna/artikel_pengguna_form.html",
        {
            "title": "Tulis Blog" if instance is None else "Edit Blog",
            "form": form,
            "article": instance,
        },
    )


@login_required
def hapus_artikel_pengguna(request, slug):
    article = get_object_or_404(BlogPengguna, slug=slug, author=request.user)
    if request.method == "POST":
        article.delete()
        messages.success(request, "Blog berhasil dihapus.")
    return redirect("app:blog_pengguna")
