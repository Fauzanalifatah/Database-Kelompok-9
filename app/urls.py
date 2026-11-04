from django.urls import path
from core import views as core_views

from . import views
from . import views_pengguna

urlpatterns = [
    path("", views.home, name="index"),
    path("shop/", views.shop, name="shop"),
    path("produk/<slug:slug>/", views.product_detail, name="product_detail"),
    path("artikel/", views.article_list, name="article_list"),
    path(
        "artikel/<slug:slug>/",
        views.article_detail,
        name="article_detail",
    ),
    path("dashboard/", views.index, name="dashboard"),
    path("login/", core_views.loginView, name="login"),
    path("register/", core_views.registerView, name="register"),
    path("logout/", core_views.LogoutView, name="logout"),
    path(
        "profile/pengguna/",
        views_pengguna.profile_pengguna,
        name="profile_pengguna",
    ),
]