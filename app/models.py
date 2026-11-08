import os
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


User.add_to_class(
    "__str__",
    lambda self: f"{self.username} - {self.first_name}",
)


class Provinsi(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    nama_provinsi = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nama Provinsi",
    )
    aktif = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        verbose_name = "Provinsi"
        verbose_name_plural = "Provinsi"
        ordering = ["nama_provinsi"]

    def __str__(self):
        return self.nama_provinsi


def rename_photo_anggota(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    filename = f"{instance.user.username}_{timestamp}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("img_profile", "anggota", filename)


class UserPengguna(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="pengguna",
    )
    telp = models.CharField(max_length=15)
    gender = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        choices=[
            ("Laki-laki", "Laki-laki"),
            ("Perempuan", "Perempuan"),
        ],
    )
    alamat = models.CharField(max_length=50, null=True, blank=True)
    photo = models.ImageField(
        upload_to=rename_photo_anggota,
        null=True,
        blank=True,
    )
    provinsi_anggota = models.ForeignKey(
        Provinsi,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Anggota"
        verbose_name_plural = "Anggota"

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = UserPengguna.objects.filter(pk=self.pk).first()
            if (
                old_instance
                and old_instance.photo
                and old_instance.photo != self.photo
            ):
                old_instance.photo.delete(save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.user)


def rename_photo_admin(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    filename = f"{instance.username}_{timestamp}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("img_profile", "admin", filename)


def default_product_slug():
    return f"produk-{uuid.uuid4().hex[:12]}"


def default_article_slug():
    return f"artikel-{uuid.uuid4().hex[:12]}"


def default_article_category_slug():
    return f"kategori-artikel-{uuid.uuid4().hex[:8]}"


def rename_mitra_deepublish_image(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"mitra-{uuid.uuid4().hex[:10]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("mitra-deepublish", filename)


def rename_article_image(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"{instance.slug or 'artikel'}-{uuid.uuid4().hex[:8]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("artikel", filename)


def rename_footer_icon(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"{instance.nama.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("footer", filename)


class FooterSetting(models.Model):
    nama_toko = models.CharField(max_length=120, default="Losari Computer")
    deskripsi = models.CharField(
        max_length=255,
        default="Partner teknologi untuk kebutuhan kuliah, kerja, desain, dan gaming.",
    )
    alamat = models.TextField(
        default="Jl. Raya Losari No. 9\nLosari, Brebes, Jawa Tengah"
    )
    jam_pelayanan = models.CharField(
        max_length=150, default="Senin - Jumat | 08.00 - 17.00 WIB"
    )
    email = models.EmailField(default="hello@losaricomputer.com")
    whatsapp = models.CharField(max_length=20, default="6281234567890")
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengaturan footer"
        verbose_name_plural = "Pengaturan footer"

    def __str__(self):
        return self.nama_toko


class FooterSocial(models.Model):
    footer = models.ForeignKey(
        FooterSetting, on_delete=models.CASCADE, related_name="socials"
    )
    nama = models.CharField(max_length=40)
    url = models.URLField(max_length=255, blank=True)
    nomor_telepon = models.CharField(max_length=30, blank=True)
    ikon = models.ImageField(upload_to=rename_footer_icon)
    urutan = models.PositiveIntegerField(default=0)
    aktif = models.BooleanField(default=True)

    class Meta:
        ordering = ["urutan", "nama"]
        verbose_name = "Ikon sosial footer"
        verbose_name_plural = "Ikon sosial footer"

    def __str__(self):
        return self.nama


def rename_footer_payment_icon(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"payment-{instance.nama.lower()}-{uuid.uuid4().hex[:8]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("footer", filename)


def rename_about_image(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"about-{instance.pk or 'profile'}-{uuid.uuid4().hex[:8]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("about", filename)


class AboutSetting(models.Model):
    logo = models.ImageField(upload_to=rename_about_image, blank=True)
    judul = models.CharField(max_length=180, default="Tentang Losari Computer")
    tagline = models.CharField(
        max_length=255,
        default="Partner teknologi terpercaya untuk kebutuhan digital Anda.",
    )
    deskripsi = models.TextField(
        default="Losari Computer hadir untuk membantu masyarakat mendapatkan perangkat teknologi berkualitas dengan layanan yang jujur, ramah, dan profesional."
    )
    sejarah = models.TextField(
        default="Berawal dari usaha mikro yang melayani kebutuhan komputer dan laptop di Losari, kami terus berkembang melalui kepercayaan pelanggan dan komitmen pada kualitas."
    )
    ceo_nama = models.CharField(max_length=120, default="CEO Losari Computer")
    ceo_jabatan = models.CharField(max_length=120, default="Founder & CEO")
    ceo_foto = models.ImageField(upload_to=rename_about_image, blank=True)
    visi = models.TextField(
        default="Menjadi partner teknologi pilihan yang membantu setiap orang tumbuh dan produktif."
    )
    misi = models.TextField(
        default="Menyediakan produk terpercaya, memberikan konsultasi yang jujur, dan menghadirkan layanan purna jual yang dapat diandalkan."
    )
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengaturan tentang kami"
        verbose_name_plural = "Pengaturan tentang kami"

    def __str__(self):
        return self.judul


def rename_testimonial_photo(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"customer-{uuid.uuid4().hex[:10]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("testimoni", filename)


class Testimoni(models.Model):
    pengguna = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimoni",
        verbose_name="Akun pelanggan",
    )
    nama_pelanggan = models.CharField(max_length=120, verbose_name="Nama pelanggan")
    kota = models.CharField(max_length=80, blank=True, verbose_name="Kota")
    produk = models.CharField(max_length=150, blank=True, verbose_name="Produk yang dibeli")
    foto = models.ImageField(
        upload_to=rename_testimonial_photo,
        blank=True,
        verbose_name="Foto pelanggan",
    )
    rating = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Rating",
    )
    pesan = models.TextField(verbose_name="Testimoni")
    aktif = models.BooleanField(default=True, verbose_name="Tampilkan")
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dibuat_pada", "-pk"]
        verbose_name = "Testimoni pelanggan"
        verbose_name_plural = "Testimoni pelanggan"

    @property
    def display_name(self):
        if self.pengguna:
            full_name = self.pengguna.get_full_name().strip()
            if full_name:
                return full_name
            admin_profile = getattr(self.pengguna, "admin_profile", None)
            if admin_profile and admin_profile.nama_panggilan:
                return admin_profile.nama_panggilan
            return self.pengguna.username
        return self.nama_pelanggan

    @property
    def display_photo(self):
        if self.pengguna:
            user_profile = getattr(self.pengguna, "pengguna", None)
            if user_profile and user_profile.photo:
                return user_profile.photo
            admin_profile = getattr(self.pengguna, "admin_profile", None)
            if admin_profile and admin_profile.photo:
                return admin_profile.photo
        return self.foto

    def __str__(self):
        return f"{self.nama_pelanggan} - {self.rating}/5"


class FooterPayment(models.Model):
    footer = models.ForeignKey(
        FooterSetting, on_delete=models.CASCADE, related_name="payments"
    )
    nama = models.CharField(max_length=40)
    ikon = models.ImageField(upload_to=rename_footer_payment_icon)
    urutan = models.PositiveIntegerField(default=0)
    aktif = models.BooleanField(default=True)

    class Meta:
        ordering = ["urutan", "nama"]
        verbose_name = "Ikon pembayaran footer"
        verbose_name_plural = "Ikon pembayaran footer"

    def __str__(self):
        return self.nama


class KategoriArtikel(models.Model):
    nama_category = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="Nama kategori",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        default=default_article_category_slug,
        verbose_name="Slug",
    )
    status_category = models.BooleanField(
        default=True,
        verbose_name="Kategori aktif",
    )

    class Meta:
        ordering = ["nama_category"]
        verbose_name = "Kategori artikel"
        verbose_name_plural = "Kategori artikel"

    def __str__(self):
        return self.nama_category


class MitraDeepublish(models.Model):
    nama = models.CharField(max_length=120, verbose_name="Nama mitra")
    gambar = models.ImageField(
        upload_to=rename_mitra_deepublish_image,
        verbose_name="Logo mitra",
    )
    aktif = models.BooleanField(default=True, verbose_name="Tampilkan")
    urutan = models.PositiveIntegerField(default=0, verbose_name="Urutan")

    class Meta:
        ordering = ["urutan", "nama"]
        verbose_name = "Mitra Losari Computer"
        verbose_name_plural = "Mitra Losari Computer"

    def __str__(self):
        return self.nama


class Artikel(models.Model):
    title_articles = models.CharField(
        max_length=200,
        verbose_name="Judul artikel",
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        default=default_article_slug,
    )
    desc_seo = models.CharField(
        max_length=300,
        verbose_name="Deskripsi SEO",
        help_text="Ringkasan singkat yang tampil di kartu artikel dan mesin pencari.",
    )
    category = models.ForeignKey(
        KategoriArtikel,
        on_delete=models.PROTECT,
        related_name="artikel",
        verbose_name="Kategori berita",
        help_text="Pilih kategori artikel yang aktif.",
    )
    content = models.TextField(verbose_name="Isi artikel")
    authors = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Penulis",
        help_text="Ketik nama penulis secara bebas.",
    )
    images = models.ImageField(
        upload_to=rename_article_image,
        null=True,
        blank=True,
        verbose_name="Gambar artikel",
    )
    published = models.BooleanField(
        default=True,
        verbose_name="Tampilkan di website",
    )
    views = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Jumlah dilihat",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"
        indexes = [
            models.Index(fields=["published", "-created_at"]),
        ]

    def __str__(self):
        return self.title_articles

    @property
    def character_count(self):
        return len(self.content or "")


def rename_blog_user_image(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"{instance.slug or 'blog'}-{uuid.uuid4().hex[:8]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("blog-pengguna", filename)


class BlogPengguna(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blog_pengguna",
        verbose_name="Penulis",
    )
    title = models.CharField(max_length=200, verbose_name="Judul blog")
    slug = models.SlugField(
        max_length=220,
        unique=True,
        default=default_article_slug,
    )
    summary = models.CharField(max_length=300, verbose_name="Ringkasan")
    content = models.TextField(verbose_name="Isi blog")
    image = models.ImageField(
        upload_to=rename_blog_user_image,
        null=True,
        blank=True,
        verbose_name="Gambar blog",
    )
    published = models.BooleanField(
        default=True,
        verbose_name="Tampilkan di website",
    )
    views = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blog pengguna"
        verbose_name_plural = "Blog pengguna"
        indexes = [models.Index(fields=["published", "-created_at"])]

    def __str__(self):
        return self.title

    @property
    def character_count(self):
        return len(self.content or "")


def rename_blog_inline_image(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"inline-{uuid.uuid4().hex[:12]}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("blog-pengguna", "inline", filename)


class BlogPenggunaImage(models.Model):
    blog = models.ForeignKey(
        BlogPengguna,
        on_delete=models.CASCADE,
        related_name="inline_images",
    )
    image = models.ImageField(upload_to=rename_blog_inline_image)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]


class ArtikelView(models.Model):
    artikel = models.ForeignKey(
        Artikel,
        on_delete=models.CASCADE,
        related_name="view_records",
    )
    visitor_key = models.CharField(max_length=100)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["artikel", "visitor_key"],
                name="unique_artikel_visitor",
            ),
        ]
        verbose_name = "Kunjungan artikel"
        verbose_name_plural = "Kunjungan artikel"


class UserAdmin(models.Model):
    username = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        to_field="username",
        primary_key=True,
        related_name="admin_profile",
    )
    nama_panggilan = models.CharField(max_length=150, blank=True, default="")
    telp = models.CharField(max_length=15)
    gender = models.CharField(
        max_length=15,
        choices=[
            ("Laki-laki", "Laki-laki"),
            ("Perempuan", "Perempuan"),
        ],
    )
    photo = models.ImageField(upload_to=rename_photo_admin)

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = UserAdmin.objects.filter(pk=self.pk).first()
            if (
                old_instance
                and old_instance.photo
                and old_instance.photo != self.photo
            ):
                old_instance.photo.delete(save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.username)


class Produk(models.Model):
    KONDISI_CHOICES = [
        ("baru", "Baru"),
        ("second", "Second"),
        ("refurbished", "Refurbished"),
    ]

    nama = models.CharField(max_length=150, verbose_name="Nama produk")
    slug = models.SlugField(
        max_length=170, unique=True, default=default_product_slug
    )
    kategori = models.ForeignKey(
        "Kategori",
        on_delete=models.PROTECT,
        related_name="produk",
        verbose_name="Kategori kebutuhan",
        null=True,
        blank=True,
    )
    merek = models.CharField(max_length=80, default="")
    deskripsi = models.TextField(blank=True)
    spesifikasi = models.JSONField(default=dict, blank=True)
    harga = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    diskon_persen = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Diskon (%)",
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        help_text="Isi 0 tanpa diskon. Diskon aktif harus antara 10 sampai 100%.",
    )
    stok = models.PositiveIntegerField(default=0)
    kondisi = models.CharField(
        max_length=20, choices=KONDISI_CHOICES, default="second"
    )
    gambar = models.ImageField(
        upload_to="produk/", null=True, blank=True
    )
    unggulan = models.BooleanField(default=False)
    aktif = models.BooleanField(default=True)
    dibuat_pada = models.DateTimeField(default=timezone.now)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-unggulan", "-dibuat_pada"]
        indexes = [
            models.Index(fields=["aktif", "kategori"]),
            models.Index(fields=["merek"]),
        ]

    def __str__(self):
        return f"{self.merek} {self.nama}"

    def clean(self):
        super().clean()
        if Decimal("0") < self.diskon_persen < Decimal("10"):
            raise ValidationError(
                {"diskon_persen": "Diskon aktif harus antara 10 sampai 100%."}
            )

    @property
    def harga_rupiah(self):
        return f"Rp{self.harga:,.0f}".replace(",", ".")

    @property
    def harga_diskon(self):
        potongan = self.harga * self.diskon_persen / Decimal("100")
        return (self.harga - potongan).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def harga_aktif(self):
        return self.harga_diskon if self.diskon_persen else self.harga

    @property
    def harga_aktif_rupiah(self):
        return f"Rp{self.harga_aktif:,.0f}".replace(",", ".")

    @property
    def memiliki_diskon(self):
        return self.diskon_persen >= Decimal("10")

    @property
    def tersedia(self):
        return self.aktif and self.stok > 0


def rename_product_gallery_image(instance, filename):
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    filename = f"{instance.produk.slug}-{instance.tipe}"
    if extension:
        filename = f"{filename}.{extension}"
    return os.path.join("produk", "galeri", filename)


class ProdukGambar(models.Model):
    TIPE_CHOICES = [
        ("depan", "Tampak depan"),
        ("keyboard", "Keyboard & port"),
        ("panel", "Panel & layar"),
        ("cek", "30-titik cek"),
        ("lainnya", "Gambar lainnya"),
    ]

    produk = models.ForeignKey(
        Produk,
        on_delete=models.CASCADE,
        related_name="galeri",
    )
    tipe = models.CharField(
        max_length=20,
        choices=TIPE_CHOICES,
        default="depan",
    )
    gambar = models.ImageField(upload_to=rename_product_gallery_image)
    urutan = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["urutan", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["produk", "tipe"],
                name="unique_produk_gambar_tipe",
            ),
        ]
        verbose_name = "Gambar produk"
        verbose_name_plural = "Gambar produk"

    def __str__(self):
        return f"{self.produk} - {self.get_tipe_display()}"


class ProdukKeunggulan(models.Model):
    IKON_CHOICES = [
        ("shield", "Perisai"),
        ("star", "Bintang"),
        ("gift", "Hadiah"),
        ("box", "Kotak"),
        ("check", "Centang"),
    ]
    WARNA_CHOICES = [
        ("green", "Hijau"),
        ("blue", "Biru"),
        ("yellow", "Kuning"),
        ("purple", "Ungu"),
    ]

    produk = models.ForeignKey(
        Produk,
        on_delete=models.CASCADE,
        related_name="keunggulan",
    )
    judul = models.CharField(max_length=100)
    deskripsi = models.CharField(max_length=180)
    ikon = models.CharField(
        max_length=15,
        choices=IKON_CHOICES,
        default="check",
    )
    warna = models.CharField(
        max_length=15,
        choices=WARNA_CHOICES,
        default="green",
    )
    urutan = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["urutan", "id"]
        verbose_name = "Keunggulan produk"
        verbose_name_plural = "Keunggulan produk"

    def __str__(self):
        return f"{self.produk} - {self.judul}"


class Kategori(models.Model):
    nama = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    deskripsi = models.TextField(blank=True)
    ikon = models.CharField(max_length=10, default="💻")
    aktif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nama"]
        verbose_name = "Kategori kebutuhan"
        verbose_name_plural = "Kategori kebutuhan"

    def __str__(self):
        return self.nama


class Pesanan(models.Model):
    STATUS_CHOICES = [
        ("menunggu", "Menunggu pembayaran"),
        ("dibayar", "Sudah dibayar"),
        ("diproses", "Diproses"),
        ("dikirim", "Dikirim"),
        ("selesai", "Selesai"),
        ("dibatalkan", "Dibatalkan"),
    ]

    nomor = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    pengguna = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="pesanan"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="menunggu"
    )
    alamat_pengiriman = models.TextField()
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return f"Pesanan {str(self.nomor)[:8].upper()}"

    def hitung_total(self):
        return sum(
            (item.subtotal for item in self.item.all()), 0
        )


class ItemPesanan(models.Model):
    pesanan = models.ForeignKey(
        Pesanan, on_delete=models.CASCADE, related_name="item"
    )
    produk = models.ForeignKey(Produk, on_delete=models.PROTECT)
    nama_produk = models.CharField(max_length=150)
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=2)
    jumlah = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Item pesanan"
        verbose_name_plural = "Item pesanan"

    @property
    def subtotal(self):
        return self.harga_satuan * self.jumlah

    def save(self, *args, **kwargs):
        if not self.nama_produk:
            self.nama_produk = self.produk.nama
        if not self.harga_satuan:
            self.harga_satuan = self.produk.harga_aktif
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nama
