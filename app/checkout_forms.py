from django import forms
from .models import Provinsi


class CheckoutForm(forms.Form):
    nama = forms.CharField(
        label="Nama Lengkap Penerima",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "name",
                "placeholder": "Contoh: Fauzan Alifatah",
            }
        ),
    )
    email = forms.EmailField(
        label="Alamat Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "nama@email.com (untuk nota & konfirmasi)",
            }
        ),
    )
    telp = forms.CharField(
        label="Nomor WhatsApp / HP",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "placeholder": "Contoh: 081234567890",
            }
        ),
    )
    provinsi = forms.ModelChoiceField(
        queryset=Provinsi.objects.filter(aktif=True),
        label="Provinsi",
        empty_label="— Pilih Provinsi —",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )
    kota = forms.CharField(
        label="Kota / Kabupaten",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Contoh: Kota Makassar",
                "autocomplete": "address-level2",
            }
        ),
    )
    kecamatan = forms.CharField(
        label="Kecamatan",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Contoh: Rappocini",
                "autocomplete": "address-level3",
            }
        ),
    )
    alamat = forms.CharField(
        label="Alamat Lengkap (Jalan, RT/RW, No. Rumah)",
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "autocomplete": "street-address",
                "placeholder": "Tuliskan nama jalan, RT/RW, nomor rumah, kelurahan, patokan",
            }
        ),
    )
    jumlah = forms.IntegerField(
        label="Jumlah",
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={"min": 1, "max": 10, "class": "qty-number-input"}),
    )
