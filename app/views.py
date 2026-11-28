from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.db.models import F, Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import re
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.utils.text import slugify

from .decorators_admin import admin_required
from .form_admin import (
    BannerBerandaForm,
    RunningTextForm,
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
    BannerBeranda,
    RunningText,
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
    ItemKeranjang,
)
from .checkout_forms import CheckoutForm
from .midtrans import create_snap_transaction, is_valid_signature

FOOTER_SOCIAL_PLATFORMS = ("Instagram", "TikTok", "WhatsApp")
FOOTER_PAYMENT_PLATFORMS = ("QRIS", "BRI", "BNI", "Mandiri")


def filter_products_by_search(queryset, query_str):
    """
    Menyaring queryset produk secara cerdas berdasarkan kata kunci pencarian.
    Mendukung pencarian nama, merek, deskripsi, kategori, kondisi, slug,
    dan atribut spesifikasi terstruktur (seperti RAM 'ram 4', 'ram 16',
    SSD/Penyimpanan 'ssd 512', prosesor 'ryzen 5', 'core i5', layar 'retina', dll).
    """
    if not query_str or not str(query_str).strip():
        return queryset

    cleaned_query = (
        re.sub(r"[:=,;/\\]", " ", str(query_str).lower())
        .strip()
    )
    cleaned_query = re.sub(r"\s+", " ", cleaned_query)
    if not cleaned_query:
        return queryset

    # 1. Ekstrak kebutuhan RAM spesifik (mis. 'ram 4', 'ram 4gb', 'ram 16', '4gb ram')
    ram_match = re.search(
        r"\b(?:ram|memory|memori)\s+(\d+)(?:\s*gb)?\b", cleaned_query
    ) or re.search(r"\b(\d+)\s*gb\s*(?:ram|memory|memori)\b", cleaned_query)
    required_ram = ram_match.group(1) if ram_match else None

    # 2. Ekstrak kebutuhan Penyimpanan spesifik (mis. 'ssd 512', 'penyimpanan 128', '128gb rom')
    storage_match = re.search(
        r"\b(?:ssd|hdd|storage|penyimpanan|rom)\s+(\d+)(?:\s*(?:gb|tb))?\b",
        cleaned_query,
    ) or re.search(
        r"\b(\d+)\s*(?:gb|tb)\s*(?:ssd|hdd|storage|penyimpanan|rom)\b",
        cleaned_query,
    )
    required_storage = storage_match.group(1) if storage_match else None

    # Daftar kata token pencarian
    words = [w for w in cleaned_query.split() if w]

    candidate_products = list(queryset)
    matched_ids = []

    for product in candidate_products:
        spek = product.spesifikasi or {}
        if isinstance(spek, str):
            try:
                spek = json.loads(spek)
            except Exception:
                spek = {}

        if not isinstance(spek, dict):
            spek = {}

        # Validasi RAM spesifik jika diminta user (mis. "ram 4" harus cocok dengan produk ber-RAM 4)
        if required_ram:
            p_ram_val = ""
            for k, v in spek.items():
                if str(k).lower().strip() in ["ram", "memory", "memori"]:
                    p_ram_val = str(v).lower()
                    break
            ram_digits = re.findall(r"\d+", p_ram_val)
            if not ram_digits or ram_digits[0] != required_ram:
                continue

        # Validasi Storage spesifik jika diminta user (mis. "ssd 512" atau "128gb")
        if required_storage:
            p_storage_val = ""
            for k, v in spek.items():
                if str(k).lower().strip() in [
                    "penyimpanan", "storage", "ssd", "hdd", "rom"
                ]:
                    p_storage_val = str(v).lower()
                    break
            storage_digits = re.findall(r"\d+", p_storage_val)
            p_name = (product.nama or "").lower()
            has_storage_in_name = (
                f"{required_storage}gb" in p_name
                or f"{required_storage} gb" in p_name
            )
            if (not storage_digits or storage_digits[0] != required_storage) and not has_storage_in_name:
                continue

        # Bangun representasi token spesifikasi yang diperluas
        spec_tokens = []
        for k, v in spek.items():
            k_str = str(k).lower()
            v_str = str(v).lower()
            spec_tokens.extend([k_str, v_str, f"{k_str} {v_str}"])

            # Konversi inch e.g. 14" -> 14 inch, 6.1" -> 6.1 inch
            if '"' in v_str:
                spec_tokens.append(v_str.replace('"', " inch"))
                spec_tokens.append(v_str.replace('"', " inchi"))

            # Pisahkan angka dan satuan e.g. 4gb -> 4 gb, 4, gb
            separated = re.sub(r"(\d+)\s*([a-zA-Z]+)", r"\1 \2", v_str)
            spec_tokens.append(separated)
            spec_tokens.append(f"{k_str} {separated}")
            digits = re.findall(r"\d+", v_str)
            for d in digits:
                spec_tokens.append(f"{k_str} {d}")
                spec_tokens.append(d)

        kategori_nama = (
            product.kategori.nama.lower() if product.kategori and product.kategori.nama else ""
        )
        kondisi_display = (
            product.get_kondisi_display().lower() if hasattr(product, "get_kondisi_display") else ""
        )

        searchable_blob = " ".join([
            (product.nama or "").lower(),
            (product.merek or "").lower(),
            (product.deskripsi or "").lower(),
            kategori_nama,
            (product.kondisi or "").lower(),
            kondisi_display,
            (product.slug or "").lower(),
            " ".join(spec_tokens),
        ]).lower()

        # Setiap kata dalam query harus ditemukan dalam searchable_blob
        match_all = True
        for word in words:
            if required_ram and (word == required_ram or word in ["ram", "memory", "memori"]):
                continue
            if required_storage and (word == required_storage or word in ["ssd", "hdd", "storage", "penyimpanan", "rom"]):
                continue
            if word not in searchable_blob:
                match_all = False
                break

        if match_all:
            matched_ids.append(product.pk)

    if not matched_ids:
        return queryset.none()
    return queryset.filter(pk__in=matched_ids)


@admin_required
@login_required(login_url="app:login")
def artikel_manager(request):
    status_filter = request.GET.get("status", "").strip().lower()
    kategori_filter = request.GET.get("kategori", "").strip()
    search_query = request.GET.get("q", "").strip()

    all_articles = Artikel.objects.select_related("category").order_by("-created_at")

    # Metrics & Executive Feasibility KPIs
    total_artikel = all_articles.count()
    total_terbit = all_articles.filter(published=True).count()
    total_draft = total_artikel - total_terbit
    persen_terbit = round((total_terbit / total_artikel * 100), 1) if total_artikel > 0 else 0
    persen_draft = round(100 - persen_terbit, 1) if total_artikel > 0 else 0

    total_views = all_articles.aggregate(Sum("views"))["views__sum"] or 0
    avg_views = round(total_views / total_artikel, 1) if total_artikel > 0 else 0

    total_kategori = KategoriArtikel.objects.filter(status_category=True).count()
    kategori_list = list(KategoriArtikel.objects.filter(status_category=True).order_by("nama_category"))

    # Apply search filter
    filtered_qs = all_articles
    if search_query:
        filtered_qs = filtered_qs.filter(
            Q(title_articles__icontains=search_query)
            | Q(desc_seo__icontains=search_query)
            | Q(authors__icontains=search_query)
            | Q(content__icontains=search_query)
        )

    # Apply status filter
    if status_filter == "tayang":
        filtered_qs = filtered_qs.filter(published=True)
    elif status_filter == "draft":
        filtered_qs = filtered_qs.filter(published=False)

    # Apply category filter
    if kategori_filter:
        filtered_qs = filtered_qs.filter(category__slug=kategori_filter)

    articles = list(filtered_qs)
    total_views_formatted = f"{total_views:,}".replace(",", ".")

    context = {
        "title": "Kelola & Publikasi Artikel",
        "heading": "Kelola Artikel",
        "section": "artikel",
        "objects": articles,
        "item_label": "artikel",
        "add_url": reverse("app:artikel_manager_add"),
        # KPIs
        "total_artikel": total_artikel,
        "total_terbit": total_terbit,
        "total_draft": total_draft,
        "persen_terbit": persen_terbit,
        "persen_draft": persen_draft,
        "total_views": total_views,
        "total_views_formatted": total_views_formatted,
        "avg_views": avg_views,
        "total_kategori": total_kategori,
        "kategori_list": kategori_list,
        # Filter States
        "status_filter": status_filter,
        "kategori_filter": kategori_filter,
        "search_query": search_query,
    }
    return render(request, "app/artikel_manager.html", context)


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
@require_POST
def artikel_upload_inline_image(request):
    image_file = request.FILES.get("image")
    if not image_file:
        return JsonResponse({"error": "Tidak ada file gambar yang diunggah."}, status=400)

    extension = image_file.name.rsplit(".", 1)[-1].lower() if "." in image_file.name else "jpg"
    if extension not in ["jpg", "jpeg", "png", "webp", "gif", "svg"]:
        return JsonResponse({"error": "Format file tidak didukung."}, status=400)

    import uuid
    from django.core.files.storage import default_storage

    filename = f"artikel/inline/{uuid.uuid4().hex[:12]}.{extension}"
    saved_path = default_storage.save(filename, image_file)
    url = default_storage.url(saved_path)
    return JsonResponse({"url": url})


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
        "app/about_manager.html",
        {
            "title": "Pengaturan Tentang Kami",
            "heading": "Pengaturan Tentang Kami",
            "section": "tentang-kami",
            "setting": setting,
            "form": form,
            "public_url": reverse("about"),
        },
    )


@admin_required
@login_required(login_url="app:login")
def mitra_manager(request):
    objects = MitraDeepublish.objects.all().order_by("urutan", "id")
    total_count = objects.count()
    active_count = objects.filter(aktif=True).count()
    inactive_count = total_count - active_count
    return render(
        request,
        "app/mitra_manager.html",
        {
            "title": "Mitra Losari Computer",
            "heading": "Mitra Losari Computer",
            "objects": objects,
            "total_count": total_count,
            "active_count": active_count,
            "inactive_count": inactive_count,
            "add_url": reverse("app:mitra_manager_add"),
            "public_url": reverse("home"),
            "section": "mitra",
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
        messages.success(request, f"Mitra '{mitra.nama}' berhasil disimpan.")
        return redirect("app:mitra_manager")
    return render(
        request,
        "app/mitra_manager_form.html",
        {
            "title": "Edit Mitra Losari Computer" if instance else "Tambah Mitra Baru",
            "heading": "Edit Mitra Losari Computer" if instance else "Tambah Mitra Baru",
            "instance": instance,
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


def normalize_banner_orders():
    """Memastikan nomor urutan banner sekuensial (1, 2, 3, ...) tanpa duplikasi atau nomor negatif/0."""
    banners = list(BannerBeranda.objects.all().order_by("urutan", "-created_at"))
    for idx, b in enumerate(banners, start=1):
        if b.urutan != idx:
            b.urutan = idx
            b.save(update_fields=["urutan"])


@admin_required
@login_required(login_url="app:login")
def banner_manager(request):
    normalize_banner_orders()
    objects = BannerBeranda.objects.all().order_by("urutan", "-created_at")
    total_count = objects.count()
    active_count = objects.filter(aktif=True).count()
    inactive_count = total_count - active_count
    return render(
        request,
        "app/banner_manager.html",
        {
            "title": "Kelola Banner Beranda",
            "heading": "Banner Beranda",
            "objects": objects,
            "total_count": total_count,
            "active_count": active_count,
            "inactive_count": inactive_count,
            "add_url": reverse("app:banner_manager_add"),
            "public_url": reverse("home"),
            "section": "banner",
        },
    )


@admin_required
@login_required(login_url="app:login")
def banner_manager_form(request, pk=None):
    normalize_banner_orders()
    instance = BannerBeranda.objects.filter(pk=pk).first() if pk else None
    if pk and instance is None:
        raise Http404

    all_banners = list(BannerBeranda.objects.all().order_by("urutan", "-created_at"))
    total_banners = len(all_banners)

    if instance:
        current_urutan = instance.urutan
        max_slots = total_banners
    else:
        current_urutan = total_banners + 1
        max_slots = total_banners + 1

    initial_data = {"urutan": current_urutan} if not instance else None
    form = BannerBerandaForm(
        request.POST or None, request.FILES or None, instance=instance, initial=initial_data
    )

    if request.method == "POST" and form.is_valid():
        banner = form.save(commit=False)
        target_urutan = form.cleaned_data.get("urutan") or current_urutan

        if not banner.pk:
            # Banner baru ditambahkan
            if target_urutan < total_banners + 1:
                # Sisipkan di posisi target_urutan: geser banner yang posisinya >= target_urutan
                for b in BannerBeranda.objects.filter(urutan__gte=target_urutan):
                    b.urutan += 1
                    b.save(update_fields=["urutan"])
                banner.urutan = target_urutan
            else:
                banner.urutan = total_banners + 1
            banner.save()
            normalize_banner_orders()
        else:
            # Edit banner yang sudah ada
            old_urutan = instance.urutan
            if target_urutan != old_urutan:
                if target_urutan < old_urutan:
                    for b in BannerBeranda.objects.filter(urutan__gte=target_urutan, urutan__lt=old_urutan).exclude(pk=instance.pk):
                        b.urutan += 1
                        b.save(update_fields=["urutan"])
                else:
                    for b in BannerBeranda.objects.filter(urutan__gt=old_urutan, urutan__lte=target_urutan).exclude(pk=instance.pk):
                        b.urutan -= 1
                        b.save(update_fields=["urutan"])
                banner.urutan = target_urutan
            banner.save()
            normalize_banner_orders()

        messages.success(
            request, f"Banner '{banner.judul}' berhasil disimpan pada Slide #{banner.urutan}."
        )
        return redirect("app:banner_manager")

    # Siapkan daftar pilihan posisi slide yang ramah pengguna
    position_options = []
    for i in range(1, max_slots + 1):
        if i == 1:
            lbl = "Slide 1 (Paling Pertama / Utama)"
        elif i == max_slots and not instance:
            lbl = f"Slide {i} (Paling Akhir - Otomatis)"
        elif i == max_slots:
            lbl = f"Slide {i} (Paling Akhir)"
        else:
            lbl = f"Slide {i}"

        position_options.append({
            "num": i,
            "label": lbl,
            "is_selected": (i == current_urutan),
        })

    return render(
        request,
        "app/banner_manager_form.html",
        {
            "title": "Edit Banner Beranda" if instance else "Tambah Banner Baru",
            "heading": "Edit Banner Beranda" if instance else "Tambah Banner Baru",
            "instance": instance,
            "section": "banner",
            "form": form,
            "item_label": "banner",
            "cancel_url": reverse("app:banner_manager"),
            "public_url": reverse("home"),
            "current_order_val": current_urutan,
            "last_position_num": max_slots,
            "position_options": position_options,
            "total_banners": total_banners,
        },
    )


@admin_required
@login_required(login_url="app:login")
def banner_manager_delete(request, pk):
    banner = get_object_or_404(BannerBeranda, pk=pk)
    if request.method == "POST":
        judul = banner.judul
        banner.delete()
        normalize_banner_orders()
        messages.success(request, f"Banner '{judul}' berhasil dihapus.")
    return redirect("app:banner_manager")


@admin_required
@login_required(login_url="app:login")
def banner_manager_reorder(request, pk, direction):
    banner = get_object_or_404(BannerBeranda, pk=pk)
    if request.method == "POST":
        normalize_banner_orders()
        banners = list(BannerBeranda.objects.all().order_by("urutan", "-created_at"))
        try:
            current_idx = [b.pk for b in banners].index(banner.pk)
        except ValueError:
            return redirect("app:banner_manager")

        if direction == "up" and current_idx > 0:
            target_banner = banners[current_idx - 1]
            banner.urutan, target_banner.urutan = target_banner.urutan, banner.urutan
            banner.save(update_fields=["urutan"])
            target_banner.save(update_fields=["urutan"])
            normalize_banner_orders()
            messages.success(
                request, f"Urutan banner '{banner.judul}' berhasil dinaikkan ke Slide #{banner.urutan}."
            )
        elif direction == "down" and current_idx < len(banners) - 1:
            target_banner = banners[current_idx + 1]
            banner.urutan, target_banner.urutan = target_banner.urutan, banner.urutan
            banner.save(update_fields=["urutan"])
            target_banner.save(update_fields=["urutan"])
            normalize_banner_orders()
            messages.success(
                request, f"Urutan banner '{banner.judul}' berhasil diturunkan ke Slide #{banner.urutan}."
            )
    return redirect("app:banner_manager")


@admin_required
@login_required(login_url="app:login")
def running_text_manager(request):
    """
    Kelola Teks Berjalan (Running Text / Announcement Marquee) untuk admin.
    Memungkinkan admin menambah, mengedit, mengaktifkan/menonaktifkan, dan menghapus teks pengumuman.
    """
    # Inisialisasi default jika tabel masih kosong sama sekali
    if not RunningText.objects.exists():
        default_items = [
            ("Garansi toko", 1),
            ("Siap kirim ke seluruh kota", 2),
            ("Unit teruji", 3),
            ("Laptop second berkualitas", 4),
        ]
        for teks, urut in default_items:
            RunningText.objects.create(teks=teks, urutan=urut, aktif=True)

    objects = RunningText.objects.all().order_by("urutan", "id")
    total_count = objects.count()
    active_count = objects.filter(aktif=True).count()
    inactive_count = total_count - active_count

    form = RunningTextForm(request.POST or None)
    if request.method == "POST":
        action = request.POST.get("action", "add")
        if action == "add":
            if form.is_valid():
                item = form.save()
                messages.success(request, f"Teks '{item.teks}' berhasil ditambahkan ke running text.")
                return redirect("app:running_text_manager")
            else:
                messages.error(request, "Gagal menambahkan teks. Pastikan input terisi dengan benar.")

    return render(
        request,
        "app/running_text_manager.html",
        {
            "title": "Kelola Running Text",
            "heading": "Running Text (Teks Berjalan)",
            "objects": objects,
            "total_count": total_count,
            "active_count": active_count,
            "inactive_count": inactive_count,
            "form": form,
            "section": "running_text",
            "next_urutan": total_count + 1,
        },
    )


@admin_required
@login_required(login_url="app:login")
def running_text_edit(request, pk):
    """
    Mengubah teks, urutan, atau status aktif dari satu item running text.
    """
    item = get_object_or_404(RunningText, pk=pk)
    form = RunningTextForm(request.POST or None, instance=item)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Perubahan teks '{item.teks}' berhasil disimpan.")
            return redirect("app:running_text_manager")
        else:
            messages.error(request, "Gagal menyimpan perubahan. Periksa kembali isian formulir.")

    objects = RunningText.objects.all().order_by("urutan", "id")
    return render(
        request,
        "app/running_text_manager.html",
        {
            "title": f"Edit Running Text - #{item.pk}",
            "heading": "Edit Teks Berjalan",
            "edit_item": item,
            "form": form,
            "objects": objects,
            "total_count": objects.count(),
            "active_count": objects.filter(aktif=True).count(),
            "inactive_count": objects.filter(aktif=False).count(),
            "section": "running_text",
        },
    )


@admin_required
@login_required(login_url="app:login")
def running_text_delete(request, pk):
    """
    Menghapus teks berjalan.
    """
    item = get_object_or_404(RunningText, pk=pk)
    if request.method == "POST":
        teks = item.teks
        item.delete()
        messages.success(request, f"Teks '{teks}' berhasil dihapus.")
    return redirect("app:running_text_manager")


@admin_required
@login_required(login_url="app:login")
def running_text_toggle(request, pk):
    """
    Toggle 1-klik untuk mengaktifkan / menonaktifkan status teks berjalan.
    """
    item = get_object_or_404(RunningText, pk=pk)
    if request.method == "POST":
        item.aktif = not item.aktif
        item.save(update_fields=["aktif", "updated_at"])
        status_text = "diaktifkan" if item.aktif else "dinonaktifkan"
        messages.success(request, f"Teks '{item.teks}' berhasil {status_text}.")
    return redirect("app:running_text_manager")


def serve_media(request, path):
    """
    Menyajikan file media:
    1. Cek disk lokal terlebih dahulu (MEDIA_ROOT / path).
    2. Jika tidak ada di disk (seperti di Vercel yang read-only), cari di tabel MediaFile.
    """
    import os
    from django.views.static import serve as static_serve

    clean_path = str(path).replace("\\", "/").lstrip("/")
    local_file = os.path.join(settings.MEDIA_ROOT, clean_path)
    if os.path.isfile(local_file):
        return static_serve(request, clean_path, document_root=settings.MEDIA_ROOT)

    try:
        from app.models import MediaFile

        media_file = MediaFile.objects.filter(name=clean_path).first()
        if media_file:
            response = HttpResponse(
                bytes(media_file.data), content_type=media_file.content_type
            )
            response[
                "Cache-Control"
            ] = "public, max-age=86400, stale-while-revalidate=604800"
            return response
    except Exception:
        pass

    raise Http404("Media file not found")


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
    status_filter = request.GET.get("status", "").strip().lower()
    kategori_filter = request.GET.get("kategori", "").strip()
    search_query = request.GET.get("q", "").strip()

    all_products = Produk.objects.select_related("kategori").order_by(
        "-unggulan", "-diperbarui_pada"
    )

    # Calculate Executive Feasibility KPIs
    total_produk = all_products.count()
    total_aktif = all_products.filter(aktif=True).count()
    total_draft = total_produk - total_aktif
    persen_aktif = round((total_aktif / total_produk * 100), 1) if total_produk > 0 else 0
    persen_draft = round(100 - persen_aktif, 1) if total_produk > 0 else 0

    total_unggulan = all_products.filter(unggulan=True).count()
    persen_unggulan = round((total_unggulan / total_produk * 100), 1) if total_produk > 0 else 0

    total_stok_habis = all_products.filter(stok__lte=0).count()
    total_stok_tersedia = all_products.filter(stok__gt=0, aktif=True).count()

    total_unit_stok = all_products.aggregate(Sum("stok"))["stok__sum"] or 0

    # Calculate inventory valuation
    total_valuasi = Decimal("0")
    for p in all_products:
        if p.stok and p.stok > 0 and p.harga:
            total_valuasi += (p.harga * p.stok)

    total_kategori = Kategori.objects.filter(aktif=True).count()
    kategori_list = list(Kategori.objects.filter(aktif=True).order_by("nama"))

    # Apply search query
    filtered_qs = all_products
    if search_query:
        filtered_qs = filter_products_by_search(filtered_qs, search_query)

    # Apply status filter
    if status_filter == "aktif":
        filtered_qs = filtered_qs.filter(aktif=True)
    elif status_filter == "draft":
        filtered_qs = filtered_qs.filter(aktif=False)
    elif status_filter == "unggulan":
        filtered_qs = filtered_qs.filter(unggulan=True)
    elif status_filter == "habis":
        filtered_qs = filtered_qs.filter(stok__lte=0)

    # Apply kategori filter
    if kategori_filter:
        filtered_qs = filtered_qs.filter(kategori__slug=kategori_filter)

    products = list(filtered_qs)
    total_valuasi_formatted = f"{total_valuasi:,.0f}".replace(",", ".")

    context = {
        "title": "Kelola & Katalog Produk",
        "heading": "Kelola Produk",
        "section": "produk",
        "objects": products,
        "item_label": "produk",
        "add_url": reverse("app:produk_manager_add"),
        # KPIs
        "total_produk": total_produk,
        "total_aktif": total_aktif,
        "total_draft": total_draft,
        "persen_aktif": persen_aktif,
        "persen_draft": persen_draft,
        "total_unggulan": total_unggulan,
        "persen_unggulan": persen_unggulan,
        "total_stok_habis": total_stok_habis,
        "total_stok_tersedia": total_stok_tersedia,
        "total_unit_stok": total_unit_stok,
        "total_valuasi_formatted": total_valuasi_formatted,
        "total_kategori": total_kategori,
        "kategori_list": kategori_list,
        # Filter States
        "status_filter": status_filter,
        "kategori_filter": kategori_filter,
        "search_query": search_query,
    }
    return render(request, "app/produk_manager.html", context)


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
    # Pastikan setiap User terdaftar memiliki profil UserPengguna
    for u in User.objects.all():
        if not hasattr(u, "pengguna"):
            UserPengguna.objects.get_or_create(user=u, defaults={"telp": ""})

    metode_filter = request.GET.get("metode", "").strip().lower()
    status_filter = request.GET.get("status", "").strip().lower()
    search_query = request.GET.get("q", "").strip()

    all_customers = UserPengguna.objects.select_related("user", "provinsi_anggota").order_by(
        "-user__date_joined"
    )

    google_q = Q(user__password__startswith="!") | Q(user__password="")

    total_pelanggan = all_customers.count()
    total_google = all_customers.filter(google_q).count()
    total_manual = all_customers.exclude(google_q).count()
    total_aktif = all_customers.filter(user__is_active=True).count()
    total_nonaktif = all_customers.filter(user__is_active=False).count()

    google_percentage = round((total_google / total_pelanggan * 100), 1) if total_pelanggan > 0 else 0
    manual_percentage = round((total_manual / total_pelanggan * 100), 1) if total_pelanggan > 0 else 0
    aktif_percentage = round((total_aktif / total_pelanggan * 100), 1) if total_pelanggan > 0 else 0

    customers = all_customers
    if metode_filter == "google":
        customers = customers.filter(google_q)
    elif metode_filter in ["registrasi", "manual"]:
        customers = customers.exclude(google_q)

    if status_filter == "aktif":
        customers = customers.filter(user__is_active=True)
    elif status_filter == "nonaktif":
        customers = customers.filter(user__is_active=False)

    if search_query:
        customers = customers.filter(
            Q(user__username__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(telp__icontains=search_query)
        )

    for customer in customers:
        pwd = customer.user.password or ""
        is_google = pwd.startswith("!") or pwd == "" or not customer.user.has_usable_password()
        customer.is_google = is_google
        customer.metode_daftar = "google" if is_google else "registrasi"
        customer.metode_daftar_label = "Google OAuth" if is_google else "Registrasi Form"

    return render(
        request,
        "app/records_manager.html",
        {
            "title": "Kelola Pelanggan",
            "heading": "Kelola Pelanggan",
            "section": "pelanggan",
            "records": customers,
            "record_type": "pelanggan",
            "total_pelanggan": total_pelanggan,
            "total_google": total_google,
            "total_manual": total_manual,
            "total_aktif": total_aktif,
            "total_nonaktif": total_nonaktif,
            "google_percentage": google_percentage,
            "manual_percentage": manual_percentage,
            "aktif_percentage": aktif_percentage,
            "metode_filter": metode_filter,
            "status_filter": status_filter,
            "search_query": search_query,
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
            "member": member,
        },
    )


@admin_required
@login_required(login_url="app:login")
def pelanggan_toggle_status(request, username):
    user = get_object_or_404(User, username=username)
    if user.is_superuser:
        messages.error(request, "Akun Superuser tidak dapat dinonaktifkan dari sini.")
        return redirect("app:pelanggan_manager")

    if request.method == "POST":
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        status_text = "diaktifkan" if user.is_active else "dinonaktifkan"
        messages.success(request, f"Status akun '{user.username}' berhasil {status_text}.")
    return redirect("app:pelanggan_manager")


def get_pesanan_tracking_data(days="7"):
    from datetime import timedelta
    now = timezone.now()
    all_orders = Pesanan.objects.all()
    total_orders = all_orders.count()

    paid_orders = all_orders.filter(status__in=["dibayar", "selesai"])
    waiting_orders = all_orders.filter(status="menunggu")
    processing_orders = all_orders.filter(status__in=["diproses", "dikirim"])
    cancelled_orders = all_orders.filter(status="dibatalkan")

    paid_count = paid_orders.count()
    waiting_count = waiting_orders.count()
    processing_count = processing_orders.count()
    cancelled_count = cancelled_orders.count()

    total_revenue = float(paid_orders.aggregate(s=Sum("total"))["s"] or 0)
    pending_revenue = float(waiting_orders.aggregate(s=Sum("total"))["s"] or 0)

    conversion_rate = round((paid_count / total_orders * 100), 1) if total_orders > 0 else 0

    if conversion_rate >= 60:
        health_status = "Sangat Sehat & Menguntungkan"
        health_color = "#16a34a"
        health_badge = "PROFITABEL (SEHAT)"
        health_desc = "Tingkat konversi transaksi lunas sangat tinggi. Cashflow bisnis toko berjalan optimal."
    elif conversion_rate >= 35:
        health_status = "Cukup Layak (Stabil)"
        health_color = "#2563eb"
        health_badge = "STABIL"
        health_desc = "Konversi normal, tingkatkan follow-up WhatsApp kepada pembeli yang belum transfer."
    else:
        health_status = "Perlu Perhatian (Follow-up)"
        health_color = "#d97706"
        health_badge = "PERLU TINDAKAN"
        health_desc = "Banyak pesanan pending. Segera konfirmasi pesanan pembeli agar segera dibayar."

    # Parse days
    if days == "all":
        earliest = all_orders.order_by("dibuat_pada").first()
        if earliest:
            delta = (now.date() - earliest.dibuat_pada.date()).days
            num_days = max(delta + 1, 7)
        else:
            num_days = 7
    else:
        try:
            num_days = int(days)
            if num_days not in [7, 14, 30]:
                num_days = 7
        except (ValueError, TypeError):
            num_days = 7

    date_list = [(now - timedelta(days=i)).date() for i in range(num_days - 1, -1, -1)]

    labels = []
    sudah_bayar_data = []
    menunggu_data = []
    diproses_data = []
    revenue_daily_data = []
    revenue_waiting_data = []
    revenue_processing_data = []

    for d in date_list:
        labels.append(d.strftime("%d %b"))
        day_orders = all_orders.filter(dibuat_pada__date=d)

        day_paid = day_orders.filter(status__in=["dibayar", "selesai"]).count()
        day_waiting = day_orders.filter(status="menunggu").count()
        day_processing = day_orders.filter(status__in=["diproses", "dikirim"]).count()

        day_rev_paid = float(day_orders.filter(status__in=["dibayar", "selesai"]).aggregate(s=Sum("total"))["s"] or 0)
        day_rev_waiting = float(day_orders.filter(status="menunggu").aggregate(s=Sum("total"))["s"] or 0)
        day_rev_processing = float(day_orders.filter(status__in=["diproses", "dikirim"]).aggregate(s=Sum("total"))["s"] or 0)

        sudah_bayar_data.append(day_paid)
        menunggu_data.append(day_waiting)
        diproses_data.append(day_processing)
        revenue_daily_data.append(day_rev_paid)
        revenue_waiting_data.append(day_rev_waiting)
        revenue_processing_data.append(day_rev_processing)

    return {
        "days": str(num_days) if days != "all" else "all",
        "labels": labels,
        "datasets": {
            "sudah_bayar": sudah_bayar_data,
            "menunggu": menunggu_data,
            "diproses": diproses_data,
            "revenue": revenue_daily_data,
            "revenue_sudah_bayar": revenue_daily_data,
            "revenue_menunggu": revenue_waiting_data,
            "revenue_diproses": revenue_processing_data,
        },
        "summary": {
            "total_orders": total_orders,
            "paid_count": paid_count,
            "waiting_count": waiting_count,
            "processing_count": processing_count,
            "cancelled_count": cancelled_count,
            "total_revenue": total_revenue,
            "total_revenue_formatted": f"Rp{total_revenue:,.0f}".replace(",", "."),
            "pending_revenue": pending_revenue,
            "pending_revenue_formatted": f"Rp{pending_revenue:,.0f}".replace(",", "."),
            "conversion_rate": conversion_rate,
            "health_status": health_status,
            "health_color": health_color,
            "health_badge": health_badge,
            "health_desc": health_desc,
            "last_updated": now.strftime("%H:%M:%S WIB"),
        },
    }


@admin_required
@login_required(login_url="app:login")
def pesanan_tracking_api(request):
    days = request.GET.get("days", "7")
    tracking_data = get_pesanan_tracking_data(days=days)
    return JsonResponse(tracking_data)


@admin_required
@login_required(login_url="app:login")
def pesanan_manager(request):
    days = request.GET.get("days", "7")
    status_filter = request.GET.get("status", "").strip()

    orders = Pesanan.objects.select_related("pengguna").prefetch_related("item")
    if status_filter:
        if status_filter == "sudah_bayar":
            orders = orders.filter(status__in=["dibayar", "selesai"])
        elif status_filter == "menunggu":
            orders = orders.filter(status="menunggu")
        elif status_filter == "diproses":
            orders = orders.filter(status__in=["diproses", "dikirim"])
        elif status_filter == "dibatalkan":
            orders = orders.filter(status="dibatalkan")

    orders = orders.all()

    # Sinkronisasi otomatis data transaksi Midtrans (Payment Type & Channel) untuk pesanan terbaru
    if getattr(settings, "MIDTRANS_SERVER_KEY", None):
        try:
            import midtransclient
            core = midtransclient.CoreApi(
                is_production=getattr(settings, "MIDTRANS_IS_PRODUCTION", False),
                server_key=settings.MIDTRANS_SERVER_KEY,
            )
            orders_to_check = [
                o for o in orders[:15]
                if not o.midtrans_payment_type or o.status == "menunggu"
            ]
            for o in orders_to_check:
                try:
                    res = core.transactions.status(str(o.nomor))
                    if res and res.get("status_code") in ["200", "201"]:
                        p_type = res.get("payment_type", "")
                        t_status = res.get("transaction_status", "")
                        tx_id = res.get("transaction_id", "")
                        fraud_st = res.get("fraud_status", "")
                        updated_fields = []
                        if p_type and o.midtrans_payment_type != p_type:
                            o.midtrans_payment_type = p_type
                            updated_fields.append("midtrans_payment_type")
                        if tx_id and o.midtrans_transaction_id != tx_id:
                            o.midtrans_transaction_id = tx_id
                            updated_fields.append("midtrans_transaction_id")
                        if fraud_st and o.midtrans_fraud_status != fraud_st:
                            o.midtrans_fraud_status = fraud_st
                            updated_fields.append("midtrans_fraud_status")
                        if t_status in {"capture", "settlement"} and o.status == "menunggu":
                            o.status = "dibayar"
                            updated_fields.append("status")
                        if updated_fields:
                            o.save(update_fields=updated_fields)
                except Exception:
                    pass
        except Exception:
            pass

    tracking_data = get_pesanan_tracking_data(days=days)

    return render(
        request,
        "app/pesanan_manager.html",
        {
            "title": "Kelola & Tracking Pesanan",
            "heading": "Kelola Pesanan",
            "section": "pesanan",
            "records": orders,
            "orders": orders,
            "status_filter": status_filter,
            "tracking": tracking_data,
            "tracking_json": json.dumps(tracking_data),
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
        .prefetch_related("item__produk", "item__produk__galeri"),
        pk=pk,
    )
    form = AdminPesananStatusForm(request.POST or None, instance=order)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Status pesanan #{str(order.nomor)[:8].upper()} berhasil diperbarui menjadi {order.get_status_display()}.")
        return redirect("app:pesanan_manager_detail", pk=pk)

    # Ensure every ordered item has a valid photo preview
    for it in order.item.all():
        if it.produk and not it.produk.gambar:
            first_gal = it.produk.galeri.first()
            if first_gal and first_gal.gambar:
                it.produk.gambar = first_gal.gambar
                it.produk.save(update_fields=["gambar"])
            else:
                it.produk.gambar = "produk/ec702708-38f3-4f8b-87dc-a90c28405dd2_removalai_preview.png"
                it.produk.save(update_fields=["gambar"])

    customer_phone = ""
    if hasattr(order.pengguna, "pengguna") and order.pengguna.pengguna and order.pengguna.pengguna.telp:
        customer_phone = order.pengguna.pengguna.telp

    clean_phone = "".join(filter(str.isdigit, customer_phone))
    if clean_phone.startswith("0"):
        clean_phone = "62" + clean_phone[1:]

    total_qty = sum((item.jumlah for item in order.item.all()), 0)

    return render(
        request,
        "app/pesanan_detail.html",
        {
            "title": f"Detail Pesanan #{str(order.nomor)[:8].upper()}",
            "heading": f"Pesanan #{str(order.nomor)[:8].upper()}",
            "section": "pesanan",
            "order": order,
            "form": form,
            "clean_phone": clean_phone,
            "customer_phone": customer_phone,
            "total_qty": total_qty,
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
    elif request.method == "POST" and request.POST.get("form_type") == "running_text_add":
        teks = request.POST.get("teks", "").strip()
        if teks:
            urutan = request.POST.get("urutan")
            try:
                urutan = int(urutan)
            except (ValueError, TypeError):
                urutan = RunningText.objects.count() + 1
            aktif = bool(request.POST.get("aktif"))
            RunningText.objects.create(teks=teks, urutan=urutan, aktif=aktif)
            messages.success(request, f"Teks berjalan '{teks}' berhasil ditambahkan.")
            return redirect("app:dashboard")
        messages.error(request, "Teks pengumuman tidak boleh kosong.")
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
    google_user_q = Q(user__password__startswith="!") | Q(user__password="")
    total_anggota_count = UserPengguna.objects.count()
    total_google_count = UserPengguna.objects.filter(google_user_q).count()
    total_manual_count = UserPengguna.objects.exclude(google_user_q).count()

    dashboard_context = {
        "title": "Dashboard",
        "heading": "Dashboard",
        "today": today,
        "total_produk": Produk.objects.count(),
        "total_artikel": Artikel.objects.count(),
        "artikel_terbit": Artikel.objects.filter(published=True).count(),
        "total_anggota": total_anggota_count,
        "total_google_users": total_google_count,
        "total_manual_users": total_manual_count,
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
                "running_texts_list": RunningText.objects.all().order_by("urutan", "id"),
                "running_text_next_urutan": RunningText.objects.count() + 1,
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
        products = filter_products_by_search(products, query)
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
            "banners": BannerBeranda.objects.filter(aktif=True).order_by("urutan", "-created_at"),
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
        products = filter_products_by_search(products, query)
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
    try:
        req_jumlah = int(request.GET.get("jumlah", 1))
        if req_jumlah < 1:
            req_jumlah = 1
        elif product.stok and req_jumlah > product.stok:
            req_jumlah = max(1, product.stok)
    except (ValueError, TypeError):
        req_jumlah = 1

    initial = {
        "nama": request.user.get_full_name() or request.user.username,
        "email": request.user.email,
        "telp": profile.telp if profile else "",
        "alamat": profile.alamat if profile else "",
        "jumlah": req_jumlah,
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
            token = snap_transaction.get("token")
            if token and order:
                order.snap_token = token
                order.save(update_fields=["snap_token"])
            if hasattr(request, "session"):
                request.session[f"snap_{order.nomor}"] = token
            return redirect("app:payment_status", nomor=order.nomor)
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

    # 1. Fitur simulasi demo untuk pengujian status pembayaran
    simulasi = request.GET.get("simulasi")
    if simulasi == "bayar" and order.status == "menunggu":
        with transaction.atomic():
            order.status = "dibayar"
            order.midtrans_transaction_id = f"SIM-{order.nomor.hex[:8].upper()}"
            order.midtrans_payment_type = "qris / gopay (demo)"
            if not order.stok_dikurangi:
                for item in order.item.select_related("produk"):
                    if item.produk:
                        item.produk.stok = max(0, item.produk.stok - item.jumlah)
                        item.produk.save(update_fields=["stok"])
                order.stok_dikurangi = True
            order.save()
            messages.success(request, "Simulasi pembayaran berhasil! Pesanan siap diproses.")
            return redirect("app:payment_status", nomor=order.nomor)
    elif simulasi == "reset" and order.status != "menunggu":
        with transaction.atomic():
            if order.stok_dikurangi:
                for item in order.item.select_related("produk"):
                    if item.produk:
                        item.produk.stok += item.jumlah
                        item.produk.save(update_fields=["stok"])
                order.stok_dikurangi = False
            order.status = "menunggu"
            order.save()
            messages.info(request, "Status pesanan dikembalikan ke 'Menunggu Pembayaran'.")
            return redirect("app:payment_status", nomor=order.nomor)

    # 2. Cek apakah pesanan telah kadaluarsa (24 jam dari waktu pemesanan)
    if order.status == "menunggu" and order.is_expired:
        order.status = "dibatalkan"
        order.save(update_fields=["status", "diperbarui_pada"])

    # 3. Cek status otomatis langsung ke API Midtrans jika masih menunggu
    if order.status == "menunggu" and settings.MIDTRANS_SERVER_KEY:
        try:
            import midtransclient
            core = midtransclient.CoreApi(
                is_production=settings.MIDTRANS_IS_PRODUCTION,
                server_key=settings.MIDTRANS_SERVER_KEY,
            )
            status_res = core.transactions.status(str(order.nomor))
            t_status = status_res.get("transaction_status")
            f_status = status_res.get("fraud_status", "")
            if t_status in {"capture", "settlement"} and f_status != "challenge":
                with transaction.atomic():
                    order.status = "dibayar"
                    order.midtrans_transaction_id = status_res.get("transaction_id", "")
                    order.midtrans_payment_type = status_res.get("payment_type", "")
                    if not order.stok_dikurangi:
                        for item in order.item.select_related("produk"):
                            if item.produk:
                                item.produk.stok = max(0, item.produk.stok - item.jumlah)
                                item.produk.save(update_fields=["stok"])
                        order.stok_dikurangi = True
                    order.save()
            elif t_status in {"expire", "cancel", "deny", "failure"}:
                order.status = "dibatalkan"
                order.midtrans_transaction_id = status_res.get("transaction_id", "")
                order.midtrans_payment_type = status_res.get("payment_type", "")
                order.save(update_fields=["status", "midtrans_transaction_id", "midtrans_payment_type", "diperbarui_pada"])
        except Exception:
            pass

    profile = UserPengguna.objects.filter(user=request.user).first()
    # 4. Siapkan Snap Token jika pesanan masih dalam status menunggu pembayaran dan belum kedaluwarsa
    snap_token = order.snap_token or request.session.get(f"snap_{order.nomor}")
    if not snap_token and order.status == "menunggu" and not order.is_expired:
        try:
            customer = {
                "name": order.pengguna.get_full_name() or order.pengguna.username,
                "email": order.pengguna.email,
                "phone": profile.telp if profile else "08123456789",
            }
            snap_res = create_snap_transaction(order, customer, list(order.item.all()))
            snap_token = snap_res.get("token")
            if snap_token:
                order.snap_token = snap_token
                order.save(update_fields=["snap_token"])
                request.session[f"snap_{order.nomor}"] = snap_token
        except Exception:
            pass

    return render(
        request,
        "storefront/payment_status.html",
        {
            "order": order,
            "profile": profile,
            "snap_token": snap_token,
            "midtrans_client_key": settings.MIDTRANS_CLIENT_KEY,
        },
    )


def angka_ke_terbilang(n):
    """Konversi nominal angka integer/decimal menjadi teks terbilang Bahasa Indonesia resmi."""
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan", "Sepuluh", "Sebelas"]
    try:
        n = int(n)
    except (ValueError, TypeError):
        return ""
    if n < 0:
        return "Minus " + angka_ke_terbilang(abs(n))
    if n < 12:
        return satuan[n]
    elif n < 20:
        return (angka_ke_terbilang(n - 10) + " Belas").strip()
    elif n < 100:
        sisa = (" " + angka_ke_terbilang(n % 10)) if (n % 10 != 0) else ""
        return (angka_ke_terbilang(n // 10) + " Puluh" + sisa).strip()
    elif n < 200:
        sisa = (" " + angka_ke_terbilang(n - 100)) if (n - 100 != 0) else ""
        return ("Seratus" + sisa).strip()
    elif n < 1000:
        sisa = (" " + angka_ke_terbilang(n % 100)) if (n % 100 != 0) else ""
        return (angka_ke_terbilang(n // 100) + " Ratus" + sisa).strip()
    elif n < 2000:
        sisa = (" " + angka_ke_terbilang(n - 1000)) if (n - 1000 != 0) else ""
        return ("Seribu" + sisa).strip()
    elif n < 1000000:
        sisa = (" " + angka_ke_terbilang(n % 1000)) if (n % 1000 != 0) else ""
        return (angka_ke_terbilang(n // 1000) + " Ribu" + sisa).strip()
    elif n < 1000000000:
        sisa = (" " + angka_ke_terbilang(n % 1000000)) if (n % 1000000 != 0) else ""
        return (angka_ke_terbilang(n // 1000000) + " Juta" + sisa).strip()
    elif n < 1000000000000:
        sisa = (" " + angka_ke_terbilang(n % 1000000000)) if (n % 1000000000 != 0) else ""
        return (angka_ke_terbilang(n // 1000000000) + " Miliar" + sisa).strip()
    return str(n)


def order_receipt(request, nomor):
    """Halaman khusus cetak nota / struk resmi dengan animasi dispenser termal kasir."""
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        order = get_object_or_404(
            Pesanan.objects.select_related("pengguna").prefetch_related("item__produk"),
            nomor=nomor,
        )
    elif request.user.is_authenticated:
        order = get_object_or_404(
            Pesanan.objects.select_related("pengguna").prefetch_related("item__produk"),
            nomor=nomor,
            pengguna=request.user,
        )
    else:
        return redirect(f"{reverse('app:login')}?next={request.path}")

    # Guard: Nota resmi hanya dapat diterbitkan setelah pembayaran lunas
    if order.status in ["menunggu", "dibatalkan"]:
        messages.warning(
            request,
            f"Nota untuk pesanan #{str(order.nomor)[:8].upper()} belum dapat dicetak karena status saat ini masih '{order.get_status_display()}'. Nota resmi hanya dapat diterbitkan setelah pembayaran dinyatakan lunas.",
        )
        if request.user.is_staff or request.user.is_superuser:
            return redirect("app:pesanan_manager_detail", pk=order.pk)
        return redirect("app:payment_status", nomor=order.nomor)

    profile = UserPengguna.objects.filter(user=order.pengguna).first()
    footer_setting, _ = FooterSetting.objects.get_or_create(pk=1)
    about_setting = AboutSetting.objects.first()
    total_terbilang = f"{angka_ke_terbilang(order.total)} Rupiah" if order.total else ""

    return render(
        request,
        "storefront/order_receipt.html",
        {
            "order": order,
            "profile": profile,
            "footer_setting": footer_setting,
            "about_setting": about_setting,
            "total_terbilang": total_terbilang,
        },
    )


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


@csrf_exempt
def logout_view(request):
    logout(request)
    return redirect("app:login")



# ═══════════════════════════════════════════════════
#  KERANJANG BELANJA (CART)
# ═══════════════════════════════════════════════════

def cart_view(request):
    """Display the shopping cart page, automatically syncing with database stock."""
    from .cart import get_cart
    cart = get_cart(request)

    # Automatically synchronize cart item quantities with admin-managed DB stock
    for item in cart.item.select_related("produk").all():
        max_stok = getattr(item.produk, "stok", 1)
        if max_stok < 1:
            pass
        elif item.jumlah > max_stok:
            item.jumlah = max_stok
            item.save(update_fields=["jumlah"])

    items = cart.item.select_related("produk", "produk__kategori").all()
    return render(request, "storefront/cart.html", {
        "cart": cart,
        "items": items,
    })


@require_POST
def cart_add(request, slug):
    """Add a product to the cart with database stock validation."""
    from .cart import add_to_cart, get_cart
    produk = get_object_or_404(Produk, slug=slug)
    if not produk.tersedia or produk.stok < 1:
        messages.error(request, f"Maaf, stok {produk.merek} {produk.nama} sedang habis.")
        next_url = request.POST.get("next", request.META.get("HTTP_REFERER", reverse("app:cart_view")))
        return redirect(next_url)

    try:
        jumlah = int(request.POST.get("jumlah", 1))
    except (ValueError, TypeError):
        jumlah = 1
    cart = get_cart(request)
    existing_item = cart.item.filter(produk=produk).first()
    current_qty = existing_item.jumlah if existing_item else 0

    if current_qty >= produk.stok:
        messages.warning(
            request,
            f"Jumlah {produk.merek} {produk.nama} di keranjang sudah mencapai batas stok maksimal ({produk.stok} unit)."
        )
    else:
        add_to_cart(request, produk, jumlah)
        messages.success(request, f"{produk.merek} {produk.nama} ditambahkan ke keranjang!")
    next_url = request.POST.get("next", request.META.get("HTTP_REFERER", reverse("app:cart_view")))
    return redirect(next_url)


@require_POST
def cart_update(request, item_id):
    """Update quantity of a cart item with stock limits."""
    from .cart import update_cart_item
    item = get_object_or_404(ItemKeranjang.objects.select_related("produk"), pk=item_id)
    try:
        jumlah = int(request.POST.get("jumlah", 1))
    except (ValueError, TypeError):
        jumlah = 1
    if jumlah > item.produk.stok:
        messages.warning(
            request,
            f"Jumlah produk {item.produk.nama} tidak dapat melebihi stok yang tersedia ({item.produk.stok} unit)."
        )
    update_cart_item(item_id, jumlah)
    return redirect(reverse("app:cart_view"))


@require_POST
def cart_remove(request, item_id):
    """Remove an item from the cart."""
    from .cart import remove_from_cart
    remove_from_cart(item_id)
    messages.success(request, "Produk dihapus dari keranjang.")
    return redirect(reverse("app:cart_view"))
