import os
import uuid

from django.conf import settings
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
            old_instance = UserPengguna.objects.get(pk=self.pk)
            if old_instance.photo and old_instance.photo != self.photo:
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
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama
