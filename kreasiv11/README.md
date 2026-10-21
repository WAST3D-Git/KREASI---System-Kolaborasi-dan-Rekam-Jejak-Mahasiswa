# KREASI — Aplikasi Django

Dokumentasi ini menjelaskan struktur aplikasi, hubungan antarbagian, alur fitur, serta bukti penerapan Object-Oriented Programming (OOP) yang benar-benar ditemukan dalam kode sumber proyek.

## 1. Gambaran umum sistem

KREASI adalah sistem kolaborasi dan rekam jejak prestasi mahasiswa S1 Informatika. Proyek ini mempertahankan frontend HTML, CSS, dan JavaScript yang sudah ada, lalu menghubungkannya ke backend Django untuk autentikasi, penyimpanan state, dan penyimpanan berkas.

Frontend utama berada di `portal/static/portal/index.html`. Tampilan dan renderer JavaScript lama tetap digunakan agar perubahan UI/UX minimal. Backend menerima permintaan frontend melalui endpoint API, memvalidasi sesi dan peran pengguna, lalu mengakses model Django melalui lapisan repository dan service.

### Tanggung jawab utama

- **Autentikasi:** Django memeriksa username dan kata sandi, mencocokkan peran, dan membuat sesi login. Kata sandi disimpan melalui mekanisme hash Django.
- **Data fitur:** snapshot state yang diperlukan renderer disimpan pada model `AppState` dalam bentuk JSON. Pembacaan dan penulisan melewati `KreasiStateRepository`.
- **Akun pengguna:** model `PortalUser` memperluas model autentikasi bawaan Django. `AccountServiceFactory` memilih layanan yang sesuai untuk mahasiswa, dosen, atau admin.
- **Dokumen:** model `UploadedDocument` menyimpan metadata berkas dan menghubungkan file fisik dengan akun pengunggah. File disimpan melalui `FileField` di direktori `MEDIA_ROOT`.
- **Akses berbasis peran:** backend memfilter state dan membatasi perubahan yang dapat dilakukan berdasarkan akun yang sedang login. Pemeriksaan di JavaScript hanya mendukung pengalaman antarmuka; backend tetap menjadi tempat validasi akses.

## 2. Struktur direktori

```text
kreasi_django/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── kreasi_project/
│   ├── __init__.py
│   ├── settings.py          # Konfigurasi Django, database, auth, static dan media
│   ├── urls.py              # Pemetaan URL ke view/API
│   ├── asgi.py              # Titik masuk server ASGI
│   └── wsgi.py              # Titik masuk server WSGI
└── portal/
    ├── __init__.py
    ├── apps.py              # Konfigurasi aplikasi Django
    ├── models.py            # PortalUser, AppState, UploadedDocument
    ├── services.py          # Kontrak abstrak dan layanan akun per peran
    ├── repository.py        # Baca, filter, validasi, dan simpan snapshot state
    ├── views.py              # Function-based views untuk halaman dan API
    ├── admin.py              # Integrasi model dengan Django Admin
    ├── migrations/
    │   ├── __init__.py
    │   └── 0001_initial.py   # Migrasi awal tabel model
    ├── management/
    │   └── commands/
    │       └── create_kreasi_admin.py  # Membuat/memperbarui admin awal
    └── static/
        └── portal/
            └── index.html   # Frontend HTML/CSS/JavaScript KREASI
```

Folder berikut dibuat saat aplikasi berjalan atau sesuai pengaturan lokal, sehingga tidak harus ada pada arsip sumber:

- `db.sqlite3`: file basis data saat konfigurasi menggunakan SQLite.
- `media/`: lokasi default berkas dokumen yang diunggah.
- `staticfiles/`: tujuan pengumpulan static files ketika `collectstatic` dijalankan.
- `.venv/`: lingkungan Python virtual lokal.

## 3. Arsitektur dan relasi antarkelas

### 3.1 Diagram arsitektur

```text
Browser
  └── portal/static/portal/index.html
        └── fetch/API bridge (session, auth, state, documents)
              └── kreasi_project/urls.py
                    └── portal/views.py (function-based views)
                          ├── AccountServiceFactory / layanan akun
                          │     └── PortalUser (model autentikasi Django)
                          └── KreasiStateRepository
                                └── AppState (snapshot JSON)

portal/views.py ── UploadedDocument ── PortalUser
                         └── FileField ── berkas fisik di MEDIA_ROOT
```

`views.py` menggunakan fungsi view Django, bukan class-based views. Class OOP utama dipakai untuk memodelkan data, memisahkan kebijakan akun, dan mengendalikan akses/persistensi state.

### 3.2 Model data

| Kelas | File | Atribut/metode penting | Peran dalam sistem |
|---|---|---|---|
| `PortalUser` | `portal/models.py` | `role`, `identifier`, `full_name`, `profile_data`, `__str__()` | Akun mahasiswa/dosen/admin dan integrasi autentikasi Django. |
| `AppState` | `portal/models.py` | `key`, `data`, `version`, `updated_at`, `__str__()` | Menyimpan snapshot JSON yang digunakan renderer frontend. |
| `UploadedDocument` | `portal/models.py` | `file`, `original_name`, `content_type`, `size`, `uploaded_by`, `metadata`, `created_at`, `__str__()` | Metadata serta berkas fisik yang diunggah. |

Relasi model yang benar-benar didefinisikan:

- `PortalUser` **mewarisi** `django.contrib.auth.models.AbstractUser`.
- `UploadedDocument.uploaded_by` adalah `ForeignKey` ke `PortalUser` dengan `on_delete=models.PROTECT` dan `related_name="uploaded_documents"`. Satu akun dapat terkait dengan banyak dokumen; dokumen yang masih mereferensikan akun melindungi akun tersebut dari penghapusan langsung melalui perilaku relasi ini.
- `AppState` berdiri sendiri dan **tidak** memiliki `ForeignKey` ke `PortalUser`. Nilai state utama ditandai dengan `key="main"` dan struktur data berisi JSON.

`projects`, `achievements`, `portfolios`, `notifications`, dan kumpulan data UI lainnya belum masing-masing dijadikan model relasional terpisah. Data tersebut berada di dalam `AppState.data` sebagai agregat JSON. Ini adalah keputusan transisi untuk menjaga kontrak renderer lama, bukan bukti bahwa setiap jenis data memiliki tabel sendiri.

### 3.3 Diagram pewarisan layanan akun

```text
abc.ABC
  └── BaseAccountService
        ├── StudentAccountService
        ├── LecturerAccountService
        └── AdminAccountService

django.contrib.auth.models.AbstractUser
  └── PortalUser

Django Admin:
UserAdmin   └── PortalUserAdmin
ModelAdmin  ├── AppStateAdmin
            └── UploadedDocumentAdmin

AppConfig   └── PortalConfig
BaseCommand └── Command  (portal/management/commands/create_kreasi_admin.py)
```

Factory `AccountServiceFactory` **bukan** kelas induk layanan. Factory hanya menyimpan pemetaan role ke kelas layanan pada atribut `_services` dan membuat objek yang sesuai melalui `for_role()`.

## 4. Penerapan konsep OOP berdasarkan bukti kode

Bagian ini membedakan pola yang diterapkan secara langsung dari konsep yang tidak ditemukan. Lokasi dan nama metode merujuk pada kode dalam arsip proyek ini.

### 4.1 Enkapsulasi (*encapsulation*)

**Lokasi utama:** `portal/repository.py`, kelas `KreasiStateRepository`.

Enkapsulasi diterapkan dengan mengumpulkan aturan pengelolaan state pada satu kelas serta memisahkan antarmuka yang dipakai bagian lain dari helper internalnya.

| Bukti | Fungsi |
|---|---|
| Atribut kelas `STATE_KEY` | Menentukan key record state utama (`main`). |
| Atribut kelas `MAX_STATE_BYTES` | Menentukan batas ukuran payload state. |
| `get_state()` | Antarmuka baca snapshot internal-server. |
| `get_state_for(actor)` | Menghasilkan state yang telah difilter menurut peran dan identitas. |
| `save_state(payload, actor)` | Memvalidasi, menerapkan batas role, lalu menyimpan state. |
| `__state_record()` | Helper internal untuk memilih record `AppState`. |
| `__validate_payload(payload)` | Memastikan bentuk/tipe field utama benar, dapat diserialisasi, dan tidak melebihi batas ukuran. |
| `__remove_password_fields(state)` | Menghapus field password dari data yang dikirim kepada frontend. |
| `__visible_projects(...)` | Memfilter proyek sesuai peran dan aturan keterkaitan proyek. |
| `__apply_role_boundaries(...)` | Mengatur data apa yang boleh diubah oleh Admin, Dosen, atau Mahasiswa. |
| `__student_project_changes(...)`, `__lecturer_project_changes(...)`, dan helper `__merge_...` lainnya | Memisahkan aturan perubahan tiap jenis data dari fungsi view. |

**Cara kerja:** `state_view()` pada `portal/views.py` tidak menulis langsung ke model. Untuk permintaan GET, view memanggil `REPOSITORY.get_state_for(request.user)`. Untuk POST, view memanggil `REPOSITORY.save_state(...)`. Repository memvalidasi payload, membandingkannya dengan state lama, mempertahankan bagian yang tidak boleh diubah oleh aktor, kemudian menyimpan hasilnya dalam transaksi database.

**Manfaat nyata:** batas akses tidak hanya bergantung pada tombol atau menu di browser. Sebagai contoh, mahasiswa tidak dapat menetapkan sendiri status persetujuan proyek atau hasil validasi prestasinya hanya dengan mengubah payload permintaan.

**Catatan ketepatan teknis:** awalan nama `__` memicu *name-mangling* Python dan menandai helper sebagai detail internal, tetapi bukan sistem keamanan mutlak. Enkapsulasi pada kode ini juga berasal dari pemusatan perubahan melalui metode repository, validasi payload, serta pemeriksaan peran. Atribut model seperti `PortalUser.role` dan `AppState.data` sendiri bukan atribut privat.

### 4.2 Abstraksi (*abstraction*)

**Lokasi:** `portal/services.py`, kelas `BaseAccountService`.

Bukti penerapan abstraksi:

```python
from abc import ABC, abstractmethod

class BaseAccountService(ABC):
    role = None

    @abstractmethod
    def build_profile(self, record: dict) -> dict:
        """Kontrak untuk menormalkan data profil."""

    @abstractmethod
    def serialize_login_profile(self, user) -> dict:
        """Kontrak untuk membentuk profil sesi yang aman bagi UI."""
```

Kelas `BaseAccountService` mewarisi `ABC` dan mendeklarasikan dua metode dengan `@abstractmethod`. Kelas dasar menetapkan **apa yang harus disediakan** oleh layanan akun tanpa menetapkan struktur profil spesifik mahasiswa, dosen, atau admin.

Tiga kelas konkret yang memenuhi kontrak ini adalah:

- `StudentAccountService.build_profile()` dan `StudentAccountService.serialize_login_profile()`.
- `LecturerAccountService.build_profile()` dan `LecturerAccountService.serialize_login_profile()`.
- `AdminAccountService.build_profile()` dan `AdminAccountService.serialize_login_profile()`.

**Alur penggunaan:** `AccountServiceFactory.for_role(role)` menghasilkan objek layanan konkret. Objek itu kemudian dipakai untuk menormalisasi record atau menyerialisasi profil login. Abstraksi menjaga kontrak layanan tetap seragam meskipun isi profil yang dikelola berbeda.

**Manfaat nyata:** kode autentikasi dan repository tidak perlu menyatukan semua rincian profil ke satu metode panjang yang penuh percabangan khusus peran.

### 4.3 Pewarisan (*inheritance*) dan jenis yang ditemukan

Pewarisan dipakai agar kelas dapat menggunakan atribut/perilaku kelas induk, kemudian menambahkan atau mengganti perilaku yang diperlukan.

#### A. Pewarisan tunggal (*single inheritance*) — diterapkan

Pewarisan tunggal terjadi ketika sebuah kelas memiliki satu kelas induk langsung. Bukti konkret:

| Kelas turunan | Kelas induk langsung | Alasan/pemanfaatan |
|---|---|---|
| `PortalUser` | `AbstractUser` | Memakai autentikasi, username, hash password, status aktif, grup, dan permission Django; menambahkan data khusus KREASI. |
| `BaseAccountService` | `ABC` | Mendapat mekanisme kelas abstrak untuk menetapkan kontrak layanan. |
| `StudentAccountService` | `BaseAccountService` | Menggunakan proses sinkronisasi bersama dan menambahkan aturan profil mahasiswa. |
| `LecturerAccountService` | `BaseAccountService` | Menggunakan proses umum dan menambahkan metadata dosen. |
| `AdminAccountService` | `BaseAccountService` | Menggunakan proses umum dan menambahkan metadata administrator. |
| `PortalUserAdmin` | `UserAdmin` | Mengadaptasi Django Admin untuk field KREASI pada akun. |
| `AppStateAdmin`, `UploadedDocumentAdmin` | `ModelAdmin` | Mengatur daftar/field model di halaman admin Django. |
| `PortalConfig` | `AppConfig` | Memakai mekanisme konfigurasi aplikasi Django. |
| `Command` | `BaseCommand` | Menggunakan struktur custom management command Django. |

#### B. Pewarisan bertingkat (*multilevel inheritance*) — diterapkan

Rantai yang paling jelas berada pada layanan akun:

```text
ABC → BaseAccountService → StudentAccountService
                          → LecturerAccountService
                          → AdminAccountService
```

Contoh: `StudentAccountService` mewarisi langsung dari `BaseAccountService`, yang sebelumnya mewarisi `ABC`. Dengan demikian terdapat lebih dari satu tingkat pewarisan dari `ABC` ke layanan mahasiswa. Di jalur tersebut, `sync_record()` disediakan kelas dasar dan menggunakan `self.build_profile(record)`, sehingga proses bersama dapat memanfaatkan implementasi profil dari subclass.

#### C. Pewarisan hierarkis (*hierarchical inheritance*) — diterapkan

`StudentAccountService`, `LecturerAccountService`, dan `AdminAccountService` mempunyai induk langsung yang sama, yaitu `BaseAccountService`. Proses sinkronisasi akun dipusatkan di induk, sedangkan pembentukan/serialisasi profil disesuaikan di tiap turunan. Ini mengurangi duplikasi tanpa mengharuskan bentuk profil semua peran menjadi identik.

#### D. Pewarisan berganda (*multiple inheritance*) — tidak ditemukan

Tidak ditemukan deklarasi kelas proyek yang mewarisi dua atau lebih kelas induk secara langsung, misalnya `class Contoh(A, B)`. `PortalUser` hanya menyebut `AbstractUser` sebagai induk langsungnya; layanan akun juga masing-masing hanya menyebut `BaseAccountService`.

#### E. Pewarisan hibrida (*hybrid inheritance*) — perlu dipahami sesuai definisi

Struktur layanan yang ada menggabungkan bentuk bertingkat (`ABC → BaseAccountService → subclass`) dan hierarkis (tiga subclass berbagi `BaseAccountService`). Dalam bahan ajar yang mendefinisikan *hybrid* sebagai gabungan beberapa pola pewarisan, struktur itu dapat disebut **kombinasi/hibrida multilevel dan hierarchical**. Namun, proyek ini **tidak** memperlihatkan kombinasi multiple inheritance atau pola diamond. Karena istilah “hybrid” berbeda antarreferensi, dokumentasi menyebut pola konkret multilevel dan hierarchical secara terpisah dan menjelaskan dasar jika kombinasi tersebut diberi label hybrid.

### 4.4 Polimorfisme (*polymorphism*)

**Lokasi utama:** `portal/services.py`.

Polimorfisme tampak melalui *method overriding*: beberapa subclass menyediakan metode dengan nama dan kontrak sama, tetapi isi/hasilnya mengikuti peran.

| Metode | Implementasi berbeda | Dampak pada fitur |
|---|---|---|
| `build_profile(record)` | Student memakai NIM, angkatan, kelas; Lecturer memakai NIP dan `mataKuliahDiampu`; Admin memakai identitas admin dan email. | Menormalkan record akun ke data backend yang sesuai peran. |
| `serialize_login_profile(user)` | Student menyertakan NIM/angkatan/kelas; Lecturer menyertakan NIP/mata kuliah yang diampu; Admin mengirim identitas administrator. | Membentuk payload profil sesi yang digunakan UI setelah login. |

Pemanggilan polimorfik dapat dilihat pada:

```python
# portal/services.py — AccountServiceFactory.serialize()
return cls.for_role(user.role).serialize_login_profile(user)
```

`for_role()` memilih objek service sesuai `user.role`, lalu Python memanggil implementasi `serialize_login_profile()` milik objek tersebut. Polimorfisme juga terjadi saat `BaseAccountService.sync_record()` memanggil `self.build_profile(record)`: metode subclass yang dipakai sesuai objek yang sedang menjalankan proses.

**Manfaat nyata:** satu alur umum dapat menangani tiga peran, sedangkan metadata khas tiap peran tetap dibentuk oleh kelas yang bertanggung jawab atasnya. Dalam model, `__str__()` pada `PortalUser`, `AppState`, dan `UploadedDocument` juga mengoverride representasi objek agar lebih mudah dibaca di log atau Django Admin.

**Yang tidak diklaim:** kode tidak menunjukkan *method overloading* eksplisit berdasarkan signature. Bukti utama polimorfisme di aplikasi adalah overriding dan pemanggilan metode melalui objek layanan terpilih.

## 5. Kelas pendukung dan pembagian tanggung jawab

| Kelas/fungsi | File | Tanggung jawab |
|---|---|---|
| `AccountServiceFactory` | `portal/services.py` | Memetakan role ke kelas layanan, sinkronisasi daftar akun dalam transaksi, dan pemanggilan serialisasi polimorfik. |
| `KreasiStateRepository` | `portal/repository.py` | Antarmuka baca/simpan state, filter peran, validasi snapshot, serta pemulihan data yang tak boleh diubah oleh aktor. |
| `PortalUserAdmin` | `portal/admin.py` | Menyesuaikan Django Admin untuk model akun. |
| `AppStateAdmin` | `portal/admin.py` | Menampilkan key, versi, dan waktu pembaruan snapshot. |
| `UploadedDocumentAdmin` | `portal/admin.py` | Menampilkan metadata dokumen dan akun pengunggah. |
| `Command` | `portal/management/commands/create_kreasi_admin.py` | Membuat atau memperbarui admin awal, mengatur hash password, dan memastikan state utama tersedia. |
| `PortalConfig` | `portal/apps.py` | Mendefinisikan konfigurasi aplikasi `portal`. |
| Fungsi pada `portal/views.py` | `portal/views.py` | Memproses HTTP request/response untuk halaman, sesi, login/logout, state, dan dokumen. Fungsi-fungsi ini bukan kelas OOP. |

## 6. Alur kerja fitur

### 6.1 Admin menyinkronkan akun

1. Frontend mengirim snapshot melalui `POST /api/state/`.
2. `state_view()` memeriksa sesi, bentuk request, dan meneruskan state ke `KreasiStateRepository.save_state()`.
3. Repository memvalidasi payload dan menerapkan batas role. Jika aktor adalah Admin dan payload berisi daftar `users`, repository memanggil `AccountServiceFactory.sync_records()`.
4. Factory memilih layanan melalui `for_role()` dan memanggil `sync_record()`.
5. `sync_record()` mencari akun menggunakan username atau ID frontend, memanggil `build_profile()` secara polimorfik, memvalidasi kata sandi jika dikirim, menggunakan `set_password()` agar kata sandi di-hash, lalu menyimpan model pengguna.
6. Repository menyimpan state JSON tanpa field password mentah.

### 6.2 Login dan pemulihan sesi

1. Frontend mengirim username, password, dan role ke `POST /api/auth/login/`.
2. `login_view()` memanggil `authenticate()`. Akun yang salah, tidak aktif, atau memiliki role yang tidak sesuai mendapat pesan generik `Akun tidak terdaftar di sistem`.
3. Jika valid, `login()` membuat sesi Django.
4. `profile_for()` memanggil `AccountServiceFactory.serialize(user)`. Factory memilih metode serialisasi profil sesuai role.
5. Frontend mengambil state pada `GET /api/state/`; repository mengembalikan subset data yang sesuai peran dan identitas.
6. Saat halaman dimuat ulang, `GET /api/session/` memberi tahu frontend apakah sesi masih aktif.

### 6.3 Membaca dan menyimpan state

- `GET /api/state/` mewajibkan sesi dan memanggil `get_state_for()` agar browser tidak menerima seluruh data tanpa filter.
- `POST /api/state/` memvalidasi struktur state, menjalankan aturan perubahan untuk Admin/Dosen/Mahasiswa, lalu menyimpan `AppState` dalam transaksi.
- `version` pada `AppState` dinaikkan setiap kali snapshot yang berhasil diproses disimpan.
- `saveDB()` di JavaScript memakai antrean Promise untuk menjaga urutan permintaan simpan. Pembatasan keamanan tetap dijalankan di backend.

### 6.4 Unggah, pratinjau, dan hapus dokumen

1. Frontend mengirim file dan metadata ke `POST /api/documents/upload/`.
2. `document_upload()` memeriksa sesi, keberadaan file, ukuran maksimal 10 MB, ekstensi yang diizinkan, bentuk metadata, dan beberapa syarat kepemilikan berdasarkan role/purpose.
3. File disimpan melalui `UploadedDocument.file`; metadata seperti nama asli, tipe MIME, ukuran, pengunggah, dan konteks disimpan di database.
4. `GET /api/documents/<uuid>/` memeriksa hak pratinjau dan mengembalikan file asli untuk ditampilkan inline.
5. `POST /api/documents/<uuid>/delete/` memeriksa hak penghapusan terpisah, lalu menghapus file fisik dan record metadata.

Dosen dan Admin diberi akses pratinjau sesuai fungsi yang diterapkan pada `can_access_document()`. Hak penghapusan diatur tersendiri oleh `can_delete_document()`; hak melihat tidak otomatis berarti hak menghapus.

## 7. Endpoint API

| Metode | URL | Fungsi |
|---|---|---|
| `GET` | `/` | Menyajikan frontend KREASI asli. |
| `GET` | `/api/session/` | Memeriksa sesi aktif. |
| `POST` | `/api/auth/login/` | Login berbasis autentikasi Django. |
| `POST` | `/api/auth/logout/` | Mengakhiri sesi. |
| `GET` | `/api/state/` | Mengambil state yang difilter menurut peran. |
| `POST` | `/api/state/` | Memvalidasi dan menyimpan state dengan batas akses. |
| `POST` | `/api/documents/upload/` | Mengunggah file ke penyimpanan server. |
| `GET` | `/api/documents/<uuid>/` | Membaca/pratinjau dokumen setelah pemeriksaan akses. |
| `POST` | `/api/documents/<uuid>/delete/` | Menghapus dokumen jika diizinkan. |
| `GET` | `/django-admin/` | Halaman administrasi bawaan Django, tunduk pada autentikasi dan permission Django. |

## 8. Instalasi dan menjalankan di Windows

Prasyarat: Python yang kompatibel dengan versi Django dalam `requirements.txt`, pip, dan koneksi jaringan saat memasang dependensi.

Buka PowerShell pada folder `kreasi_django`, kemudian jalankan:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py create_kreasi_admin --username admin --name "Administrator Program Studi"
python manage.py runserver
```

Perintah `create_kreasi_admin` akan meminta kata sandi secara tersembunyi di terminal. Kata sandi minimal 8 karakter dan juga harus lolos validator kata sandi Django yang aktif. Setelah server berjalan, buka `http://127.0.0.1:8000/`, pilih peran **Admin**, lalu masuk memakai username dan kata sandi yang dibuat.

Jika PowerShell memblokir aktivasi virtual environment, jalankan perintah berikut pada sesi terminal itu, lalu aktifkan kembali:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Di Linux/macOS, aktivasi lingkungan virtual biasanya dilakukan dengan `source .venv/bin/activate`.

### Perintah pengembangan yang berguna

```powershell
python manage.py check
python manage.py showmigrations
python manage.py createsuperuser
```

Migrasi awal untuk model proyek sudah tersedia dalam `portal/migrations/0001_initial.py`. Jalankan `makemigrations` jika model benar-benar diubah kemudian; jangan menghapus atau mengubah migrasi yang sudah digunakan oleh database bersama tanpa rencana migrasi yang sesuai.

## 9. Catatan keamanan dan deployment

Pengaturan bawaan ditujukan untuk pengembangan lokal. Sebelum hosting:

1. Tetapkan `DJANGO_SECRET_KEY` yang kuat dan rahasia.
2. Atur `DJANGO_DEBUG=0` dan `DJANGO_ALLOWED_HOSTS` sesuai domain server.
3. Siapkan HTTPS serta konfigurasi cookie secure (pengaturan proyek mengaktifkannya saat `DEBUG` nonaktif).
4. Cadangkan database dan seluruh `MEDIA_ROOT`; mencadangkan database saja tidak mencadangkan konten berkas.
5. Jalankan migrasi dan konfigurasi static files sesuai kebutuhan hosting.
6. Uji seluruh alur penting dengan akun dan data yang sah sebelum sistem dipakai nyata.

Jangan menaruh password administrator dalam command line atau riwayat shell. Gunakan prompt tersembunyi yang disediakan command bila memungkinkan.

## 10. Batasan arsitektur yang perlu diketahui

- Sebagian besar data fitur frontend tetap disimpan dalam satu field JSON di `AppState`. Cara ini membantu mempertahankan renderer lama, tetapi bukan pengganti skema relasional terpisah untuk proyek, anggota, tahapan dokumentasi, prestasi, notifikasi, atau SKPI.
- Model akun (`PortalUser`) dan dokumen (`UploadedDocument`) tersimpan pada tabel Django tersendiri. File fisik berada di storage yang dipilih melalui `MEDIA_ROOT`.
- Proyek ini menggunakan function-based views. OOP paling terlihat pada model, repository, layanan akun, Django Admin, dan custom management command.
- Metode helper dengan awalan `__` dimaksudkan sebagai detail internal melalui name-mangling, bukan batas keamanan yang tidak dapat ditembus.
- Arsip sumber tidak memuat direktori pengujian otomatis khusus. Pemeriksaan `manage.py check`, migrasi, uji integrasi login/role, perubahan state, dan pengelolaan file tetap perlu dilakukan pada lingkungan tempat dependensi terpasang sebelum deployment produksi.

## 11. Ringkasan kontribusi OOP terhadap fitur

| Konsep | Bukti dalam kode | Kontribusi pada KREASI |
|---|---|---|
| Enkapsulasi | Antarmuka publik `KreasiStateRepository`; helper privat `__validate_payload()`, `__apply_role_boundaries()`, dan helper penggabungan state. | Pemrosesan state dipusatkan; validasi dan aturan perubahan tidak tersebar di view. |
| Abstraksi | `BaseAccountService(ABC)` serta `@abstractmethod` pada `build_profile()` dan `serialize_login_profile()`. | Menetapkan kontrak seragam bagi semua layanan akun tanpa memaksakan bentuk profil yang sama. |
| Pewarisan tunggal | `PortalUser(AbstractUser)`, `StudentAccountService(BaseAccountService)`, dan kelas turunan Django Admin. | Memanfaatkan perilaku framework dan proses umum tanpa menyalin ulang seluruh fungsi. |
| Pewarisan bertingkat | `ABC → BaseAccountService → layanan akun`. | Memisahkan kontrak abstrak dari proses bersama serta variasi implementasi konkret. |
| Pewarisan hierarkis | Tiga layanan role mewarisi `BaseAccountService`. | Mahasiswa, dosen, dan Admin berbagi proses sinkronisasi tetapi mempertahankan metadata masing-masing. |
| Polimorfisme | Override `build_profile()` dan `serialize_login_profile()`; factory memanggil nama metode yang sama melalui objek terpilih. | Login dan sinkronisasi akun dapat memakai alur seragam dengan hasil yang sesuai peran. |

Kesimpulannya, penerapan OOP yang paling langsung terlihat pada pengelolaan akun berbasis service, pengelolaan state berbasis repository, serta model Django. Konsep yang tidak memiliki bukti langsung—khususnya multiple inheritance—tidak dinyatakan sebagai implementasi proyek.
