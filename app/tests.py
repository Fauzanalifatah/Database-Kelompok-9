from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Kategori, Produk, UserPengguna


class StorefrontTests(TestCase):
    def setUp(self):
        self.category = Kategori.objects.create(
            nama="Kategori Uji",
            slug="kategori-uji",
            deskripsi="Laptop untuk aktivitas harian.",
        )
        self.product = Produk.objects.create(
            nama="ThinkPad T14",
            slug="thinkpad-t14",
            kategori=self.category,
            merek="Lenovo",
            harga=7500000,
            stok=3,
            spesifikasi={"RAM": "16 GB", "Penyimpanan": "512 GB SSD"},
        )

    def test_home_displays_active_product(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ThinkPad T14")

    def test_category_filter_and_product_detail(self):
        response = self.client.get(
            reverse("home"), {"kategori": self.category.slug}
        )
        detail = self.client.get(
            reverse("app:product_detail", args=[self.product.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "16 GB")

    def test_shop_formats_prices_without_template_error(self):
        response = self.client.get(reverse("shop"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rp7.500.000")

    def test_discount_calculates_final_price(self):
        self.product.diskon_persen = 10
        self.product.full_clean()
        self.product.save()

        self.assertEqual(self.product.harga_diskon, 6750000)
        self.assertEqual(self.product.harga_aktif, 6750000)

    def test_active_discount_must_be_at_least_ten_percent(self):
        self.product.diskon_persen = 5

        with self.assertRaises(ValidationError):
            self.product.full_clean()


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pengguna",
            email="pengguna@example.com",
            password="Password123!",
        )

    def test_login_redirects_to_storefront_home(self):
        response = self.client.post(
            reverse("app:login"),
            {"email": "pengguna@example.com", "password": "Password123!"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_logs_user_in_and_redirects_to_storefront_home(self):
        response = self.client.post(
            reverse("app:register"),
            {
                "username": "pengguna-baru",
                "first_name": "Pengguna Baru",
                "email": "baru@example.com",
                "password": "Password123!",
                "password_confirmation": "Password123!",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.email, "baru@example.com")

    def test_regular_user_cannot_open_admin_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("app:dashboard"))

        self.assertRedirects(response, reverse("app:profile_pengguna"))
