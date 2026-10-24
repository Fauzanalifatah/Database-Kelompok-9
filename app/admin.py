from django.contrib import admin

from .models import Produk, Provinsi, UserAdmin, UserPengguna


admin.site.register(Produk)
admin.site.register(Provinsi)
admin.site.register(UserAdmin)
admin.site.register(UserPengguna)
