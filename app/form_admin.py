from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

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
    url = forms.URLField(required=False, label="Link URL")
    nomor_telepon = forms.CharField(
        required=False,
        label="Nomor telepon",
        help_text="Isi URL atau nomor telepon. Salah satu wajib diisi.",
    )
    aktif = forms.BooleanField(required=False, initial=True)
    ikon = forms.ImageField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not cleaned_data.get("ikon"):
            self.add_error("ikon", "Unggah gambar ikon untuk sosial media ini.")
        if not cleaned_data.get("url") and not cleaned_data.get("nomor_telepon"):
            raise forms.ValidationError("Isi link URL atau nomor telepon.")
        if cleaned_data.get("url") and cleaned_data.get("nomor_telepon"):
            raise forms.ValidationError("Isi salah satu saja: link URL atau nomor telepon.")
        return cleaned_data

    class Meta:
        model = FooterSocial
        fields = ["url", "nomor_telepon", "ikon", "aktif"]
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
        fields = ["nama", "url", "nomor_telepon", "ikon", "aktif"]


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
    password_baru = forms.CharField(
        label="Kata sandi baru",
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Kosongkan jika tidak ingin mengganti"}
        ),
        help_text="Kosongkan jika kata sandi pelanggan tidak ingin diubah.",
    )
    konfirmasi_password = forms.CharField(
        label="Konfirmasi kata sandi",
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Ulangi kata sandi baru"}
        ),
    )
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

    def clean_password_baru(self):
        password = self.cleaned_data.get("password_baru")
        if password:
            validate_password(password, self.instance)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password_baru")
        confirmation = cleaned_data.get("konfirmasi_password")
        if password or confirmation:
            if not password:
                self.add_error("password_baru", "Isi kata sandi baru.")
            if password != confirmation:
                self.add_error(
                    "konfirmasi_password",
                    "Konfirmasi kata sandi tidak sama.",
                )
        return cleaned_data

    def save(self, commit=True):
        user = self.instance
        user.first_name = self.cleaned_data["nama"]
        user.email = self.cleaned_data["email"]
        user.is_active = self.cleaned_data["is_active"]
        password = self.cleaned_data.get("password_baru")
        update_fields = ["first_name", "email", "is_active"]
        if password:
            user.set_password(password)
            update_fields.append("password")
        if commit:
            user.save(update_fields=update_fields)
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
        labels = {
            "tipe": "Jenis foto",
            "gambar": "Pilih foto produk",
            "urutan": "Urutan",
        }
        widgets = {
            "gambar": forms.FileInput(attrs={"accept": "image/*"}),
            "urutan": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipe"].help_text = "Pilih bagian produk yang terlihat pada foto."
        self.fields["gambar"].help_text = "Gunakan foto yang terang dan tidak buram."


class AdminProdukKeunggulanForm(forms.ModelForm):
    class Meta:
        model = ProdukKeunggulan
        fields = ("judul", "deskripsi", "ikon", "warna", "urutan")
        labels = {
            "judul": "Nama keunggulan",
            "deskripsi": "Penjelasan singkat",
            "ikon": "Ikon",
            "warna": "Warna ikon",
            "urutan": "Urutan",
        }
        widgets = {
            "judul": forms.TextInput(attrs={"placeholder": "Contoh: Garansi resmi"}),
            "deskripsi": forms.TextInput(
                attrs={"placeholder": "Contoh: Aman digunakan dan bergaransi"}
            ),
            "warna": forms.HiddenInput(),
            "urutan": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["judul"].help_text = "Tulis keunggulan dalam 2–4 kata."
        self.fields["deskripsi"].help_text = "Jelaskan manfaatnya secara singkat."
        self.fields["ikon"].help_text = "Pilih ikon yang paling sesuai."
        self.fields["warna"].help_text = "Pilih warna yang sesuai dengan ikon."


class ProdukGambarFormSet(forms.BaseInlineFormSet):
    slot_types = ("depan", "keyboard", "panel", "cek")

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if index is None:
            return
        form.fields["urutan"].initial = index
        if not form.instance.pk and index < len(self.slot_types):
            form.fields["tipe"].initial = self.slot_types[index]


class ProdukKeunggulanFormSet(forms.BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if index is not None:
            form.fields["urutan"].initial = index


def create_produk_gambar_formset(*args, instance=None, **kwargs):
    existing_count = instance.galeri.count() if instance and instance.pk else 0
    formset_class = forms.inlineformset_factory(
        Produk,
        ProdukGambar,
        form=AdminProdukGambarForm,
        formset=ProdukGambarFormSet,
        extra=max(0, 4 - existing_count),
        can_delete=True,
    )
    return formset_class(*args, instance=instance, **kwargs)


def create_produk_keunggulan_formset(*args, instance=None, **kwargs):
    existing_count = instance.keunggulan.count() if instance and instance.pk else 0
    formset_class = forms.inlineformset_factory(
        Produk,
        ProdukKeunggulan,
        form=AdminProdukKeunggulanForm,
        formset=ProdukKeunggulanFormSet,
        extra=max(0, 2 - existing_count),
        can_delete=True,
    )
    return formset_class(*args, instance=instance, **kwargs)


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
