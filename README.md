# KREASI — Sistem Kolaborasi dan Rekam Jejak Prestasi Mahasiswa

KREASI dikembangkan sebagai platform yang mendukung kolaborasi dan pengembangan potensi mahasiswa S1 Informatika melalui pengelolaan proyek, kegiatan akademik, dan rekam jejak prestasi secara terintegrasi. Melalui platform ini, mahasiswa dapat mengembangkan profil dan talenta, mengikuti kegiatan atau proyek, mengumpulkan bukti kegiatan, serta membangun rekam prestasi yang dapat digunakan untuk kebutuhan akademik.

KREASI juga membantu dosen dalam membimbing proyek, memantau perkembangan dokumentasi, memverifikasi tahapan kegiatan, dan memberikan penilaian. Administrator program studi mendukung pengelolaan akun dan data akademik, validasi prestasi, rekapitulasi, finalisasi, serta pencetakan Surat Keterangan Pendamping Ijazah (SKPI).

## Gambaran umum program

KREASI memiliki tiga jenis pengguna utama: **Mahasiswa**, **Dosen**, dan **Administrator**. Setiap jenis pengguna memiliki menu dan tanggung jawab yang berbeda, tetapi semuanya mendukung tujuan yang sama, yaitu mengelola aktivitas, kolaborasi, dan rekam jejak prestasi mahasiswa dengan lebih teratur.

- **Mahasiswa** mengelola profil dan talenta, melihat bursa proyek, mengikuti atau mengusulkan proyek, memantau kemajuan, mengirim dokumentasi, dan melihat rekam jejak prestasi serta SKPI.
- **Dosen** mengelola profil dosen, melihat talent pool, meninjau usulan, membimbing proyek, memeriksa dokumentasi, mengelola kelompok, dan melakukan penilaian sesuai alur proyek.
- **Administrator** mengelola akun dan data master, memvalidasi prestasi, menyampaikan pengumuman, melihat rekapitulasi, melakukan finalisasi, serta mencetak SKPI.

Sistem mendukung proyek umum, proyek mata kuliah, dan kegiatan Informatika Untuk Masyarakat. Alur proyek dapat mencakup pengajuan, pengelolaan anggota, pengumpulan dokumen, verifikasi, revisi, persetujuan, dan penilaian.

## Data dan cara kerja singkat

Aplikasi menggunakan Django sebagai backend dan SQLite sebagai database awal. Data dummy bawaan dari versi KREASI sebelumnya tetap dipertahankan untuk kebutuhan demonstrasi. Informasi aplikasi disimpan di `ApplicationState`, sedangkan berkas yang diunggah disimpan di folder `media/` dan informasi berkasnya dicatat pada `StoredDocument`.

Untuk menjaga kompatibilitas dengan data demo, data bisnis aplikasi saat ini disimpan sebagai satu payload JSON, bukan dipisah menjadi tabel relasional untuk setiap akun, proyek, anggota, dan prestasi. Pendekatan ini membantu mempertahankan struktur data pada versi demo, tetapi belum ditujukan sebagai rancangan akhir untuk penggunaan produksi berskala besar.

Frontend — HTML, CSS, JavaScript
Menampilkan halaman, tombol, formulir, menu navigasi, filter proyek, modal, notifikasi, dan perubahan tampilan tanpa harus memuat ulang seluruh halaman.
Permintaan dan respons melalui API

Backend — Python dan Django
Memproses permintaan, melakukan autentikasi, memeriksa hak akses, memvalidasi data, menjalankan aturan bisnis, dan mengelola penyimpanan.
Baca dan simpan data

Rincian fitur per peran dijelaskan dalam [FEATURE.md](FEATURE.md).

## Menjalankan aplikasi

### Persyaratan

- Python 3.10 atau lebih baru.
- Django versi `>=5.1,<6.0`.
- Browser modern dengan JavaScript aktif.

### Langkah menjalankan

Buka terminal pada folder proyek, kemudian jalankan:

```bash
# Membuat lingkungan Python terpisah untuk proyek
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# Memasang dependensi proyek
pip install -r requirements.txt

# Membuat tabel database yang diperlukan Django
python manage.py migrate

# Menjalankan server pengembangan
python manage.py runserver
```

Buka `http://127.0.0.1:8000/` di browser. Pada penggunaan awal, antarmuka menginisialisasi data dummy jika belum ada, lalu menyimpannya melalui API Django. Perubahan berikutnya disimpan ke database.

### Akun demonstrasi

Akun demo menggunakan kata sandi contoh `password123`.

- **Administrator:** username `admin`, kata sandi `password123`.
- **Mahasiswa dan dosen:** gunakan username berupa NIM atau NIP yang tersedia pada data demo, dengan kata sandi `password123`, lalu pilih peran login yang sesuai.

Akun tersebut hanya untuk demonstrasi dan bukan kredensial kampus sungguhan.

## Struktur folder

```text
KREASI_Django/
├── manage.py                    # Perintah untuk menjalankan dan mengelola Django
├── requirements.txt             # Daftar dependensi Python
├── kreasi_site/
│   ├── settings.py              # Pengaturan proyek, database, sesi, dan media
│   ├── urls.py                  # Rute utama website
│   ├── wsgi.py                  # Titik masuk server WSGI
│   └── asgi.py                  # Titik masuk server ASGI
├── kreasi_app/
│   ├── models.py                # Class yang mewakili data yang disimpan
│   ├── services.py              # Class layanan, aturan bisnis, dan contoh OOP
│   ├── views.py                 # Penghubung permintaan website dengan layanan
│   ├── urls.py                  # Rute halaman dan API aplikasi
│   ├── admin.py                 # Pengaturan tampilan data di Django Admin
│   ├── tests.py                 # Pengujian otomatis dasar
│   ├── migrations/              # Riwayat struktur database
│   ├── templates/kreasi_app/
│   │   └── index.html           # Halaman utama KREASI
│   └── static/kreasi_app/       # Lokasi aset statis tambahan
├── docs/
│   ├── uml_class_diagram.png    # Diagram UML dalam bentuk gambar
│   └── uml_class_diagram.dot    # Sumber diagram yang dapat diedit
└── media/                       # Lokasi penyimpanan berkas yang diunggah
```

## Alur kerja utama

1. Pengguna membuka KREASI dan melihat fitur sesuai alur aplikasi.
2. Data aplikasi yang sudah tersimpan dimuat dari backend. Jika belum ada, data dummy awal dimasukkan ke penyimpanan.
3. Ketika pengguna login, backend memeriksa akun demo dan memilih layanan profil berdasarkan jenis pengguna.
4. Saat perubahan data dikirim, layanan memeriksa bentuk dan ukuran data serta memeriksa apakah sesi memiliki peran yang diizinkan untuk menyimpan perubahan.
5. Data disimpan melalui repository Django ke database. Berkas dokumentasi disimpan melalui layanan dokumen, sedangkan metadata berkas disimpan di database.
6. Data yang tersimpan dapat dimuat kembali saat aplikasi dibuka lagi.

# Penerapan empat pilar OOP

OOP (*Object-Oriented Programming* atau pemrograman berorientasi objek) adalah cara menyusun program menggunakan **class** sebagai rancangan dan **object** sebagai hasil yang dibuat dari rancangan tersebut. Dalam KREASI, pendekatan ini digunakan agar proses pengelolaan akun, data aplikasi, dan dokumen memiliki tanggung jawab yang jelas. Contoh utamanya dapat dipelajari pada `kreasi_app/services.py` dan `kreasi_app/models.py`.

## Peta class yang penting

| Class | Tanggung jawab dalam KREASI |
|---|---|
| `BaseAccountService` | Menetapkan aturan umum yang harus disediakan setiap layanan akun. |
| `StudentAccountService` | Menyiapkan profil dan informasi akademik mahasiswa. |
| `LecturerAccountService` | Menyiapkan profil dan informasi pengampuan dosen. |
| `AdminAccountService` | Menyiapkan identitas administrator yang diperlukan oleh aplikasi. |
| `AccountServiceFactory` | Memilih layanan akun berdasarkan peran pengguna. |
| `StateService` | Mengatur proses membaca dan menyimpan data utama aplikasi. |
| `BaseStateRepository` | Menentukan kontrak untuk mengambil dan menyimpan data aplikasi. |
| `DjangoStateRepository` | Menjalankan proses penyimpanan menggunakan database Django. |
| `PermissionService` | Mengumpulkan pemeriksaan dasar peran untuk perubahan data dan berkas. |
| `DocumentService` | Mengatur unggah, pencarian, dan penghapusan berkas dokumentasi. |
| `ApplicationState` | Menyimpan payload data KREASI di database. |
| `StoredDocument` | Menyimpan metadata dan lokasi berkas yang diunggah. |
| `TimestampedModel` | Menyediakan waktu pembuatan dan pembaruan bagi model turunannya. |

## 1. Enkapsulasi (*encapsulation*)

**Di mana:** `kreasi_app/models.py`, class `ApplicationState`, melalui getter `get_payload()` dan setter `set_payload()` serta property `payload`; dan `kreasi_app/services.py`, class `DjangoStateRepository` serta `StateService` yang memakai jalur getter/setter tersebut.

### Apa artinya?

Enkapsulasi berarti mengelompokkan data dan proses yang berhubungan ke dalam class, lalu menyediakan cara yang jelas untuk menggunakannya. Tujuannya agar bagian lain dari program tidak perlu mengubah data dengan cara yang berbeda-beda atau melewati pemeriksaan yang seharusnya dilakukan.

### Penerapannya di KREASI

`StateService` menjadi pintu layanan untuk membaca dan menyimpan data aplikasi. View pada `views.py` memanggil `load_state()` atau `store_state()`, bukan menulis langsung ke record database dari setiap endpoint. Sebelum data disimpan, `store_state()` memeriksa apakah data berbentuk dictionary, memeriksa ukuran payload, dan memeriksa peran sesi setelah data awal dibuat. Setelah lolos pemeriksaan, data diteruskan ke repository untuk disimpan.

Di sisi model, `ApplicationState.get_payload()` adalah getter yang memberikan salinan isi data. `ApplicationState.set_payload(data)` adalah setter yang menerima perubahan, memastikan data berbentuk dictionary, lalu menyimpan salinannya. Property `payload` juga diarahkan ke getter/setter tersebut, sehingga kode aplikasi yang membaca atau mengisi `state.payload` melewati aturan yang sama. Method lama `read_payload()` dan `replace_payload()` tetap tersedia sebagai penghubung agar pemanggil terdahulu tetap kompatibel.

```python
# Contoh ringkas dari kreasi_app/models.py
class ApplicationState(TimestampedModel):
    # Field database internal memakai kolom database bernama "payload".
    _payload_data = models.JSONField(db_column="payload", default=dict)

    @property
    def payload(self):
        # Getter menyediakan salinan agar perubahan di luar class tidak langsung mengubah data internal.
        return self.get_payload()

    @payload.setter
    def payload(self, data):
        # Setter mengarahkan setiap penetapan property ke proses validasi yang sama.
        self.set_payload(data)

    def get_payload(self):
        # Getter mengembalikan salinan isi data.
        return deepcopy(getattr(self, "_payload_data", None) or {})

    def set_payload(self, data):
        # Setter memastikan data cocok untuk state aplikasi dan memisahkan salinannya.
        if not isinstance(data, dict):
            raise ValueError("Data payload harus berupa dictionary/objek JSON.")
        self._payload_data = deepcopy(data)
```

**Contoh alur pemakaian:** repository memanggil `get_payload()` untuk membaca data dan `set_payload(data)` untuk menggantinya. Setelah setter dipanggil, repository menyimpan record dengan `save()`. Dengan begitu, perubahan data proyek, prestasi, dashboard, dan data master menggunakan jalur yang konsisten.

```python
# Contoh pemakaian dari kode backend
state = ApplicationState.objects.get(key="kreasi-default")
data = state.get_payload()           # Getter: ambil salinan untuk dibaca/diolah.
data["masterData"]["courses"] = ["Basis Data"]
state.set_payload(data)              # Setter: validasi tipe dan simpan salinan baru.
state.save()                         # Simpan perubahan ke database.
```

Jika setter menerima data yang bukan dictionary, method akan mengangkat `ValueError` sehingga bentuk data yang disimpan tetap sesuai dengan state KREASI. Getter juga mengembalikan salinan, jadi perubahan pada hasil getter tidak otomatis mengubah data di dalam model sebelum setter dipanggil.

**Hubungannya dengan fitur:** saat dashboard, proyek, prestasi, atau data master perlu disimpan, aplikasi menggunakan layanan state yang sama. Pemeriksaan dan proses penyimpanan terpusat sehingga tidak perlu ditulis ulang pada setiap fitur.

Pada layanan akun, method `_base_fields()` juga merapikan informasi umum akun dan tidak memasukkan field `password` ke profil. Nama yang diawali satu garis bawah, seperti `_base_fields()`, merupakan konvensi Python untuk menandai bagian yang dimaksudkan sebagai helper internal. Ini bukan kunci keamanan mutlak. Kontrol akses tetap perlu dilakukan melalui pemeriksaan service dan endpoint.

**Batasan yang perlu dipahami:** getter/setter membuat jalur akses resmi dan menerapkan validasi, tetapi bukan mekanisme keamanan mutlak. Python masih memungkinkan kode yang sengaja mengakses atribut internal `_payload_data`; garis bawah adalah konvensi untuk menandai bagian internal. Perlindungan pada fitur juga tetap mengandalkan validasi `StateService` dan pemeriksaan peran sebelum data disimpan.

## 2. Abstraksi (*abstraction*)

**Di mana:** `kreasi_app/services.py`, class `BaseAccountService` dan `BaseStateRepository`, menggunakan `ABC` serta `@abstractmethod`.

### Apa artinya?

Abstraksi menyembunyikan rincian yang tidak perlu diketahui oleh pemanggil dan menetapkan fungsi utama yang harus tersedia. Dalam Python, salah satu cara menerapkannya adalah memakai `ABC` (*Abstract Base Class*) dan `@abstractmethod`.

### Penerapannya di KREASI

`BaseAccountService` merupakan kelas abstrak. Class ini menentukan bahwa setiap layanan akun harus mempunyai `build_profile()` dan `serialize_login_profile()`. Kelas dasar mengetahui **apa yang perlu dilakukan**, tetapi tidak menentukan semua rincian profil mahasiswa, dosen, dan administrator karena kebutuhan data mereka berbeda.

```python
# Contoh dari kreasi_app/services.py
from abc import ABC, abstractmethod

class BaseAccountService(ABC):
    # Kontrak ini harus dilengkapi oleh layanan akun turunannya.
    @abstractmethod
    def build_profile(self, record: dict) -> dict:
        """Membentuk profil sesuai jenis pengguna."""
        raise NotImplementedError

    @abstractmethod
    def serialize_login_profile(self, user: dict) -> dict:
        """Membentuk data profil yang dikirim setelah login."""
        raise NotImplementedError
```

Karena dua method tersebut abstrak, `BaseAccountService` tidak dapat digunakan sebagai layanan konkret sebelum implementasinya disediakan oleh class turunan. `StudentAccountService`, `LecturerAccountService`, dan `AdminAccountService` melengkapi kontrak tersebut sesuai kebutuhan masing-masing.

Abstraksi juga diterapkan pada `BaseStateRepository`, yang menetapkan method `load()` dan `save()`. `DjangoStateRepository` mengisi kontrak itu dengan cara membaca dan menulis melalui ORM Django.

**Hubungannya dengan fitur:** proses login dapat meminta profil melalui kontrak layanan yang sama, tanpa perlu mengetahui detail bagaimana profil setiap peran dirangkai. Demikian juga, `StateService` memakai repository melalui method `load()` dan `save()` sehingga detail penyimpanan database terpisah dari aturan layanan.

## 3. Pewarisan (*inheritance*)

**Di mana:** `kreasi_app/services.py`, class `StudentAccountService`, `LecturerAccountService`, dan `AdminAccountService` yang mewarisi `BaseAccountService`, serta `DjangoStateRepository` yang mewarisi `BaseStateRepository`. Pewarisan model juga ada di `kreasi_app/models.py`: `ApplicationState` dan `StoredDocument` mewarisi `TimestampedModel`.

### Apa artinya?

Pewarisan memungkinkan class baru menggunakan fungsi atau aturan dari class induk, kemudian menambahkan atau mengganti perilakunya. Pola ini berguna ketika beberapa bagian aplikasi mempunyai tanggung jawab umum tetapi masih memerlukan perilaku khusus.

### Penerapannya di KREASI

Ketiga layanan akun mewarisi `BaseAccountService`. Proses umum `sync_record()` dan helper `_base_fields()` disediakan oleh kelas dasar, sedangkan class turunan mengatur field profil sesuai perannya.

```python
# Contoh singkat dari kreasi_app/services.py
class StudentAccountService(BaseAccountService):
    role = "student"

    def build_profile(self, record: dict) -> dict:
        # Gunakan field umum dari induk, lalu tambahkan data akademik mahasiswa.
        profile = self._base_fields(record)
        profile.update({
            "nim": str(record.get("nim", "")),
            "angkatan": str(record.get("angkatan", "")),
            "kelas": str(record.get("kelas", "")),
            "gpa": record.get("gpa"),
        })
        return profile
```

Pada contoh tersebut, `StudentAccountService` tidak perlu menulis ulang semua proses untuk membentuk field umum seperti username, nama, email, dan program studi. Class ini menggunakan `_base_fields()` dari induknya, kemudian melengkapi data yang khusus diperlukan mahasiswa.

### Jenis pewarisan yang ditemukan

**Pewarisan tunggal (*single inheritance*) — diterapkan.** Sebuah class memiliki satu class induk langsung. Contohnya `StudentAccountService` mewarisi `BaseAccountService`; `DjangoStateRepository` mewarisi `BaseStateRepository`; serta `ApplicationState` dan `StoredDocument` mewarisi `TimestampedModel`.

**Pewarisan bertingkat (*multilevel inheritance*) — diterapkan.** Rantai pewarisan melibatkan lebih dari satu tingkat. Contohnya:

```text
ABC
└── BaseAccountService
    └── StudentAccountService
```

`BaseAccountService` mewarisi `ABC`, lalu `StudentAccountService` mewarisi `BaseAccountService`. Dengan demikian, layanan mahasiswa berada dua tingkat di bawah `ABC`.

**Pewarisan hierarkis (*hierarchical inheritance*) — diterapkan.** Beberapa class memiliki induk yang sama. `StudentAccountService`, `LecturerAccountService`, dan `AdminAccountService` sama-sama mewarisi `BaseAccountService`. Mereka menggunakan proses umum dari induk, tetapi mengolah informasi spesifik masing-masing peran.

**Pewarisan berganda (*multiple inheritance*) — tidak diterapkan pada class aplikasi.** Multiple inheritance terjadi jika sebuah class secara langsung mewarisi dua atau lebih class induk, misalnya `class Contoh(A, B):`. Kode KREASI tidak memakai pola tersebut untuk layanan akun. Sebagai gantinya, `StateService` menggunakan **komposisi**: ia menerima object repository dan object pemeriksaan izin, lalu bekerja dengan memanggil method kedua object tersebut. Komposisi memisahkan tanggung jawab tanpa membuat `StateService` menjadi turunan dari kedua class.

**Hubungannya dengan fitur:** tiga portal menggunakan layanan akun dengan kerangka dasar seragam, sehingga proses umum tidak perlu diduplikasi. Field yang khusus mahasiswa, dosen, atau administrator tetap diolah oleh class yang tepat.

## 4. Polimorfisme (*polymorphism*)

**Di mana:** `kreasi_app/services.py`, method `build_profile()` dan `serialize_login_profile()` pada class `StudentAccountService`, `LecturerAccountService`, dan `AdminAccountService`, dengan pemilihan melalui `AccountServiceFactory.serialize()`. Alur ini digunakan oleh `session_api()` di `kreasi_app/views.py`.

### Apa artinya?

Polimorfisme memungkinkan method dengan nama dan kontrak yang sama menghasilkan perilaku berbeda sesuai object yang menjalankannya. Pada KREASI, bentuk utamanya adalah *method overriding*: class turunan menyediakan implementasi method yang sebelumnya didefinisikan sebagai kontrak di kelas dasar.

### Penerapannya di KREASI

Ketiga class layanan mempunyai method `build_profile()` dan `serialize_login_profile()`, tetapi field yang disiapkan berbeda.

- `StudentAccountService` menyertakan NIM, angkatan, kelas, IPK, dan mata kuliah yang diambil.
- `LecturerAccountService` menyertakan NIP, bidang keahlian, mata kuliah yang diampu, serta ringkasan informasi akademik dosen.
- `AdminAccountService` menyertakan identitas NIP dan jabatan administrator.

Factory memanggil method dengan cara yang sama, tetapi Python menjalankan implementasi milik service yang dipilih.

```python
# Contoh dari kreasi_app/services.py
class AccountServiceFactory:
    _services = {
        "student": StudentAccountService,
        "lecturer": LecturerAccountService,
        "admin": AdminAccountService,
    }

    @classmethod
    def serialize(cls, user: dict) -> dict:
        # Pilih jenis service dari role akun.
        service = cls.for_role(user.get("role"))
        # Normalisasi menggunakan aturan service terpilih.
        normalized = service.sync_record(user)
        # Method ini berjalan sesuai implementasi class yang dipilih.
        return service.serialize_login_profile(normalized)
```

Contohnya, jika akun yang login berperan sebagai mahasiswa, factory memilih `StudentAccountService`; untuk dosen, factory memilih `LecturerAccountService`. Pemanggil tetap menggunakan method `serialize_login_profile()` yang sama, tetapi hasilnya berbeda karena implementasi class berbeda.

Alur ini benar-benar digunakan oleh endpoint `session_api()` di `kreasi_app/views.py`. Endpoint memeriksa akun demo, lalu memanggil `AccountServiceFactory.serialize(user)` untuk membuat profil yang aman dikirim ke antarmuka. Profil yang dihasilkan tidak menyertakan field kata sandi.

**Hubungannya dengan fitur:** pemrosesan profil login untuk tiga peran dilakukan melalui satu alur umum, sementara identitas dan informasi akademik yang dibutuhkan masing-masing portal tetap berbeda.

## Hubungan antar-class dan UML

Diagram menggambarkan dua jenis hubungan utama:

- **Pewarisan:** class turunan menggunakan perilaku dasar dari class induknya. Contohnya tiga service akun terhadap `BaseAccountService`, serta `DjangoStateRepository` terhadap `BaseStateRepository`.
- **Penggunaan/komposisi:** sebuah class bekerja dengan object lain tanpa mewarisi class tersebut. Contohnya `StateService` menggunakan `DjangoStateRepository` untuk penyimpanan dan `PermissionService` untuk pemeriksaan peran. `AccountServiceFactory` memilih class service yang sesuai, sedangkan `DocumentService` menggunakan `PermissionService` ketika mengelola berkas.

Buka [UML Class Diagram](docs/uml_class_diagram.png) untuk melihat atribut, method utama, dan hubungan antar-class. Sumber diagram yang dapat diedit tersedia di [uml_class_diagram.dot](docs/uml_class_diagram.dot) dan dapat dibuat ulang dengan Graphviz.

## Pengujian

Pengujian otomatis disiapkan dalam `kreasi_app/tests.py`. Pengujian mencakup pemilihan layanan akun untuk tiga peran, sifat abstrak `BaseAccountService`, pemisahan field profil, penolakan peran yang tidak dikenal, proses simpan-baca data, aturan sesi untuk perubahan data, endpoint login, dan halaman utama.

Jalankan perintah berikut setelah dependensi terpasang:

```bash
python manage.py check
python manage.py test
```

**Catatan status pengujian:** struktur kode serta pemeriksaan sintaks Python/JavaScript telah diperiksa pada saat pembuatan paket. Namun, Django belum tersedia di lingkungan pembuatan ini dan pengambilan paket tidak dapat dilakukan, sehingga `python manage.py check` dan `python manage.py test` belum dijalankan di lingkungan tersebut. Jalankan kedua perintah di komputer lokal untuk memeriksa aplikasi dengan Django terpasang.

## Batasan dan pengembangan selanjutnya

- KREASI ini menggunakan akun dan kata sandi dummy untuk demonstrasi. Sebelum digunakan secara nyata, autentikasi perlu dipindahkan ke sistem akun Django dan kata sandi harus disimpan sebagai hash.
- Data bisnis masih disimpan sebagai satu JSON agar cocok dengan struktur data demo. Penggunaan produksi dapat dikembangkan dengan model relasional untuk akun, proyek, anggota, dokumentasi, prestasi, dan penilaian.
- Pembatasan akses pada fitur lama sebagian masih berkaitan dengan aturan antarmuka. Untuk penggunaan produksi, setiap tindakan perlu diperiksa kembali di backend berdasarkan peran dan objek yang sedang diakses.
- Batas unggah berkas saat ini adalah 25 MB. Untuk deployment, konfigurasi `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, HTTPS, backup, dan kebijakan penyimpanan berkas perlu disesuaikan.
