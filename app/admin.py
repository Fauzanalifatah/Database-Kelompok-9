from django.contrib import admin

from .models import (
    Artikel,
    KategoriArtikel,
    MitraDeepublish,
    AboutSetting,
    FooterSetting,
    FooterPayment,
    FooterSocial,
    ItemPesanan,
    Kategori,
    Pesanan,
    Produk,
    ProdukGambar,
    ProdukKeunggulan,
    Provinsi,
    UserAdmin,
    UserPengguna,
    Testimoni,
)


@admin.register(AboutSetting)
class AboutSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identitas bisnis", {"fields": ("logo", "judul", "tagline", "deskripsi")}),
        ("Perjalanan bisnis", {"fields": ("sejarah",)}),
        ("Profil CEO", {"fields": ("ceo_nama", "ceo_jabatan", "ceo_foto")}),
        ("Arah bisnis", {"fields": ("visi", "misi")}),
    )


@admin.register(Testimoni)
class TestimoniAdmin(admin.ModelAdmin):
    list_display = (
        "nama_pelanggan",
        "pengguna",
        "produk",
        "rating",
        "aktif",
        "dibuat_pada",
    )
    list_filter = ("aktif", "rating")
    search_fields = ("nama_pelanggan", "kota", "produk", "pesan")


class FooterSocialInline(admin.TabularInline):
    model = FooterSocial
    extra = 1


class FooterPaymentInline(admin.TabularInline):
    model = FooterPayment
    extra = 0


@admin.register(FooterSetting)
class FooterSettingAdmin(admin.ModelAdmin):
    inlines = [FooterSocialInline, FooterPaymentInline]


@admin.register(Artikel)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = (
        "title_articles",
        "category",
        "authors",
        "published",
        "views",
        "created_at",
        "updated_at",
    )
    list_filter = ("category", "published", "created_at", "updated_at")
    search_fields = (
        "title_articles",
        "category__nama_category",
        "desc_seo",
        "content",
    )
    prepopulated_fields = {"slug": ("title_articles",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(KategoriArtikel)
class KategoriArtikelAdmin(admin.ModelAdmin):
    list_display = ("nama_category", "slug", "status_category")
    list_filter = ("status_category",)
    search_fields = ("nama_category",)
    prepopulated_fields = {"slug": ("nama_category",)}


@admin.register(MitraDeepublish)
class MitraDeepublishAdmin(admin.ModelAdmin):
    list_display = ("nama", "aktif", "urutan")
    list_filter = ("aktif",)
    search_fields = ("nama",)
    list_editable = ("aktif", "urutan")
    fields = ("nama", "gambar")


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ("nama", "slug", "aktif")
    list_filter = ("aktif",)
    prepopulated_fields = {"slug": ("nama",)}


class ProdukGambarInline(admin.TabularInline):
    model = ProdukGambar
    extra = 1
    fields = ("tipe", "gambar", "urutan")


class ProdukKeunggulanInline(admin.TabularInline):
    model = ProdukKeunggulan
    extra = 4
    fields = ("judul", "deskripsi", "ikon", "warna", "urutan")


@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = (
        "nama",
        "merek",
        "kategori",
        "harga",
        "diskon_persen",
        "harga_aktif_admin",
        "stok",
        "aktif",
    )
    list_filter = ("kategori", "kondisi", "aktif", "unggulan")
    search_fields = ("nama", "merek")
    prepopulated_fields = {"slug": ("nama",)}
    inlines = [ProdukGambarInline, ProdukKeunggulanInline]

    @admin.display(description="Harga setelah diskon")
    def harga_aktif_admin(self, obj):
        return obj.harga_aktif


class ItemPesananInline(admin.TabularInline):
    model = ItemPesanan
    extra = 0


@admin.register(Pesanan)
class PesananAdmin(admin.ModelAdmin):
    list_display = ("nomor", "pengguna", "status", "total", "dibuat_pada")
    list_filter = ("status", "dibuat_pada")
    search_fields = ("pengguna__username", "pengguna__email")
    inlines = [ItemPesananInline]


admin.site.register(Provinsi)
admin.site.register(UserAdmin)
admin.site.register(UserPengguna)
