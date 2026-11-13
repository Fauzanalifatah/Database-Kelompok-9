from .models import FooterSetting, Kategori
from .cart import get_cart_total_items


def storefront_footer(request):
    return {
        "footer_categories": Kategori.objects.filter(aktif=True).only(
            "nama", "slug"
        )[:6],
        "footer_setting": FooterSetting.objects.first(),
        "cart_total_items": get_cart_total_items(request),
    }
