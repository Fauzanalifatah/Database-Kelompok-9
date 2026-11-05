from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators_admin import admin_required
from .form_admin import (
    FooterPaymentForm,
    FooterPaymentAddForm,
    FooterSettingForm,
    FooterSocialForm,
    FooterSocialAddForm,
    MitraDeepublishForm,
    AboutSettingForm,
    TestimoniPublicForm,
    formProfile,
)
from .forms import RegistrationForm
from .models import (
    Artikel,
    KategoriArtikel,
    MitraDeepublish,
    ArtikelView,
    Kategori,
    Produk,
    Provinsi,
    UserAdmin,
    UserPengguna,
    FooterSetting,
    FooterPayment,
    FooterSocial,
    AboutSetting,
    Testimoni,
)

FOOTER_SOCIAL_PLATFORMS = ("Instagram", "TikTok", "WhatsApp")
FOOTER_PAYMENT_PLATFORMS = ("QRIS", "BRI", "BNI", "Mandiri")


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

    footer_setting, _ = FooterSetting.objects.get_or_create(pk=1)
    about_setting, _ = AboutSetting.objects.get_or_create(pk=1)
    profile_form = formProfile(
        instance=user_admin,
        user=request.user,
        member=user_pengguna,
    )
    if request.method == "POST" and request.POST.get("form_type") == "about":
        about_form = AboutSettingForm(
            request.POST, request.FILES, instance=about_setting
        )
        if about_form.is_valid():
            about_form.save()
            messages.success(request, "Profil Tentang Kami berhasil diperbarui.")
            return redirect("app:dashboard")
        messages.error(request, "Gagal memperbarui Tentang Kami.")
    elif request.method == "POST" and request.POST.get("form_type") == "mitra_deepublish":
        mitra_id = request.POST.get("mitra_id")
        instance = (
            MitraDeepublish.objects.filter(pk=mitra_id).first()
            if mitra_id
            else None
        )
        mitra_form = MitraDeepublishForm(
            request.POST, request.FILES, instance=instance
        )
        if mitra_form.is_valid():
            mitra = mitra_form.save(commit=False)
            if not mitra.pk:
                mitra.urutan = MitraDeepublish.objects.count()
            mitra.save()
            messages.success(request, "Mitra Deepublish berhasil disimpan.")
            return redirect("app:dashboard")
        messages.error(request, "Gagal menyimpan mitra. Periksa nama dan gambar.")
    elif request.method == "POST" and request.POST.get("form_type") == "social_add":
        social_form = FooterSocialAddForm(request.POST, request.FILES)
        if social_form.is_valid():
            social = social_form.save(commit=False)
            social.footer = footer_setting
            social.urutan = footer_setting.socials.count()
            social.save()
            messages.success(request, "Ikon sosial media berhasil ditambahkan.")
            return redirect("app:dashboard")
        messages.error(request, "Gagal menambahkan ikon sosial media.")
    elif request.method == "POST" and request.POST.get("form_type") == "social":
        social_name = request.POST.get("social_name", "")
        if not social_name:
            messages.error(request, "Platform sosial media tidak valid.")
            return redirect("app:dashboard")
        social = footer_setting.socials.filter(nama=social_name).first()
        social_is_new = social is None
        if social is None:
            social = FooterSocial(
                footer=footer_setting,
                nama=social_name,
                urutan=footer_setting.socials.count(),
            )
        social_form = FooterSocialForm(
            request.POST, request.FILES, instance=social
        )
        if social_form.is_valid():
            social = social_form.save(commit=False)
            social.footer = footer_setting
            social.nama = social_name
            if social_is_new:
                social.urutan = footer_setting.socials.count()
            social.save()
            messages.success(
                request, f"Ikon {social_name} berhasil diperbarui."
            )
            return redirect("app:dashboard")
        messages.error(request, "Gagal memperbarui ikon. Periksa isian form.")
    elif request.method == "POST" and request.POST.get("form_type") == "footer":
        footer_form = FooterSettingForm(request.POST, instance=footer_setting)
        if footer_form.is_valid():
            footer_form.save()
            messages.success(request, "Pengaturan footer berhasil diperbarui.")
            return redirect("app:dashboard")
        messages.error(request, "Gagal memperbarui footer. Periksa isian form.")
    elif request.method == "POST" and request.POST.get("form_type") == "payment_add":
        payment_form = FooterPaymentAddForm(request.POST, request.FILES)
        if payment_form.is_valid():
            payment = payment_form.save(commit=False)
            payment.footer = footer_setting
            payment.urutan = footer_setting.payments.count()
            payment.save()
            messages.success(request, "Metode pembayaran berhasil ditambahkan.")
            return redirect("app:dashboard")
        messages.error(request, "Gagal menambahkan metode pembayaran.")
    elif request.method == "POST" and request.POST.get("form_type") == "payment":
        payment_name = request.POST.get("payment_name", "")
        if not payment_name:
            messages.error(request, "Metode pembayaran tidak valid.")
            return redirect("app:dashboard")
        payment = footer_setting.payments.filter(nama=payment_name).first()
        payment_is_new = payment is None
        if payment is None:
            payment = FooterPayment(
                footer=footer_setting,
                nama=payment_name,
                urutan=footer_setting.payments.count(),
            )
        payment_form = FooterPaymentForm(
            request.POST, request.FILES, instance=payment
        )
        if payment_form.is_valid():
            payment = payment_form.save(commit=False)
            payment.footer = footer_setting
            payment.nama = payment_name
            if payment_is_new:
                payment.urutan = footer_setting.payments.count()
            payment.save()
            messages.success(
                request, f"Logo {payment_name} berhasil diperbarui."
            )
            return redirect("app:dashboard")
        messages.error(request, "Gagal memperbarui logo pembayaran.")
    elif request.method == "POST":
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
    footer_form = FooterSettingForm(instance=footer_setting)
    about_form = AboutSettingForm(instance=about_setting)
    mitra_deepublish_forms = [
        {"item": item, "form": MitraDeepublishForm(instance=item)}
        for item in MitraDeepublish.objects.all()
    ]
    footer_social_forms = []
    for social_name in FOOTER_SOCIAL_PLATFORMS:
        social = footer_setting.socials.filter(nama=social_name).first()
        footer_social_forms.append(
            {
                "name": social_name,
                "form": FooterSocialForm(instance=social),
                "social": social,
            }
        )
    for social in footer_setting.socials.exclude(
        nama__in=FOOTER_SOCIAL_PLATFORMS
    ):
        footer_social_forms.insert(
            0,
            {
                "name": social.nama,
                "form": FooterSocialForm(instance=social),
                "social": social,
            },
        )
    footer_payment_forms = []
    for payment_name in FOOTER_PAYMENT_PLATFORMS:
        payment = footer_setting.payments.filter(nama=payment_name).first()
        footer_payment_forms.append(
            {
                "name": payment_name,
                "form": FooterPaymentForm(instance=payment),
                "payment": payment,
            }
        )
    for payment in footer_setting.payments.exclude(
        nama__in=FOOTER_PAYMENT_PLATFORMS
    ):
        footer_payment_forms.insert(
            0,
            {
                "name": payment.nama,
                "form": FooterPaymentForm(instance=payment),
                "payment": payment,
            },
        )
    footer_social_add_form = FooterSocialAddForm()
    footer_payment_add_form = FooterPaymentAddForm()
    mitra_deepublish_add_form = MitraDeepublishForm()

    today = timezone.localdate()
    dashboard_context = {
        "title": "Dashboard",
        "heading": "Dashboard",
        "today": today,
        "total_produk": Produk.objects.count(),
        "total_artikel": Artikel.objects.count(),
        "artikel_terbit": Artikel.objects.filter(published=True).count(),
        "total_anggota": UserPengguna.objects.count(),
        "total_provinsi": Provinsi.objects.count(),
        "total_admin": UserAdmin.objects.count(),
        "total_user": User.objects.count(),
        "produk_terbaru": Produk.objects.order_by("-id")[:5],
        "artikel_terbaru": Artikel.objects.order_by("-created_at")[:5],
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
                "footer_setting": footer_setting,
                "footer_form": footer_form,
                "footer_social_forms": footer_social_forms,
                "footer_payment_forms": footer_payment_forms,
                "footer_social_add_form": footer_social_add_form,
                "footer_payment_add_form": footer_payment_add_form,
                "about_setting": about_setting,
                "about_form": about_form,
                "mitra_deepublish_forms": mitra_deepublish_forms,
                "mitra_deepublish_add_form": mitra_deepublish_add_form,
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
            "latest_articles": Artikel.objects.filter(published=True).order_by(
                "-created_at"
            )[:3],
            "mitra_deepublish": MitraDeepublish.objects.filter(aktif=True),
            "products": products,
            "selected_category": selected_category,
            "query": query,
        },
    )


def about(request):
    about_setting, _ = AboutSetting.objects.get_or_create(pk=1)
    return render(request, "storefront/about.html", {"about_setting": about_setting})


def testimonials(request):
    items = list(
        Testimoni.objects.filter(aktif=True).select_related(
            "pengguna",
            "pengguna__pengguna",
            "pengguna__admin_profile",
        )
    )
    user_testimonial = (
        Testimoni.objects.filter(pengguna=request.user).first()
        if request.user.is_authenticated
        else None
    )
    testimonial_form = None
    if request.user.is_authenticated and user_testimonial is None:
        testimonial_form = TestimoniPublicForm(
            request.POST or None,
            request.FILES or None,
        )
        if request.method == "POST":
            if testimonial_form.is_valid():
                testimonial = testimonial_form.save(commit=False)
                testimonial.pengguna = request.user
                testimonial.nama_pelanggan = (
                    request.user.get_full_name().strip()
                    or request.user.username
                )
                testimonial.aktif = True
                try:
                    testimonial.save()
                except IntegrityError:
                    messages.error(
                        request,
                        "Akun Anda sudah memiliki satu testimoni.",
                    )
                else:
                    messages.success(
                        request,
                        "Terima kasih, testimoni Anda berhasil ditambahkan.",
                    )
                    return redirect("testimonials")
            else:
                messages.error(request, "Periksa kembali isian testimoni Anda.")
    total_reviews = len(items)
    average_rating = (
        sum(item.rating for item in items) / total_reviews if total_reviews else 0
    )
    return render(
        request,
        "storefront/testimonials.html",
        {
            "testimonials": items,
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "testimonial_form": testimonial_form,
            "user_testimonial": user_testimonial,
        },
    )


def article_list(request):
    articles = (
        Artikel.objects.filter(
            published=True,
            category__status_category=True,
        )
        .select_related("category")
        .order_by("-created_at", "-pk")
    )
    if request.GET.get("semua") != "1":
        articles = articles[:5]
    return render(
        request,
        "storefront/article_list.html",
        {
            "articles": articles,
            "article_categories": KategoriArtikel.objects.filter(
                status_category=True
            ),
        },
    )


def article_detail(request, slug):
    article = get_object_or_404(
        Artikel.objects.select_related("category"),
        slug=slug,
        published=True,
        category__status_category=True,
    )
    if request.user.is_authenticated:
        visitor_key = f"user:{request.user.pk}"
    else:
        if not request.session.session_key:
            request.session.create()
        visitor_key = f"session:{request.session.session_key}"

    _, created = ArtikelView.objects.get_or_create(
        artikel=article,
        visitor_key=visitor_key,
    )
    if created:
        Artikel.objects.filter(pk=article.pk).update(views=F("views") + 1)
    article.refresh_from_db(fields=["views"])
    related_articles = (
        Artikel.objects.filter(published=True)
        .exclude(pk=article.pk)
        .order_by("-views", "-created_at")[:5]
    )
    return render(
        request,
        "storefront/article_detail.html",
        {"article": article, "related_articles": related_articles},
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
