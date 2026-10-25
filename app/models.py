import os
import uuid

from django.contrib.auth.models import User
from django.db import models
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
    jafung = models.CharField(max_length=100, null=True, blank=True)
    nupk = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="NUPK",
    )
    bidang_keahlian = models.CharField(max_length=100, null=True, blank=True)
    link_sinta = models.URLField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Link Sinta",
    )
    link_scopus = models.URLField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Link Scopus",
    )
    link_google_scholar = models.URLField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Link Google Scholar",
    )
    link_orcid = models.URLField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Link ORCID",
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


class UserAdmin(models.Model):
    username = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        to_field="username",
        primary_key=True,
        related_name="admin_profile",
    )
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
            old_instance = UserAdmin.objects.get(pk=self.pk)
            if old_instance.photo and old_instance.photo != self.photo:
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

    @property
    def tersedia(self):
        return self.aktif and self.stok > 0


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
            self.harga_satuan = self.produk.harga
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nama
