import app.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0021_testimoni_pengguna"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="KategoriArtikel",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("nama_category", models.CharField(max_length=80, unique=True, verbose_name="Nama kategori")),
                        ("slug", models.SlugField(default=app.models.default_article_category_slug, max_length=100, unique=True, verbose_name="Slug")),
                        ("status_category", models.BooleanField(default=True, verbose_name="Kategori aktif")),
                    ],
                    options={
                        "ordering": ["nama_category"],
                        "verbose_name": "Kategori artikel",
                        "verbose_name_plural": "Kategori artikel",
                    },
                ),
                migrations.CreateModel(
                    name="MitraDeepublish",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("nama", models.CharField(max_length=120, verbose_name="Nama mitra")),
                        ("gambar", models.ImageField(upload_to=app.models.rename_mitra_deepublish_image, verbose_name="Logo mitra")),
                        ("aktif", models.BooleanField(default=True, verbose_name="Tampilkan")),
                        ("urutan", models.PositiveIntegerField(default=0, verbose_name="Urutan")),
                    ],
                    options={
                        "ordering": ["urutan", "nama"],
                        "verbose_name": "Mitra Deepublish",
                        "verbose_name_plural": "Mitra Deepublish",
                    },
                ),
                migrations.AlterField(
                    model_name="artikel",
                    name="category",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="artikel",
                        to="app.kategoriartikel",
                        verbose_name="Kategori berita",
                        help_text="Pilih kategori artikel yang aktif.",
                    ),
                ),
            ],
            database_operations=[
                migrations.CreateModel(
                    name="MitraDeepublish",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("nama", models.CharField(max_length=120, verbose_name="Nama mitra")),
                        ("gambar", models.ImageField(upload_to=app.models.rename_mitra_deepublish_image, verbose_name="Logo mitra")),
                        ("aktif", models.BooleanField(default=True, verbose_name="Tampilkan")),
                        ("urutan", models.PositiveIntegerField(default=0, verbose_name="Urutan")),
                    ],
                    options={
                        "ordering": ["urutan", "nama"],
                        "verbose_name": "Mitra Deepublish",
                        "verbose_name_plural": "Mitra Deepublish",
                    },
                ),
            ],
        ),
    ]
