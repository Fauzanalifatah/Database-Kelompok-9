from django.db import migrations


def create_business_catalog(apps, schema_editor):
    Kategori = apps.get_model("app", "Kategori")
    Produk = apps.get_model("app", "Produk")

    categories = {
        "office-kuliah": (
            "Office & Kuliah",
            "Laptop praktis untuk tugas, kuliah, pekerjaan kantor, dan aktivitas harian.",
            "📚",
        ),
        "desain-kreatif": (
            "Desain & Kreatif",
            "Perangkat bertenaga untuk desain grafis, editing, dan produksi konten.",
            "🎨",
        ),
        "gaming": (
            "Gaming",
            "Laptop dengan performa tinggi untuk gaming dan pekerjaan berat.",
            "🎮",
        ),
        "bisnis": (
            "Bisnis",
            "Notebook profesional untuk mobilitas dan produktivitas kerja.",
            "💼",
        ),
        "aksesoris-pos": (
            "Aksesoris & POS",
            "Perlengkapan komputer, gaming, dan kebutuhan point of sale.",
            "🖨️",
        ),
        "smartphone-gadget": (
            "Smartphone & Gadget",
            "Smartphone dan gadget pilihan untuk kebutuhan komunikasi dan hiburan.",
            "📱",
        ),
        "cctv-smart-security": (
            "CCTV & Smart Security",
            "Perangkat keamanan pintar untuk rumah, toko, dan kantor.",
            "📹",
        ),
    }

    category_objects = {}
    for slug, (nama, deskripsi, ikon) in categories.items():
        category_objects[slug], _ = Kategori.objects.get_or_create(
            slug=slug,
            defaults={
                "nama": nama,
                "deskripsi": deskripsi,
                "ikon": ikon,
            },
        )

    products = [
        {
            "slug": "lenovo-thinkpad-t490",
            "nama": "ThinkPad T490",
            "merek": "Lenovo",
            "kategori": "office-kuliah",
            "deskripsi": "Tangkas untuk kerja, kuliah, coding, dan multitasking harian.",
            "spesifikasi": {"prosesor": "Intel Core i5", "ram": "16GB", "penyimpanan": "SSD 512GB", "layar": '14" FHD'},
            "harga": 4250000,
            "stok": 1,
            "unggulan": True,
        },
        {
            "slug": "asus-tuf-gaming-a15",
            "nama": "TUF Gaming A15",
            "merek": "ASUS",
            "kategori": "gaming",
            "deskripsi": "Performa gaming dan produktivitas dengan pendinginan tangguh.",
            "spesifikasi": {"prosesor": "Ryzen 5 7535HS", "ram": "8GB DDR5", "penyimpanan": "SSD 512GB", "layar": '15.6" FHD'},
            "harga": 8900000,
            "stok": 1,
            "unggulan": True,
        },
        {
            "slug": "hp-elitebook-840-g7",
            "nama": "EliteBook 840 G7",
            "merek": "HP",
            "kategori": "bisnis",
            "deskripsi": "Tipis, profesional, dan nyaman untuk mobilitas kantor.",
            "spesifikasi": {"prosesor": "Core i5 Gen 10", "ram": "16GB", "penyimpanan": "SSD 512GB", "layar": '14" FHD'},
            "harga": 5150000,
            "stok": 1,
            "unggulan": True,
        },
        {
            "slug": "macbook-air-m1",
            "nama": "MacBook Air M1",
            "merek": "Apple",
            "kategori": "desain-kreatif",
            "deskripsi": "Ringan dan bertenaga untuk desain, konten, dan kerja mobile.",
            "spesifikasi": {"prosesor": "Apple M1", "ram": "8GB", "penyimpanan": "SSD 256GB", "layar": '13.3" Retina'},
            "harga": 11900000,
            "stok": 1,
            "unggulan": True,
        },
        {
            "slug": "asus-vivobook-14",
            "nama": "VivoBook 14",
            "merek": "ASUS",
            "kategori": "office-kuliah",
            "deskripsi": "Praktis untuk tugas kampus, presentasi, meeting, dan browsing.",
            "spesifikasi": {"prosesor": "Core i5", "ram": "8GB", "penyimpanan": "SSD 512GB", "layar": '14" FHD'},
            "harga": 4650000,
            "stok": 1,
        },
        {
            "slug": "lenovo-thinkpad-t14-gen-1",
            "nama": "ThinkPad T14 Gen 1",
            "merek": "Lenovo",
            "kategori": "bisnis",
            "deskripsi": "Keyboard nyaman dan build kokoh untuk kerja intensif setiap hari.",
            "spesifikasi": {"prosesor": "Ryzen 5 Pro", "ram": "16GB", "penyimpanan": "SSD 512GB", "layar": '14" FHD'},
            "harga": 6350000,
            "stok": 1,
        },
        {
            "slug": "acer-nitro-5",
            "nama": "Nitro 5",
            "merek": "Acer",
            "kategori": "gaming",
            "deskripsi": "Pilihan gaming budget dengan ruang upgrade yang luas.",
            "spesifikasi": {"prosesor": "Core i5 Gen 11", "ram": "8GB", "penyimpanan": "SSD 512GB", "layar": '15.6" FHD'},
            "harga": 7350000,
            "stok": 1,
        },
        {
            "slug": "asus-vivobook-pro-14",
            "nama": "Vivobook Pro 14",
            "merek": "ASUS",
            "kategori": "desain-kreatif",
            "deskripsi": "Untuk editing, desain grafis, dan workflow kreatif lebih serius.",
            "spesifikasi": {"prosesor": "Ryzen 7", "ram": "16GB", "penyimpanan": "SSD 1TB", "layar": '14" 2.8K'},
            "harga": 10900000,
            "stok": 1,
        },
        {
            "slug": "thermal-printer-80mm",
            "nama": "Thermal Printer 80mm iWare IW-J300H",
            "merek": "iWare",
            "kategori": "aksesoris-pos",
            "deskripsi": "Printer kasir dengan koneksi USB, LAN, Serial, Bluetooth, dan WiFi.",
            "spesifikasi": {"koneksi": "USB + LAN, Bluetooth + WiFi", "fitur": "Auto Cutter", "kecepatan": "300mm/s"},
            "harga": 1725000,
            "stok": 5,
            "kondisi": "baru",
        },
        {
            "slug": "rexus-gamepad-gx500v2",
            "nama": "Gamepad GX-500-V2",
            "merek": "Rexus",
            "kategori": "aksesoris-pos",
            "deskripsi": "Wireless RGB gamepad 2.4GHz dengan dual vibration.",
            "spesifikasi": {"koneksi": "Wireless 2.4GHz", "fitur": "RGB LED, Dual Vibration", "warna": "Putih & Navy"},
            "harga": 575000,
            "stok": 5,
            "kondisi": "baru",
        },
        {
            "slug": "iphone-11-second",
            "nama": "iPhone 11 128GB",
            "merek": "Apple",
            "kategori": "smartphone-gadget",
            "deskripsi": "Second mulus 95-98%, Face ID normal, True Tone aktif, battery health 87% original.",
            "spesifikasi": {"prosesor": "A13 Bionic", "ram": "4GB", "penyimpanan": "128GB", "layar": '6.1" Liquid Retina'},
            "harga": 4200000,
            "stok": 1,
        },
        {
            "slug": "ezviz-c6n-cctv",
            "nama": "C6N 1080p Smart WiFi PTZ Camera",
            "merek": "Ezviz",
            "kategori": "cctv-smart-security",
            "deskripsi": "CCTV 360° Full HD dengan smart tracking, night vision 10m, dan two-way audio.",
            "spesifikasi": {"resolusi": "Full HD 1080p", "gerak": "Pan/Tilt 360°", "night_vision": "10m", "audio": "Two-Way Audio"},
            "harga": 395000,
            "stok": 5,
            "kondisi": "baru",
        },
    ]

    for product in products:
        values = product.copy()
        values["kategori"] = category_objects[values["kategori"]]
        Produk.objects.get_or_create(slug=values.pop("slug"), defaults=values)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0004_default_categories"),
    ]

    operations = [
        migrations.RunPython(create_business_catalog, migrations.RunPython.noop),
    ]
