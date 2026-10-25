from django.urls import path
from core import views as core_views

from . import views
from . import views_admin
from . import views_pengguna

urlpatterns = [
    path("", views.home, name="index"),
    path("produk/<slug:slug>/", views.product_detail, name="product_detail"),
    path("dashboard/", views.index, name="dashboard"),
    path("login/", core_views.loginView, name="login"),
    path("register/", core_views.registerView, name="register"),
    path("logout/", core_views.LogoutView, name="logout"),
    path(
        "profile/admin/",
        views_admin.profile_admin,
        name="profile_admin",
    ),
    path(
        "profile/pengguna/",
        views_pengguna.profile_pengguna,
        name="profile_pengguna",
    ),
]