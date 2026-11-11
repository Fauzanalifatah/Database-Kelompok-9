from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.utils.text import slugify

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
    AdminArtikelForm,
    AdminProdukForm,
    create_produk_gambar_formset,
    create_produk_keunggulan_formset,
    AdminPelangganForm,
    AdminPesananStatusForm,
)
from .forms import RegistrationForm
from .models import (
    Artikel,
    BlogPengguna,
    KategoriArtikel,
    MitraDeepublish,
    ArtikelView,
    Kategori,
    Produk,
    Provinsi,
    UserAdmin,
    UserPengguna,
    Pesanan,
    FooterSetting,
    FooterPayment,
    FooterSocial,
    AboutSetting,
    Testimoni,
    ItemPesanan,
)
from .checkout_forms import CheckoutForm
from .midtrans import create_snap_transaction, is_valid_signature

FOOTER_SOCIAL_PLATFORMS = ("Instagram", "TikTok", "WhatsApp")
FOOTER_PAYMENT_PLATFORMS = ("QRIS", "BRI", "BNI", "Mandiri")


@admin_required
@login_required(login_url="app:login")
def artikel_manager(request):
    articles = list(Artikel.objects.select_related("category"))
    return render(
        request,
        "app/content_manager_list.html",
        {
            "title": "Kelola Artikel",
            "heading": "Kelola Artikel",
            "section": "artikel",
            "objects": articles,
            "item_label": "artikel",
            "add_url": reverse("app:artikel_manager_add"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def artikel_manager_form(request, pk=None):
    instance = Artikel.objects.filter(pk=pk).first() if pk else None
    if pk and instance is None:
        raise Http404
    form = AdminArtikelForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        article = form.save(commit=False)
        if not article.slug:
            article.slug = slugify(article.title_articles)
        article.save()
        messages.success(request, "Artikel berhasil disimpan.")
        return redirect("app:artikel_manager")
    return render(
        request,
        "app/article_manager_form.html",
        {
            "title": "Edit Artikel",
            "heading": "Edit Artikel" if instance else "Tambah Artikel",
            "section": "artikel",
            "form": form,
            "item_label": "artikel",
            "cancel_url": reverse("app:artikel_manager"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def artikel_manager_delete(request, pk):
    article = get_object_or_404(Artikel, pk=pk)
    if request.method == "POST":
        article.delete()
        messages.success(request, "Artikel berhasil dihapus.")
    return redirect("app:artikel_manager")


@admin_required
@login_required(login_url="app:login")
def about_manager(request):
    setting, _ = AboutSetting.objects.get_or_create(pk=1)
    form = AboutSettingForm(request.POST or None, request.FILES or None, instance=setting)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil Tentang Kami berhasil diperbarui.")
        return redirect("app:about_manager")
    return render(
        request,
        "app/content_manager_form.html",
        {
            "title": "Tentang Kami",
            "heading": "Pengaturan Tentang Kami",
            "section": "tentang-kami",
            "form": form,
            "item_label": "Tentang Kami",
            "cancel_url": reverse("app:about_manager"),
            "public_url": reverse("about"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def mitra_manager(request):
    return render(
        request,
        "app/mitra_manager.html",
        {
            "title": "Mitra Losari Computer",
            "heading": "Mitra Losari Computer",
            "objects": MitraDeepublish.objects.all(),
            "add_url": reverse("app:mitra_manager_add"),
            "public_url": reverse("home"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def mitra_manager_form(request, pk=None):
    instance = MitraDeepublish.objects.filter(pk=pk).first() if pk else None
    if pk and instance is None:
        raise Http404
    form = MitraDeepublishForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        mitra = form.save(commit=False)
        if not mitra.pk:
            mitra.urutan = MitraDeepublish.objects.count()
        mitra.save()
        messages.success(request, "Mitra Losari Computer berhasil disimpan.")
        return redirect("app:mitra_manager")
    return render(
        request,
        "app/content_manager_form.html",
        {
            "title": "Edit Mitra Losari Computer",
            "heading": "Edit Mitra Losari Computer" if instance else "Tambah Mitra Losari Computer",
            "section": "mitra",
            "form": form,
            "item_label": "mitra",
            "cancel_url": reverse("app:mitra_manager"),
            "public_url": reverse("home"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def mitra_manager_delete(request, pk):
    mitra = get_object_or_404(MitraDeepublish, pk=pk)
    if request.method == "POST":
        mitra.delete()
        messages.success(request, "Mitra Losari Computer berhasil dihapus.")
    return redirect("app:mitra_manager")


@admin_required
@login_required(login_url="app:login")
def footer_manager(request):
    footer_setting, _ = FooterSetting.objects.get_or_create(pk=1)
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "footer":
            form = FooterSettingForm(request.POST, instance=footer_setting)
            if form.is_valid():
                form.save()
                messages.success(request, "Pengaturan footer berhasil diperbarui.")
                return redirect("app:footer_manager")
        elif form_type == "social_add":
            form = FooterSocialAddForm(request.POST, request.FILES)
            if form.is_valid():
                social = form.save(commit=False)
                social.footer = footer_setting
                social.urutan = footer_setting.socials.count()
                social.save()
                messages.success(request, "Ikon sosial media berhasil ditambahkan.")
                return redirect("app:footer_manager")
        elif form_type == "social":
            name = request.POST.get("social_name", "")
            social = footer_setting.socials.filter(nama=name).first()
            form = FooterSocialForm(request.POST, request.FILES, instance=social)
            if form.is_valid() and name:
                social = form.save(commit=False)
                social.footer = footer_setting
                social.nama = name
                social.urutan = social.urutan or footer_setting.socials.count()
                social.save()
                messages.success(request, f"Ikon {name} berhasil diperbarui.")
                return redirect("app:footer_manager")
        elif form_type == "payment_add":
            form = FooterPaymentAddForm(request.POST, request.FILES)
            if form.is_valid():
                payment = form.save(commit=False)
                payment.footer = footer_setting
                payment.urutan = footer_setting.payments.count()
                payment.save()
                messages.success(request, "Metode pembayaran berhasil ditambahkan.")
                return redirect("app:footer_manager")
        elif form_type == "payment":
            name = request.POST.get("payment_name", "")
            payment = footer_setting.payments.filter(nama=name).first()
            form = FooterPaymentForm(request.POST, request.FILES, instance=payment)
            if form.is_valid() and name:
                payment = form.save(commit=False)
                payment.footer = footer_setting
                payment.nama = name
                payment.urutan = payment.urutan or footer_setting.payments.count()
                payment.save()
                messages.success(request, f"Logo {name} berhasil diperbarui.")
                return redirect("app:footer_manager")
        else:
            form = FooterSettingForm(request.POST, instance=footer_setting)
        messages.error(request, "Gagal menyimpan pengaturan footer. Periksa isian form.")

    footer_form = FooterSettingForm(request.POST if request.method == "POST" and request.POST.get("form_type") == "footer" else None, instance=footer_setting)
    social_forms = []
    for name in FOOTER_SOCIAL_PLATFORMS:
        social = footer_setting.socials.filter(nama=name).first()
        social_forms.append({"name": name, "form": FooterSocialForm(instance=social), "social": social})
    for social in footer_setting.socials.exclude(nama__in=FOOTER_SOCIAL_PLATFORMS):
        social_forms.insert(0, {"name": social.nama, "form": FooterSocialForm(instance=social), "social": social})
    payment_forms = []
    for name in FOOTER_PAYMENT_PLATFORMS:
        payment = footer_setting.payments.filter(nama=name).first()
        payment_forms.append({"name": name, "form": FooterPaymentForm(instance=payment), "payment": payment})
    for payment in footer_setting.payments.exclude(nama__in=FOOTER_PAYMENT_PLATFORMS):
        payment_forms.insert(0, {"name": payment.nama, "form": FooterPaymentForm(instance=payment), "payment": payment})
    return render(
        request,
        "app/footer_manager.html",
        {
            "title": "Pengaturan Footer",
            "heading": "Pengaturan Footer",
            "footer_form": footer_form,
            "footer_social_forms": social_forms,
            "footer_payment_forms": payment_forms,
            "footer_social_add_form": FooterSocialAddForm(),
            "footer_payment_add_form": FooterPaymentAddForm(),
            "public_url": reverse("home"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def produk_manager(request):
    products = list(Produk.objects.select_related("kategori"))
    return render(
        request,
        "app/content_manager_list.html",
        {
            "title": "Kelola Produk",
            "heading": "Kelola Produk",
            "section": "produk",
            "objects": products,
            "item_label": "produk",
            "add_url": reverse("app:produk_manager_add"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def produk_manager_form(request, pk=None):
    instance = Produk.objects.filter(pk=pk).first() if pk else None
    if pk and instance is None:
        raise Http404
    form = AdminProdukForm(request.POST or None, request.FILES or None, instance=instance)
    image_formset = create_produk_gambar_formset(
        request.POST or None, request.FILES or None, instance=instance
    )
    benefit_formset = create_produk_keunggulan_formset(
        request.POST or None, instance=instance
    )
    if request.method == "POST" and form.is_valid() and image_formset.is_valid() and benefit_formset.is_valid():
        product = form.save(commit=False)
        if not product.slug:
            product.slug = slugify(product.nama)
        product.save()
        image_formset.instance = product
        image_formset.save()
        benefit_formset.instance = product
        benefit_formset.save()
        messages.success(request, "Produk berhasil disimpan.")
        return redirect("app:produk_manager")
    return render(
        request,
        "app/content_manager_form.html",
        {
            "title": "Edit Produk",
            "heading": "Edit Produk" if instance else "Tambah Produk",
            "section": "produk",
            "form": form,
            "image_formset": image_formset,
            "benefit_formset": benefit_formset,
            "item_label": "produk",
            "cancel_url": reverse("app:produk_manager"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def produk_manager_delete(request, pk):
    product = get_object_or_404(Produk, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Produk berhasil dihapus.")
    return redirect("app:produk_manager")


@admin_required
@login_required(login_url="app:login")
def pelanggan_manager(request):
    customers = UserPengguna.objects.select_related("user", "provinsi_anggota").order_by(
        "-user__date_joined"
    )
    return render(
        request,
        "app/records_manager.html",
        {
            "title": "Kelola Pelanggan",
            "heading": "Kelola Pelanggan",
            "section": "pelanggan",
            "records": customers,
            "record_type": "pelanggan",
        },
    )


@admin_required
@login_required(login_url="app:login")
def pelanggan_manager_form(request, username):
    member = get_object_or_404(
        UserPengguna.objects.select_related("user"),
        user__username=username,
    )
    form = AdminPelangganForm(
        request.POST or None,
        instance=member.user,
        member=member,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Data pelanggan berhasil diperbarui.")
        return redirect("app:pelanggan_manager")
    return render(
        request,
        "app/record_form.html",
        {
            "title": "Edit Pelanggan",
            "heading": "Edit Pelanggan",
            "section": "pelanggan",
            "form": form,
            "record_type": "pelanggan",
            "cancel_url": reverse("app:pelanggan_manager"),
            "record_name": member.user.get_full_name() or member.user.username,
        },
    )


@admin_required
@login_required(login_url="app:login")
def pesanan_manager(request):
    orders = Pesanan.objects.select_related("pengguna").prefetch_related("item").all()
    return render(
        request,
        "app/records_manager.html",
        {
            "title": "Kelola Pesanan",
            "heading": "Kelola Pesanan",
            "section": "pesanan",
            "records": orders,
            "record_type": "pesanan",
        },
    )


@admin_required
@login_required(login_url="app:login")
def pesanan_manager_form(request, pk):
    order = get_object_or_404(Pesanan.objects.select_related("pengguna"), pk=pk)
    form = AdminPesananStatusForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Status pesanan berhasil diperbarui.")
        return redirect("app:pesanan_manager")
    return render(
        request,
        "app/record_form.html",
        {
            "title": "Edit Pesanan",
            "heading": "Edit Pesanan",
            "section": "pesanan",
            "form": form,
            "record_type": "pesanan",
            "cancel_url": reverse("app:pesanan_manager"),
            "record_name": str(order),
            "order": order,
        },
    )


@admin_required
@login_required(login_url="app:login")
def pesanan_manager_detail(request, pk):
    order = get_object_or_404(
        Pesanan.objects.select_related("pengguna", "pengguna__pengguna")
        .prefetch_related("item__produk"),
        pk=pk,
    )
    form = AdminPesananStatusForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Status pesanan berhasil diperbarui.")
        return redirect("app:pesanan_manager_detail", pk=pk)
    return render(
        request,
        "app/pesanan_detail.html",
        {
            "title": f"Detail Pesanan {str(order.nomor)[:8].upper()}",
            "heading": "Detail Pesanan",
            "section": "pesanan",
            "order": order,
            "form": form,
            "cancel_url": reverse("app:pesanan_manager"),
        },
    )


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
            messages.success(request, "Mitra Losari Computer berhasil disimpan.")
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
    total_pesanan = Pesanan.objects.count()
    pesanan_menunggu = Pesanan.objects.filter(status="menunggu").count()
    pesanan_dibayar = Pesanan.objects.filter(status="dibayar").count()
    pesanan_selesai = Pesanan.objects.filter(status="selesai").count()
    pesanan_terbaru = (
        Pesanan.objects.select_related("pengguna")
        .prefetch_related("item")
        .order_by("-dibuat_pada")[:5]
    )
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
        "total_pesanan": total_pesanan,
        "pesanan_menunggu": pesanan_menunggu,
        "pesanan_dibayar": pesanan_dibayar,
        "pesanan_selesai": pesanan_selesai,
        "pesanan_terbaru": pesanan_terbaru,
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
    return render(
        request,
        "storefront/article_detail.html",
        {"article": article},
    )


def blog_pengguna_list(request):
    blogs = BlogPengguna.objects.filter(
        published=True
    ).select_related("author").order_by("-created_at", "-pk")
    return render(request, "storefront/blog_pengguna_list.html", {"blogs": blogs})


def blog_pengguna_detail(request, slug):
    blog = get_object_or_404(
        BlogPengguna.objects.select_related("author"),
        slug=slug,
        published=True,
    )
    BlogPengguna.objects.filter(pk=blog.pk).update(views=F("views") + 1)
    blog.refresh_from_db(fields=["views"])
    return render(
        request,
        "storefront/blog_pengguna_detail.html",
        {"blog": blog},
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


@login_required(login_url="app:login")
def checkout(request, slug):
    product = get_object_or_404(
        Produk.objects.select_related("kategori"), slug=slug, aktif=True
    )
    profile = UserPengguna.objects.filter(user=request.user).first()
    initial = {
        "nama": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "telp": profile.telp if profile else "",
        "alamat": profile.alamat if profile else "",
    }
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        quantity = form.cleaned_data["jumlah"]
        snap_transaction = None
        snap_error = None
        order = None
        with transaction.atomic():
            locked_product = Produk.objects.select_for_update().get(pk=product.pk)
            if not locked_product.tersedia or locked_product.stok < quantity:
                form.add_error("jumlah", "Stok produk tidak mencukupi.")
            else:
                provinsi_obj = form.cleaned_data.get("provinsi")
                order = Pesanan.objects.create(
                    pengguna=request.user,
                    provinsi=str(provinsi_obj) if provinsi_obj else "",
                    kota=form.cleaned_data.get("kota", ""),
                    kecamatan=form.cleaned_data.get("kecamatan", ""),
                    alamat_pengiriman=form.cleaned_data["alamat"],
                )
                ItemPesanan.objects.create(
                    pesanan=order,
                    produk=locked_product,
                    nama_produk=str(locked_product),
                    harga_satuan=locked_product.harga_aktif,
                    jumlah=quantity,
                )
                order.total = order.hitung_total()
                order.save(update_fields=["total", "diperbarui_pada"])
                try:
                    snap_transaction = create_snap_transaction(
                        order,
                        {
                            "name": form.cleaned_data["nama"],
                            "email": form.cleaned_data["email"],
                            "phone": form.cleaned_data["telp"],
                        },
                        list(order.item.all()),
                    )
                except ImproperlyConfigured as error:
                    snap_error = str(error)
                    transaction.set_rollback(True)
        # Render dilakukan di luar blok atomic agar tidak memicu TransactionManagementError
        if snap_error:
            form.add_error(None, snap_error)
            return render(
                request,
                "storefront/checkout.html",
                {"product": product, "form": form},
                status=503,
            )
        if snap_transaction is not None:
            return render(
                request,
                "storefront/payment_status.html",
                {
                    "order": order,
                    "snap_token": snap_transaction["token"],
                    "midtrans_client_key": settings.MIDTRANS_CLIENT_KEY,
                },
            )
    return render(
        request,
        "storefront/checkout.html",
        {"product": product, "form": form},
    )


@login_required(login_url="app:login")
def payment_status(request, nomor):
    order = get_object_or_404(
        Pesanan.objects.select_related("pengguna").prefetch_related("item__produk"),
        nomor=nomor,
        pengguna=request.user,
    )
    return render(request, "storefront/payment_status.html", {"order": order})


@csrf_exempt
@require_POST
def midtrans_notification(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Payload JSON tidak valid."}, status=400)
    if not settings.MIDTRANS_SERVER_KEY:
        return JsonResponse({"error": "Midtrans belum dikonfigurasi."}, status=503)
    if not is_valid_signature(payload):
        return JsonResponse({"error": "Signature tidak valid."}, status=403)
    try:
        order = Pesanan.objects.get(nomor=payload.get("order_id"))
    except (Pesanan.DoesNotExist, ValueError):
        return JsonResponse({"error": "Pesanan tidak ditemukan."}, status=404)
    try:
        notification_total = Decimal(str(payload.get("gross_amount")))
    except (InvalidOperation, TypeError):
        return JsonResponse({"error": "Nominal transaksi tidak valid."}, status=400)
    if notification_total != order.total:
        return JsonResponse({"error": "Nominal transaksi tidak sesuai."}, status=400)

    transaction_status = payload.get("transaction_status")
    fraud_status = payload.get("fraud_status", "")
    with transaction.atomic():
        order = Pesanan.objects.select_for_update().get(pk=order.pk)
        order.midtrans_transaction_id = payload.get("transaction_id", "")
        order.midtrans_payment_type = payload.get("payment_type", "")
        order.midtrans_fraud_status = fraud_status
        if transaction_status in {"capture", "settlement"} and fraud_status != "challenge":
            if not order.stok_dikurangi:
                for item in order.item.select_related("produk").select_for_update():
                    if item.produk.stok < item.jumlah:
                        order.status = "dibatalkan"
                        break
                    item.produk.stok -= item.jumlah
                    item.produk.save(update_fields=["stok"])
                else:
                    order.stok_dikurangi = True
                    order.status = "dibayar"
            else:
                order.status = "dibayar"
        elif transaction_status == "pending" and order.status == "menunggu":
            order.status = "menunggu"
        elif transaction_status in {"deny", "cancel", "expire", "failure"}:
            order.status = "dibatalkan"
        order.save(
            update_fields=[
                "status",
                "midtrans_transaction_id",
                "midtrans_payment_type",
                "midtrans_fraud_status",
                "stok_dikurangi",
                "diperbarui_pada",
            ]
        )
    return JsonResponse({"message": "Notifikasi berhasil diproses."})


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
