from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
import re

from django.shortcuts import get_object_or_404, redirect, render

from .form_pengguna import formProfile
from .forms import UserBlogForm
from .models import BlogPengguna, BlogPenggunaImage, UserPengguna, Pesanan


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

    # Otomatis tandai pesanan 'menunggu' yang melewati 24 jam sebagai 'dibatalkan' (kedaluwarsa)
    batas_waktu_kadaluarsa = timezone.now() - timedelta(hours=24)
    Pesanan.objects.filter(
        pengguna=request.user,
        status="menunggu",
        dibuat_pada__lt=batas_waktu_kadaluarsa,
    ).update(status="dibatalkan")

    user_orders = (
        Pesanan.objects.filter(pengguna=request.user)
        .prefetch_related("item__produk")
        .order_by("-dibuat_pada")
    )
    total_orders = user_orders.count()
    total_pesanan_pending = user_orders.filter(status="menunggu").count()
    recent_orders = user_orders[:3]

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
        "active_menu": "profil",
        "recent_orders": recent_orders,
        "total_orders": total_orders,
        "total_pesanan_pending": total_pesanan_pending,
    }
    return render(request, "pengguna/profil_pengguna.html", context)


@login_required(login_url="app:login")
def pesanan_pengguna(request):
    status_filter = request.GET.get("status", "").strip().lower()

    # Otomatis tandai pesanan 'menunggu' yang melewati batas 24 jam sebagai 'dibatalkan' (kedaluwarsa)
    batas_waktu_kadaluarsa = timezone.now() - timedelta(hours=24)
    Pesanan.objects.filter(
        pengguna=request.user,
        status="menunggu",
        dibuat_pada__lt=batas_waktu_kadaluarsa,
    ).update(status="dibatalkan")

    all_orders = (
        Pesanan.objects.filter(pengguna=request.user)
        .prefetch_related("item__produk", "item__produk__galeri")
        .order_by("-dibuat_pada")
    )

    total_orders = all_orders.count()
    total_menunggu = all_orders.filter(status="menunggu").count()
    total_dibayar = all_orders.filter(status__in=["dibayar", "diproses", "dikirim"]).count()
    total_selesai = all_orders.filter(status="selesai").count()
    total_dibatalkan = all_orders.filter(status="dibatalkan").count()

    orders = all_orders
    if status_filter == "menunggu":
        orders = orders.filter(status="menunggu")
    elif status_filter == "dibayar":
        orders = orders.filter(status__in=["dibayar", "diproses", "dikirim"])
    elif status_filter == "selesai":
        orders = orders.filter(status="selesai")
    elif status_filter == "dibatalkan":
        orders = orders.filter(status="dibatalkan")

    userpengguna = UserPengguna.objects.filter(user=request.user).first()

    context = {
        "title": "Pesanan Saya",
        "heading": "Riwayat Pesanan",
        "orders": orders,
        "status_filter": status_filter,
        "total_orders": total_orders,
        "total_menunggu": total_menunggu,
        "total_dibayar": total_dibayar,
        "total_selesai": total_selesai,
        "total_dibatalkan": total_dibatalkan,
        "total_pesanan_pending": total_menunggu,
        "userpengguna": userpengguna,
        "photo": userpengguna.photo if userpengguna and userpengguna.photo else None,
        "active_menu": "pesanan",
    }
    return render(request, "pengguna/pesanan_pengguna.html", context)


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
            existing_inline_images = list(article.inline_images.all())
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
            for inline_image in existing_inline_images:
                if inline_image.image.url not in article.content:
                    inline_image.image.delete(save=False)
                    inline_image.delete()
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
