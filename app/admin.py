from django.contrib import admin

from .models import (
    ItemPesanan,
    Kategori,
    Pesanan,
    Produk,
    ProdukGambar,
    ProdukKeunggulan,
    Provinsi,
    UserAdmin,
    UserPengguna,
)


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
