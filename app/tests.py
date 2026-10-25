from django.test import TestCase
from django.urls import reverse

from .models import Kategori, Produk


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
