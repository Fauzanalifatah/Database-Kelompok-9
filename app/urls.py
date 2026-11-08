from django.urls import path
from core import views as core_views

from . import views
from . import views_pengguna

urlpatterns = [
    path("", views.home, name="index"),
    path("dashboard/produk/", views.produk_manager, name="produk_manager"),
    path("dashboard/produk/tambah/", views.produk_manager_form, name="produk_manager_add"),
    path("dashboard/produk/<int:pk>/edit/", views.produk_manager_form, name="produk_manager_edit"),
    path("dashboard/produk/<int:pk>/hapus/", views.produk_manager_delete, name="produk_manager_delete"),
    path("dashboard/artikel/", views.artikel_manager, name="artikel_manager"),
    path("dashboard/artikel/tambah/", views.artikel_manager_form, name="artikel_manager_add"),
    path("dashboard/artikel/<int:pk>/edit/", views.artikel_manager_form, name="artikel_manager_edit"),
    path("dashboard/artikel/<int:pk>/hapus/", views.artikel_manager_delete, name="artikel_manager_delete"),
    path("dashboard/footer/", views.footer_manager, name="footer_manager"),
    path("dashboard/tentang-kami/", views.about_manager, name="about_manager"),
    path("dashboard/mitra-deepublish/", views.mitra_manager, name="mitra_manager"),
    path("dashboard/mitra-deepublish/tambah/", views.mitra_manager_form, name="mitra_manager_add"),
    path("dashboard/mitra-deepublish/<int:pk>/edit/", views.mitra_manager_form, name="mitra_manager_edit"),
    path("dashboard/mitra-deepublish/<int:pk>/hapus/", views.mitra_manager_delete, name="mitra_manager_delete"),
    path("dashboard/pelanggan/", views.pelanggan_manager, name="pelanggan_manager"),
    path("dashboard/pelanggan/<str:username>/edit/", views.pelanggan_manager_form, name="pelanggan_manager_edit"),
    path("dashboard/pesanan/", views.pesanan_manager, name="pesanan_manager"),
    path("dashboard/pesanan/<int:pk>/edit/", views.pesanan_manager_form, name="pesanan_manager_edit"),
    path("shop/", views.shop, name="shop"),
    path("produk/<slug:slug>/", views.product_detail, name="product_detail"),
    path("artikel/", views.article_list, name="article_list"),
    path("tentang-kami/", views.about, name="about"),
    path("testimoni/", views.testimonials, name="testimonials"),
    path(
        "artikel/<slug:slug>/",
        views.article_detail,
        name="article_detail",
    ),
    path("dashboard/", views.index, name="dashboard"),
    path("login/", core_views.loginView, name="login"),
    path("login/google/", core_views.google_login, name="google_login"),
    path(
        "login/google/callback/",
        core_views.google_callback,
        name="google_callback",
    ),
    path("register/", core_views.registerView, name="register"),
    path("logout/", core_views.LogoutView, name="logout"),
    path(
        "profile/pengguna/",
        views_pengguna.profile_pengguna,
        name="profile_pengguna",
    ),
    path("blog/pengguna/", views_pengguna.blog_pengguna, name="blog_pengguna"),
    path(
        "blog/pengguna/tulis/",
        views_pengguna.artikel_pengguna_form,
        name="artikel_pengguna_tulis",
    ),
    path(
        "blog/pengguna/<slug:slug>/edit/",
        views_pengguna.artikel_pengguna_form,
        name="artikel_pengguna_edit",
    ),
    path(
        "blog/pengguna/<slug:slug>/hapus/",
        views_pengguna.hapus_artikel_pengguna,
        name="artikel_pengguna_hapus",
    ),
    path("blog/", views.blog_pengguna_list, name="blog_pengguna_list"),
    path(
        "blog/<slug:slug>/",
        views.blog_pengguna_detail,
        name="blog_pengguna_detail",
    ),
]