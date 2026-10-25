from django import forms

from .models import Provinsi, UserPengguna


class formProfile(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=[
            ("", "-- Pilih Jenis Kelamin --"),
            ("Laki-laki", "Laki-laki"),
            ("Perempuan", "Perempuan"),
        ],
        widget=forms.Select(
            attrs={"class": "form-control", "id": "id_gender"}
        ),
        required=True,
    )

    provinsi_anggota = forms.ModelChoiceField(
        queryset=Provinsi.objects.filter(aktif=True).order_by("nama_provinsi"),
        empty_label="-- Pilih provinsi --",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "id": "id_provinsi_anggota",
            }
        ),
        required=True,
    )

    class Meta:
        model = UserPengguna
        fields = [
            "telp",
            "gender",
            "alamat",
            "provinsi_anggota",
            "photo",
        ]
        widgets = {
            "telp": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contoh: 08123456789",
                }
            ),
            "alamat": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Alamat lengkap untuk pengiriman",
                }
            ),
            "photo": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }
