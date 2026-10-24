from django.http import HttpResponse


def home(request):
    return HttpResponse(
        "<h1>Thesis Store</h1>"
        "<p>Aplikasi berhasil berjalan.</p>"
        '<p><a href="/admin/">Buka Django Admin</a></p>'
    )
