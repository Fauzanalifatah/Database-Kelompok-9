from django.db import migrations


def create_default_categories(apps, schema_editor):
    Kategori = apps.get_model("app", "Kategori")
    categories = [
        (
            "Office & Kuliah",
            "office-kuliah",
            "Ringan, nyaman, dan siap untuk aktivitas harian.",
            "📚",
        ),
        (
            "Desain & Kreatif",
            "desain-kreatif",
            "Performa lebih untuk editing, desain, dan produksi.",
            "🎨",
        ),
        (
            "Gaming",
            "gaming",
            "Performa tinggi untuk game dan pekerjaan berat.",
            "🎮",
        ),
        (
            "Bisnis",
            "bisnis",
            "Notebook profesional untuk mobilitas dan produktivitas.",
            "💼",
        ),
    ]
    for nama, slug, deskripsi, ikon in categories:
        Kategori.objects.get_or_create(
            slug=slug,
            defaults={"nama": nama, "deskripsi": deskripsi, "ikon": ikon},
        )


class Migration(migrations.Migration):
    dependencies = [("app", "0003_kategori_pesanan_alter_produk_options_produk_aktif_and_more")]

    operations = [migrations.RunPython(create_default_categories, migrations.RunPython.noop)]
