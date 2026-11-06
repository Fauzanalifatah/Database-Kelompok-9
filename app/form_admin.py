from django import forms
from django.contrib.auth.models import User

from .models import (
    AboutSetting,
    FooterPayment,
    FooterSetting,
    FooterSocial,
    MitraDeepublish,
    Provinsi,
    Testimoni,
    UserAdmin,
    UserPengguna,
    Pesanan,
    Artikel,
    KategoriArtikel,
    Produk,
    ProdukGambar,
    ProdukKeunggulan,
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
        fields = ["nama", "gambar", "aktif", "urutan"]
        widgets = {
            "gambar": forms.FileInput(attrs={"accept": "image/*"}),
        }


class AdminPelangganForm(forms.ModelForm):
    nama = forms.CharField(max_length=150, label="Nama pelanggan", required=False)
    telp = forms.CharField(max_length=15, label="Nomor telepon", required=False)
    alamat = forms.CharField(
        label="Alamat",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = User
        fields = ["nama", "email", "telp", "alamat", "is_active"]
        labels = {
            "email": "Email",
            "is_active": "Akun aktif",
        }

    def __init__(self, *args, **kwargs):
        self.member = kwargs.pop("member", None)
        super().__init__(*args, **kwargs)
        if self.member:
            self.fields["nama"].initial = self.instance.get_full_name()
            self.fields["telp"].initial = self.member.telp
            self.fields["alamat"].initial = self.member.alamat
    def save(self, commit=True):
        user = self.instance
        user.first_name = self.cleaned_data["nama"]
        user.email = self.cleaned_data["email"]
        user.is_active = self.cleaned_data["is_active"]
        if commit:
            user.save(update_fields=["first_name", "email", "is_active"])
        if self.member:
            self.member.telp = self.cleaned_data["telp"]
            self.member.alamat = self.cleaned_data["alamat"]
            self.member.save(update_fields=["telp", "alamat"])
        return user


class AdminPesananStatusForm(forms.ModelForm):
    class Meta:
        model = Pesanan
        fields = ["status"]
        labels = {"status": "Status pesanan"}


class AdminArtikelForm(forms.ModelForm):
    slug = forms.SlugField(required=False)

    class Meta:
        model = Artikel
        fields = [
            "title_articles",
            "slug",
            "desc_seo",
            "category",
            "authors",
            "content",
            "images",
            "published",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 18}),
            "images": forms.FileInput(attrs={"accept": "image/*"}),
        }


class AdminProdukForm(forms.ModelForm):
    slug = forms.SlugField(required=False)

    class Meta:
        model = Produk
        fields = [
            "nama",
            "slug",
            "merek",
            "kategori",
            "deskripsi",
            "spesifikasi",
            "harga",
            "diskon_persen",
            "stok",
            "kondisi",
            "gambar",
            "unggulan",
            "aktif",
        ]
        widgets = {
            "deskripsi": forms.Textarea(attrs={"rows": 6}),
            "spesifikasi": forms.Textarea(
                attrs={"rows": 5, "placeholder": '{"RAM": "16 GB", "Storage": "512 GB"}'}
            ),
            "gambar": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_spesifikasi(self):
        value = self.cleaned_data["spesifikasi"]
        if isinstance(value, str):
            import json

            try:
                value = json.loads(value or "{}")
            except json.JSONDecodeError as error:
                raise forms.ValidationError(
                    "Spesifikasi harus berupa JSON yang valid."
                ) from error
        if not isinstance(value, dict):
            raise forms.ValidationError("Spesifikasi harus berupa objek JSON.")
        return value


class AdminProdukGambarForm(forms.ModelForm):
    gambar = forms.ImageField(required=False)

    class Meta:
        model = ProdukGambar
        fields = ("tipe", "gambar", "urutan")


ProdukGambarFormSet = forms.inlineformset_factory(
    Produk,
    ProdukGambar,
    form=AdminProdukGambarForm,
    extra=1,
    can_delete=True,
)
ProdukKeunggulanFormSet = forms.inlineformset_factory(
    Produk,
    ProdukKeunggulan,
    fields=("judul", "deskripsi", "ikon", "warna", "urutan"),
    extra=2,
    can_delete=True,
)


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
