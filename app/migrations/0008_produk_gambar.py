from django.db import migrations, models
import django.db.models.deletion

from app.models import rename_product_gallery_image


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0007_remove_unused_user_profile_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProdukGambar",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipe",
                    models.CharField(
                        choices=[
                            ("depan", "Tampak depan"),
                            ("keyboard", "Keyboard & port"),
                            ("panel", "Panel & layar"),
                            ("cek", "30-titik cek"),
                            ("lainnya", "Gambar lainnya"),
                        ],
                        default="depan",
                        max_length=20,
                    ),
                ),
                (
                    "gambar",
                    models.ImageField(upload_to=rename_product_gallery_image),
                ),
                ("urutan", models.PositiveIntegerField(default=0)),
                (
                    "produk",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="galeri",
                        to="app.produk",
                    ),
                ),
            ],
            options={
                "verbose_name": "Gambar produk",
                "verbose_name_plural": "Gambar produk",
                "ordering": ["urutan", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="produkgambar",
            constraint=models.UniqueConstraint(
                fields=("produk", "tipe"),
                name="unique_produk_gambar_tipe",
            ),
        ),
    ]
