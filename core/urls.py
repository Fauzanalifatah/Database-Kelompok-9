"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from app import views
from . import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("app/", include(("app.urls", "app"), namespace="app")),
    path("login/", core_views.loginView, name="login"),
    path("register/", core_views.registerView, name="register"),
    path("logout/", core_views.LogoutView, name="logout"),
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("artikel/", views.article_list, name="article_list"),
    path("artikel/<slug:slug>/", views.article_detail, name="article_detail"),
    path("blog/", views.blog_pengguna_list, name="blog_pengguna_list"),
    path(
        "blog/<slug:slug>/",
        views.blog_pengguna_detail,
        name="blog_pengguna_detail",
    ),
    path("tentang-kami/", views.about, name="about"),
    path("testimoni/", views.testimonials, name="testimonials"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)