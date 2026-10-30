from django import forms

from .models import Provinsi, UserPengguna


class formProfile(forms.ModelForm):
    nama = forms.CharField(
        label="Nama",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nama lengkap"}
        ),
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Alamat email"}
        ),
    )
    telp = forms.CharField(
        label="Nomor HP",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contoh: 08123456789",
            }
        ),
    )
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.initial["nama"] = self.user.first_name
            self.initial["email"] = self.user.email

    class Meta:
        model = UserPengguna
        fields = [
            "nama",
            "email",
            "telp",
            "gender",
            "alamat",
            "provinsi_anggota",
            "photo",
        ]
        widgets = {
            "alamat": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Alamat lengkap untuk pengiriman",
                }
            ),
            "photo": forms.FileInput(attrs={"accept": "image/*"}),
        }
