from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import RegistrationForm
from .models import Kategori, Produk, Provinsi, UserAdmin, UserPengguna


@login_required(login_url="app:login")
def index(request):
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

    user_admin = UserAdmin.objects.filter(username=request.user).first()
    if (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.last_name == "Super Admin"
        or user_admin
    ):
        dashboard_context.update(
            {
                "heading": "Dashboard Administrator",
                "photo": (
                    user_admin.photo
                    if user_admin and user_admin.photo
                    else None
                ),
                "userdetail": user_admin,
            }
        )
        return render(request, "app/dashboard.html", dashboard_context)

    user_pengguna = UserPengguna.objects.filter(user=request.user).first()
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
            }
        )
        return render(request, "app/dashboard.html", dashboard_context)

    dashboard_context["userdetail"] = request.user
    return render(request, "app/dashboard.html", dashboard_context)


def home(request):
    kategori_slug = request.GET.get("kategori", "").strip()
    query = request.GET.get("q", "").strip()
    products = Produk.objects.filter(aktif=True).select_related("kategori")
    selected_category = None
    if kategori_slug:
        selected_category = get_object_or_404(
            Kategori, slug=kategori_slug, aktif=True
        )
        products = products.filter(kategori=selected_category)
    if query:
        products = products.filter(
            Q(nama__icontains=query)
            | Q(merek__icontains=query)
            | Q(deskripsi__icontains=query)
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
        Produk.objects.select_related("kategori"), slug=slug, aktif=True
    )
    related_products = (
        Produk.objects.filter(aktif=True, kategori=product.kategori)
        .exclude(pk=product.pk)
        .order_by("-unggulan", "-dibuat_pada")[:4]
    )
    return render(
        request,
        "storefront/product_detail.html",
        {"product": product, "related_products": related_products},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("app:dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "app:dashboard")
    return render(request, "app/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("app:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("app:dashboard")
    return render(request, "app/register.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("app:login")
