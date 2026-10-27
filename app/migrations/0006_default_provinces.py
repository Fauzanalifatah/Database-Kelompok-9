from django.db import migrations


def create_default_provinces(apps, schema_editor):
    Provinsi = apps.get_model("app", "Provinsi")
    provinces = [
        "Aceh",
        "Sumatera Utara",
        "Sumatera Barat",
        "Riau",
        "Jambi",
        "Sumatera Selatan",
        "Bengkulu",
        "Lampung",
        "Kepulauan Bangka Belitung",
        "Kepulauan Riau",
        "DKI Jakarta",
        "Jawa Barat",
        "Jawa Tengah",
        "Daerah Istimewa Yogyakarta",
        "Jawa Timur",
        "Banten",
        "Bali",
        "Nusa Tenggara Barat",
        "Nusa Tenggara Timur",
        "Kalimantan Barat",
        "Kalimantan Tengah",
        "Kalimantan Selatan",
        "Kalimantan Timur",
        "Kalimantan Utara",
        "Sulawesi Utara",
        "Sulawesi Tengah",
        "Sulawesi Selatan",
        "Sulawesi Tenggara",
        "Gorontalo",
        "Sulawesi Barat",
        "Maluku",
        "Maluku Utara",
        "Papua",
        "Papua Barat",
        "Papua Selatan",
        "Papua Tengah",
        "Papua Pegunungan",
        "Papua Barat Daya",
    ]
    for nama_provinsi in provinces:
        Provinsi.objects.get_or_create(
            nama_provinsi=nama_provinsi,
            defaults={"aktif": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0005_business_catalog"),
    ]

    operations = [
        migrations.RunPython(create_default_provinces, migrations.RunPython.noop),
    ]
