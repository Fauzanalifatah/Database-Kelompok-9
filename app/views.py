from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators_admin import admin_required
from .form_admin import formProfile
from .forms import RegistrationForm
from .models import Kategori, Produk, Provinsi, UserAdmin, UserPengguna


@admin_required
@login_required(login_url="app:login")
def index(request):
    user_admin = UserAdmin.objects.filter(username=request.user).first()
    if user_admin is None:
        user_admin = UserAdmin(username=request.user)
    user_pengguna = (
        UserPengguna.objects.select_related("provinsi_anggota")
        .filter(user=request.user)
        .first()
    )

    if request.method == "POST":
        profile_form = formProfile(
            request.POST,
            request.FILES,
            instance=user_admin,
            user=request.user,
            member=user_pengguna,
        )
        if profile_form.is_valid():
            with transaction.atomic():
                user_admin = profile_form.save(commit=False)
                user_admin.username = request.user
                user_admin.save()
                user_pengguna, _ = UserPengguna.objects.get_or_create(
                    user=request.user,
                    defaults={
                        "telp": profile_form.cleaned_data["telp"],
                    },
                )
                user_pengguna.telp = profile_form.cleaned_data["telp"]
                user_pengguna.gender = profile_form.cleaned_data["gender"]
                user_pengguna.alamat = profile_form.cleaned_data["alamat"]
                user_pengguna.provinsi_anggota = (
                    profile_form.cleaned_data["provinsi_anggota"]
                )
                user_pengguna.save()
                request.user.email = profile_form.cleaned_data["email"]
                request.user.save(update_fields=["email"])
            messages.success(request, "Profil admin berhasil diperbarui.")
            return redirect("app:dashboard")
        messages.error(request, "Gagal memperbarui profil. Periksa isian form.")
    else:
        profile_form = formProfile(instance=user_admin, user=request.user)

    today = timezone.localdate()
    dashboard_context = {
        "title": "Dashboard",
        "heading": "Dashboard",
        "today": today,
        "total_produk": Produk.objects.count(),
        "total_anggota": UserPengguna.objects.count(),
        "total_provinsi": Provinsi.objects.count(),
        "total_admin": UserAdmin.objects.count(),
        "total_user": User.objects.count(),
        "produk_terbaru": Produk.objects.order_by("-id")[:5],
        "provinsi_aktif": Provinsi.objects.filter(aktif=True).count(),
    }

    dashboard_context["profil_pengguna"] = user_pengguna
    is_admin = request.user.is_staff or request.user.is_superuser
    if is_admin:
        dashboard_context.update(
            {
                "heading": "Dashboard Administrator",
                "photo": (
                    user_admin.photo
                    if user_admin and user_admin.photo
                    else None
                ),
                "userdetail": user_admin,
                "profile_form": profile_form,
                "profile_user": request.user,
                "profile_member": user_pengguna,
                "is_admin": True,
            }
        )
        return render(request, "app/dashboard.html", dashboard_context)

    if request.user.last_name == "Pengguna" or user_pengguna:

        if not user_pengguna:
            messages.error(request, "Profil pengguna belum tersedia.")
            return redirect("app:profile_pengguna")

        if (
            not user_pengguna.photo
            or not user_pengguna.telp
            or not user_pengguna.provinsi_anggota
            or not user_pengguna.alamat
        ):
            messages.error(
                request,
                "Harap lengkapi profil Anda terlebih dahulu.",
            )
            return redirect("app:profile_pengguna")

        dashboard_context.update(
            {
                "heading": "Dashboard Pengguna",
                "photo": user_pengguna.photo,
                "userdetail": user_pengguna,
                "is_admin": False,
            }
        )
        return render(request, "app/dashboard.html", dashboard_context)

    dashboard_context["userdetail"] = request.user
    return render(request, "app/dashboard.html", dashboard_context)


def home(request):
    kategori_slug = request.GET.get("kategori", "").strip()
    query = request.GET.get("q", "").strip()
    products = (
        Produk.objects.filter(aktif=True)
        .select_related("kategori")
        .prefetch_related("galeri")
    )
    selected_category = None
    if kategori_slug:
        selected_category = get_object_or_404(
            Kategori, slug=kategori_slug, aktif=True
        )
        products = products.filter(kategori=selected_category)
    if query:
        search_terms = query.split()
        for term in search_terms:
            products = products.filter(
                Q(nama__icontains=term)
                | Q(merek__icontains=term)
                | Q(deskripsi__icontains=term)
                | Q(kategori__nama__icontains=term)
                | Q(slug__icontains=term)
            )
    return render(
        request,
        "storefront/home.html",
        {
            "categories": Kategori.objects.filter(aktif=True),
            "products": products,
            "selected_category": selected_category,
            "query": query,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Produk.objects.select_related("kategori").prefetch_related(
            "galeri", "keunggulan"
        ),
        slug=slug,
        aktif=True,
    )
    related_queryset = (
        Produk.objects.filter(aktif=True, kategori=product.kategori)
        .select_related("kategori")
        .prefetch_related("galeri")
        .exclude(pk=product.pk)
        .order_by("-unggulan", "-dibuat_pada")
    )
    related_products = list(related_queryset[:4])
    if len(related_products) < 4:
        related_ids = [item.pk for item in related_products]
        additional_products = (
            Produk.objects.filter(aktif=True)
            .select_related("kategori")
            .prefetch_related("galeri")
            .exclude(pk=product.pk)
            .exclude(pk__in=related_ids)
            .order_by("-unggulan", "-dibuat_pada")[: 4 - len(related_products)]
        )
        related_products.extend(additional_products)
    gallery = list(product.galeri.all())
    benefits = list(product.keunggulan.all())
    if not benefits:
        benefits = [
            {
                "judul": "Garansi Toko 1 Bulan",
                "deskripsi": "Jaminan tukar unit jika ada kendala fungsi mesin.",
                "ikon": "shield",
                "warna": "green",
            },
            {
                "judul": "Mesin 100% Original",
                "deskripsi": "Bukan barang servis atau bekas rakitan.",
                "ikon": "star",
                "warna": "blue",
            },
            {
                "judul": "Free Tas & Mouse",
                "deskripsi": "Langsung siap digunakan untuk kerja atau kuliah.",
                "ikon": "gift",
                "warna": "yellow",
            },
            {
                "judul": "Packing Kayu Aman",
                "deskripsi": "Kirim se-Indonesia dengan bubble tebal & asuransi.",
                "ikon": "box",
                "warna": "purple",
            },
        ]
    gallery_by_type = {photo.tipe: photo for photo in gallery}
    primary_gallery_image = next(
        (photo for photo in gallery if photo.tipe == "depan"),
        gallery[0] if gallery else None,
    )
    return render(
        request,
        "storefront/product_detail.html",
        {
            "product": product,
            "gallery": gallery,
            "gallery_by_type": gallery_by_type,
            "primary_gallery_image": primary_gallery_image,
            "benefits": benefits,
            "related_products": related_products,
        },
    )


def shop(request):
    kategori_slug = request.GET.get("kategori", "").strip()
    query = request.GET.get("q", "").strip()
    budget = request.GET.get("budget", "").strip()
    products = (
        Produk.objects.filter(aktif=True)
        .select_related("kategori")
        .prefetch_related("galeri")
    )
    selected_category = None
    if kategori_slug:
        selected_category = get_object_or_404(
            Kategori, slug=kategori_slug, aktif=True
        )
        products = products.filter(kategori=selected_category)
    if query:
        search_terms = query.split()
        for term in search_terms:
            products = products.filter(
                Q(nama__icontains=term)
                | Q(merek__icontains=term)
                | Q(deskripsi__icontains=term)
                | Q(kategori__nama__icontains=term)
                | Q(slug__icontains=term)
            )
    budget_ranges = {
        "under-5": (None, 5_000_000),
        "5-10": (5_000_000, 10_000_000),
        "over-10": (10_000_000, None),
    }
    if budget in budget_ranges:
        minimum, maximum = budget_ranges[budget]
        if minimum is not None:
            products = products.filter(harga__gte=minimum)
        if maximum is not None:
            products = products.filter(harga__lt=maximum)
    return render(
        request,
        "storefront/shop.html",
        {
            "categories": Kategori.objects.filter(aktif=True),
            "products": products,
            "selected_category": selected_category,
            "query": query,
            "budget": budget,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home")
    return render(request, "app/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")
    return render(request, "app/register.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("app:login")
