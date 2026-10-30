from django import forms

from .models import Provinsi, UserAdmin


class formProfile(forms.ModelForm):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    alamat = forms.CharField(
        label="Alamat",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Alamat lengkap",
            }
        ),
    )
    provinsi_anggota = forms.ModelChoiceField(
        label="Provinsi",
        queryset=Provinsi.objects.filter(aktif=True).order_by("nama_provinsi"),
        empty_label="-- Pilih provinsi --",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.member = kwargs.pop("member", None)
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.initial["email"] = self.user.email
        if self.member is not None:
            self.initial["alamat"] = self.member.alamat
            self.initial["provinsi_anggota"] = self.member.provinsi_anggota
        self.fields["photo"].required = False

    class Meta:
        model = UserAdmin
        fields = [
            "nama_panggilan",
            "email",
            "telp",
            "gender",
            "alamat",
            "provinsi_anggota",
            "photo",
        ]
        widgets = {
            "gender": forms.Select(
                choices=[
                    ("Laki-laki", "Laki-laki"),
                    ("Perempuan", "Perempuan"),
                ],
                attrs={"class": "form-control"},
            ),
            "telp": forms.NumberInput(
                attrs={"class": "form-control"},
            ),
            "photo": forms.FileInput(
                attrs={"class": "form-control"},
            ),
        }
