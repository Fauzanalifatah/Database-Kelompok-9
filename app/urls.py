from django.urls import path
from . import views

urlpatterns = []

urlpatterns = [
    path("", views.home, name="home"),
]