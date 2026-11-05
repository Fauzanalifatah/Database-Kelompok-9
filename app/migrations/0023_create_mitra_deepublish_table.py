import app.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0022_kategoriartikel_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[],
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
