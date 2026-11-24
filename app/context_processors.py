from .models import FooterSetting, Kategori, AboutSetting, RunningText
from .cart import get_cart_total_items


def storefront_footer(request):
    try:
        running_texts = list(RunningText.objects.filter(aktif=True).order_by("urutan", "id"))
    except Exception:
        running_texts = []

    if not running_texts:
        running_texts = [
            {"teks": "Garansi toko"},
            {"teks": "Siap kirim ke seluruh kota"},
            {"teks": "Unit teruji"},
            {"teks": "Laptop second berkualitas"},
        ]

    return {
        "footer_categories": Kategori.objects.filter(aktif=True).only(
            "nama", "slug"
        )[:6],
        "footer_setting": FooterSetting.objects.first(),
        "about_setting": AboutSetting.objects.first(),
        "cart_total_items": get_cart_total_items(request),
        "running_texts": running_texts,
    }
