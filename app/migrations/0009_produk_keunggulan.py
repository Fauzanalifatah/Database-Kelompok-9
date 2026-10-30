from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0008_produk_gambar"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProdukKeunggulan",
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
                ("judul", models.CharField(max_length=100)),
                ("deskripsi", models.CharField(max_length=180)),
                (
                    "ikon",
                    models.CharField(
                        choices=[
                            ("shield", "Perisai"),
                            ("star", "Bintang"),
                            ("gift", "Hadiah"),
                            ("box", "Kotak"),
                            ("check", "Centang"),
                        ],
                        default="check",
                        max_length=15,
                    ),
                ),
                (
                    "warna",
                    models.CharField(
                        choices=[
                            ("green", "Hijau"),
                            ("blue", "Biru"),
                            ("yellow", "Kuning"),
                            ("purple", "Ungu"),
                        ],
                        default="green",
                        max_length=15,
                    ),
                ),
                ("urutan", models.PositiveIntegerField(default=0)),
                (
                    "produk",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="keunggulan",
                        to="app.produk",
                    ),
                ),
            ],
            options={
                "verbose_name": "Keunggulan produk",
                "verbose_name_plural": "Keunggulan produk",
                "ordering": ["urutan", "id"],
            },
        ),
    ]
