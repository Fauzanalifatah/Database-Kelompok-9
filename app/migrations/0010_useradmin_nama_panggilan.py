from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0009_produk_keunggulan"),
    ]

    operations = [
        migrations.AddField(
            model_name="useradmin",
            name="nama_panggilan",
            field=models.CharField(
                blank=True,
                default="",
                max_length=150,
            ),
        ),
    ]
