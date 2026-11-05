from django import forms

from .models import (
    AboutSetting,
    FooterPayment,
    FooterSetting,
    FooterSocial,
    MitraDeepublish,
    Provinsi,
    Testimoni,
    UserAdmin,
)


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
            attrs={"class": "form-control", "placeholder": "Alamat lengkap"}
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
            "telp": forms.NumberInput(attrs={"class": "form-control"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
        }


class FooterSettingForm(forms.ModelForm):
    class Meta:
        model = FooterSetting
        fields = [
            "nama_toko",
            "deskripsi",
            "alamat",
            "jam_pelayanan",
            "email",
            "whatsapp",
        ]
        widgets = {
            "alamat": forms.Textarea(attrs={"rows": 3}),
            "deskripsi": forms.TextInput(),
        }


class FooterSocialForm(forms.ModelForm):
    url = forms.URLField(required=False)
    aktif = forms.BooleanField(required=False, initial=True)
    ikon = forms.ImageField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not cleaned_data.get("ikon"):
            self.add_error("ikon", "Unggah gambar ikon untuk sosial media ini.")
        return cleaned_data

    class Meta:
        model = FooterSocial
        fields = ["url", "ikon", "aktif"]
        widgets = {
            "ikon": forms.FileInput(attrs={"accept": "image/*"}),
        }


class FooterPaymentForm(forms.ModelForm):
    ikon = forms.ImageField(required=False)

    class Meta:
        model = FooterPayment
        fields = ["ikon", "aktif"]
        widgets = {
            "ikon": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not cleaned_data.get("ikon"):
            self.add_error("ikon", "Unggah gambar logo pembayaran.")
        return cleaned_data


class FooterSocialAddForm(FooterSocialForm):
    nama = forms.CharField(max_length=40, label="Nama platform")

    class Meta(FooterSocialForm.Meta):
        fields = ["nama", "url", "ikon", "aktif"]


class FooterPaymentAddForm(FooterPaymentForm):
    nama = forms.CharField(max_length=40, label="Nama pembayaran")

    class Meta(FooterPaymentForm.Meta):
        fields = ["nama", "ikon", "aktif"]


class AboutSettingForm(forms.ModelForm):
    class Meta:
        model = AboutSetting
        fields = [
            "logo",
            "judul",
            "tagline",
            "deskripsi",
            "sejarah",
            "ceo_nama",
            "ceo_jabatan",
            "ceo_foto",
            "visi",
            "misi",
        ]
        widgets = {
            "deskripsi": forms.Textarea(attrs={"rows": 4}),
            "sejarah": forms.Textarea(attrs={"rows": 5}),
            "visi": forms.Textarea(attrs={"rows": 4}),
            "misi": forms.Textarea(attrs={"rows": 4}),
            "logo": forms.FileInput(attrs={"accept": "image/*"}),
            "ceo_foto": forms.FileInput(attrs={"accept": "image/*"}),
        }


class TestimoniForm(forms.ModelForm):
    class Meta:
        model = Testimoni
        fields = [
            "nama_pelanggan",
            "kota",
            "produk",
            "foto",
            "rating",
            "pesan",
            "aktif",
        ]
        widgets = {
            "foto": forms.FileInput(attrs={"accept": "image/*"}),
            "pesan": forms.Textarea(attrs={"rows": 4}),
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }


class MitraDeepublishForm(forms.ModelForm):
    class Meta:
        model = MitraDeepublish
        fields = ["nama", "gambar"]
        widgets = {
            "gambar": forms.FileInput(attrs={"accept": "image/*"}),
        }


class TestimoniPublicForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[
            (1, "★"),
            (2, "★"),
            (3, "★"),
            (4, "★"),
            (5, "★"),
        ],
        coerce=int,
        empty_value=None,
        required=True,
        widget=forms.RadioSelect,
        label="Rating",
    )

    class Meta:
        model = Testimoni
        fields = ["rating", "pesan"]
        widgets = {
            "pesan": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Ceritakan pengalaman Anda berbelanja di Losari Computer...",
                }
            ),
        }
