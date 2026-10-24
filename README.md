# Thesis Store

## Kelompok 9

| No. | Nama Lengkap | NIM |
|---:|---|---|
| 1 | Muhammad Fauzan Ali Fatah | 240907500027 |
| 2 | Husnul Nadya F | 240907502036 |
| 3 | Firman | 240907501044 |
| 4 | Ahmad Naufal Dzaky | 240907502037 |

## Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Struktur Direktori](#2-struktur-direktori)
3. [Model Produk](#3-model-produk)
4. [Database dan Docker](#4-database-dan-docker)
5. [Menyiapkan dan Menjalankan Proyek](#5-menyiapkan-dan-menjalankan-proyek)
   - [Hasil Tambahkan](#hasil-tambahkan)
6. [Migrasi Database](#6-migrasi-database)
7. [Django Administration](#7-django-administration)
8. [Konfigurasi Dependency](#8-konfigurasi-dependency)
9. [Menghindari Konflik Port](#9-menghindari-konflik-port)
10. [Pengembangan Berikutnya](#10-pengembangan-berikutnya)
11. [Ringkasan Perintah](#11-ringkasan-perintah)

## 1. Gambaran Umum

Thesis Store adalah proyek awal aplikasi e-commerce berbasis Django. Proyek ini
menggunakan MariaDB sebagai database dan phpMyAdmin sebagai alat bantu untuk
melihat serta mengelola database melalui browser.

Pada kondisi saat ini, proyek sudah memiliki:

- konfigurasi proyek Django;
- aplikasi Django bernama `app`;
- model `Produk`;
- file migrasi awal untuk membuat tabel produk;
- service MariaDB dan phpMyAdmin melalui Docker Compose;
- konfigurasi koneksi Django ke MariaDB.

Halaman katalog atau CRUD produk belum dibuat. File view dan URL aplikasi masih
disiapkan sebagai fondasi untuk pengembangan berikutnya.

## 2. Struktur Direktori

```text
thesisstore/
├── manage.py
├── requirements.txt
├── compose.yaml
├── db.sqlite3
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── app/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── tests.py
    └── migrations/
        ├── 0001_initial.py
        └── __init__.py
```

### Penjelasan file penting

- `manage.py`: menjalankan perintah administrasi Django, misalnya migrasi dan
  server development.
- `core/settings.py`: konfigurasi utama proyek, termasuk aplikasi terpasang,
  database, middleware, dan pengaturan bahasa.
- `core/urls.py`: URL utama proyek. Saat ini menyediakan `/admin/` dan
  meneruskan URL dengan awalan `/app/` ke aplikasi `app`.
- `app/models.py`: definisi struktur data aplikasi.
- `app/views.py`: tempat logika untuk menerima request dan menghasilkan response.
  Saat ini belum memiliki view khusus.
- `app/urls.py`: daftar URL milik aplikasi. Saat ini masih kosong.
- `app/admin.py`: tempat mendaftarkan model agar dapat dikelola melalui Django
  Admin. Model `Produk` belum didaftarkan.
- `app/migrations/0001_initial.py`: migrasi untuk membuat tabel `Produk`.
- `compose.yaml`: definisi container MariaDB dan phpMyAdmin.
- `requirements.txt`: dependency Python yang diperlukan proyek.

## 3. Model Produk

Isi model saat ini secara konsep adalah:

```python
class Produk(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama
```

Model tersebut menghasilkan tabel aplikasi dengan kolom:

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | `BigAutoField` | Primary key yang dibuat otomatis oleh Django |
| `nama` | `VARCHAR(100)` | Nama produk, maksimal 100 karakter |

Method `__str__()` membuat objek produk ditampilkan menggunakan nilai
`nama`, bukan hanya nomor ID.

## 4. Database dan Docker

File `compose.yaml` menjalankan dua service:

### Service `db`

- Image: `mariadb:10.11.15`
- Nama database: `db_storethesis`
- User aplikasi: `thesistore_user`
- Password user aplikasi: `thesistore_pass`
- Password root: `rootpassword`
- Port host: `3311`
- Port di dalam jaringan Docker: `3306`

Format port berikut:

```yaml
"3311:3306"
```

berarti port `3311` pada Windows diteruskan ke port `3306` di dalam container
MariaDB.

### Service `phpmyadmin`

- Image: `phpmyadmin:latest`
- Host database Docker: `db`
- Port database Docker: `3306`
- Port browser pada host: `8889`

Format port berikut:

```yaml
"8889:80"
```

berarti phpMyAdmin dapat dibuka pada port `8889` di Windows, sedangkan Apache
di dalam container mendengarkan pada port `80`.

Nama `db` pada `PMA_HOST` bukan `localhost`. Karena phpMyAdmin dan MariaDB
berjalan pada network Docker yang sama, phpMyAdmin mengakses MariaDB melalui
nama service `db`.

Volume `db_data` menyimpan data MariaDB agar data tidak hilang ketika container
dihentikan atau dibuat ulang. Network `thesistore_network` memungkinkan service
`db` dan `phpmyadmin` saling berkomunikasi.

## 5. Menyiapkan dan Menjalankan Proyek

### Prasyarat

Pastikan sudah tersedia:

- Docker Desktop;
- Python;
- virtual environment Python;
- PowerShell pada Windows.

### Menjalankan container

Buka PowerShell pada direktori proyek:

```powershell
cd "D:\UCANG SEMESTER 5\E-COMMERCE\thesisstore"
docker compose up -d
```

Periksa status service:

```powershell
docker compose ps
```

Kedua service harus berstatus `Up`.

### Membuka phpMyAdmin

Buka alamat berikut pada browser:

```text
http://localhost:8889
```

Gunakan data login:

```text
Server: db
Username: root
Password: rootpassword
```

Database `db_storethesis` seharusnya terlihat pada panel kiri phpMyAdmin.

### Output phpMyAdmin

Berikut adalah hasil saat database `db_storethesis` berhasil dibuka melalui
phpMyAdmin pada `http://localhost:8889`. Tampilan ini menunjukkan tabel
`app_produk` dan tabel bawaan Django seperti tabel autentikasi, migrasi, dan
session.

![Output database db_storethesis di phpMyAdmin](docs/images/phpmyadmin-database-output.png)

Pada gambar tersebut:

- `db_storethesis` adalah database yang digunakan oleh proyek;
- `app_produk` adalah tabel yang dibuat dari model `Produk`;
- tabel `auth_*` digunakan oleh sistem autentikasi Django;
- `django_migrations` menyimpan catatan migrasi yang sudah diterapkan;
- `django_session` menyimpan data session Django.

### Hasil tambahkan

Deskripsi: **hasil tambahkan**

1. `app_provinsi`
2. `app_useradmin`

![Hasil tambahkan app_provinsi dan app_useradmin](docs/images/phpmyadmin-hasil-tambahkan.png)

### Menjalankan Django

Aktifkan virtual environment:

```powershell
.\venvku\Scripts\Activate.ps1
```

Jika PowerShell menolak script karena execution policy, jalankan Python secara
langsung tanpa aktivasi:

```powershell
.\venvku\Scripts\python.exe manage.py runserver
```

Jika virtual environment sudah aktif, perintahnya:

```powershell
python manage.py runserver
```

Buka aplikasi pada:

```text
http://127.0.0.1:8000/
```

## 6. Migrasi Database

Migrasi adalah mekanisme Django untuk mengubah definisi model Python menjadi
struktur tabel database.

Setelah mengubah `app/models.py`, buat migrasi baru:

```powershell
.\venvku\Scripts\python.exe manage.py makemigrations
```

Terapkan migrasi ke MariaDB:

```powershell
.\venvku\Scripts\python.exe manage.py migrate
```

Periksa status migrasi:

```powershell
.\venvku\Scripts\python.exe manage.py showmigrations
```

Tanda `[X]` berarti migrasi sudah diterapkan. Pesan `No migrations to apply`
berarti tidak ada migrasi baru yang perlu dijalankan; pesan tersebut bukan
error.

Penting: konfigurasi pada `core/settings.py` menggunakan MariaDB:

```python
'HOST': '127.0.0.1',
'PORT': '3311',
```

Karena itu, Django harus dijalankan ketika container database aktif. File
`db.sqlite3` tidak digunakan oleh konfigurasi database saat ini.

## 7. Django Administration

Django Administration adalah panel bawaan Django untuk mengelola data aplikasi
melalui browser. Pada proyek ini, panel tersebut tersedia pada:

```text
http://127.0.0.1:8000/admin/
```

Screenshot berikut menunjukkan halaman Django Administration setelah model
aplikasi berhasil ditambahkan. Menu yang tersedia meliputi `Anggota`,
`Produks`, `Provinsi`, dan `User admins`, serta menu autentikasi Django.

![Django Administration](docs/images/django-administration-hasil-tambahkan.png)

Server Django harus tetap berjalan agar halaman admin dapat dibuka. Jalankan
server dengan:

```powershell
.\venvku\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Jika browser menampilkan `ERR_CONNECTION_REFUSED`, biasanya tidak ada proses
Django yang sedang mendengarkan pada port `8000`. Pastikan perintah
`runserver` masih berjalan dan gunakan alamat yang sesuai.

### Membuat akun administrator

Buat akun superuser menggunakan perintah berikut:

```powershell
.\venvku\Scripts\python.exe manage.py createsuperuser
```

Isi username, alamat email, dan password ketika diminta. Akun tersebut
digunakan untuk login ke Django Administration. Jika password yang dimasukkan
dua kali berbeda, Django akan meminta pengulangan password.

### Mendaftarkan model ke admin

Model hanya tampil di panel admin setelah didaftarkan pada `app/admin.py`.
Untuk menampilkan model `Produk`, isi file tersebut dengan:

```python
from django.contrib import admin
from .models import Produk

admin.site.register(Produk)
```

Setelah server dijalankan dan login sebagai superuser, menu `Produk` dapat
digunakan untuk menambah, mengubah, dan menghapus data produk. Perubahan data
yang dilakukan melalui admin akan tersimpan pada database yang dikonfigurasi
di `core/settings.py`.

## 8. Konfigurasi Dependency

Isi `requirements.txt` menyediakan:

- `Django>=5.2,<6.0`: framework web yang digunakan;
- `PyMySQL>=1.1,<2.0`: driver Python untuk koneksi MySQL/MariaDB.

Instal dependency jika diperlukan:

```powershell
.\venvku\Scripts\python.exe -m pip install -r requirements.txt
```

## 9. Menghindari Konflik Port

Satu port host tidak dapat dipakai oleh dua container secara bersamaan. Jika
muncul pesan:

```text
Bind for 0.0.0.0:8889 failed: port is already allocated
```

periksa container yang memakai port tersebut:

```powershell
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

Hentikan container lama yang tidak digunakan, misalnya:

```powershell
docker stop tes-phpmyadmin-1
```

Lalu jalankan project ini kembali:

```powershell
docker compose up -d
```

Jangan menggunakan `docker compose down -v` hanya untuk mengatasi konflik
port. Opsi `-v` dapat menghapus volume database dan data yang tersimpan di
dalamnya.

## 10. Pengembangan Berikutnya

Fitur berikut dapat ditambahkan pada tahap selanjutnya:

1. mendaftarkan `Produk` di `app/admin.py`;
2. membuat view daftar dan detail produk;
3. menambahkan route produk pada `app/urls.py`;
4. membuat template HTML;
5. menambahkan field seperti harga, stok, deskripsi, dan gambar;
6. menambahkan form serta operasi tambah, ubah, dan hapus produk;
7. menambahkan pengujian untuk model, view, dan URL.

Contoh pendaftaran model di Django Admin:

```python
from django.contrib import admin
from .models import Produk

admin.site.register(Produk)
```

Setelah itu, buat superuser agar dapat masuk ke `/admin/`:

```powershell
.\venvku\Scripts\python.exe manage.py createsuperuser
```

## 11. Ringkasan Perintah

```powershell
cd "D:\UCANG SEMESTER 5\E-COMMERCE\thesisstore"
docker compose up -d
.\venvku\Scripts\python.exe manage.py migrate
.\venvku\Scripts\python.exe manage.py runserver
```

Alamat penting:

- Django: `http://127.0.0.1:8000/`
- Django Admin: `http://127.0.0.1:8000/admin/`
- phpMyAdmin: `http://localhost:8889`
- MariaDB dari Windows: `127.0.0.1:3311`
