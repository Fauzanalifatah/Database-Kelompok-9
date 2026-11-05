from .models import FooterSetting, Kategori


def storefront_footer(request):
    return {
        "footer_categories": Kategori.objects.filter(aktif=True).only(
            "nama", "slug"
        )[:6],
        "footer_setting": FooterSetting.objects.first(),
    }
