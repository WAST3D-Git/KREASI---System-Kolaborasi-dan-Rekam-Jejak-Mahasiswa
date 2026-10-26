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

### Panduan cepat untuk presentasi

| Pertanyaan yang mungkin muncul | Jawaban singkat | Lihat |
|---|---|---|
| Bagian mana yang berisi OOP? | Backend Python: `models.py`, `services.py`, `repository.py`, `admin.py`, command admin. Frontend JavaScript tidak memakai class. | Bagian 4 |
| Apa 4 pilar OOP di proyek ini? | **Enkapsulasi** → `KreasiStateRepository`; **Abstraksi** → `BaseAccountService(ABC)`; **Pewarisan** → `PortalUser(AbstractUser)` dan 3 layanan akun; **Polimorfisme** → override `build_profile()` & `serialize_login_profile()`. | Bagian 4 |
| Bagaimana cara membuktikannya berjalan? | Skenario demo per pilar (bisa dijalankan langsung). | Bagian 4.5 |
| Fitur ini ditangani fungsi/class apa? | Tabel peta fitur → kode. | Bagian 1.1 |

### 1.1 Peta fitur → kode (frontend → endpoint → backend)

| Fitur (menu) | Fungsi frontend (`index.html`) | Endpoint | Backend yang bekerja |
|---|---|---|---|
| Login | `handleLoginSubmit` | `POST /api/auth/login/` | `views.login_view` → `AccountServiceFactory.serialize` |
| Tetap login setelah refresh | `initializeKreasi` | `GET /api/session/` | `views.session_info` |
| Logout | `doLogout` | `POST /api/auth/logout/` | `views.logout_view` |
| Memuat semua data (dashboard dll.) | `loadDB`, `kreasiApi` | `GET /api/state/` | `KreasiStateRepository.get_state_for` |
| Menyimpan setiap perubahan | `saveDB` | `POST /api/state/` | `KreasiStateRepository.save_state` → `__apply_role_boundaries` |
| Sinkron antar perangkat | `kreasiSyncFromServer` | `GET /api/state/version/` | `KreasiStateRepository.get_version` |
| Manajemen Akun (Admin) | `openCreateUserModal`, `saveNewUser`, `saveEditUser`, `saveNewPassword`, `confirmDeleteUser` | `POST /api/state/` | `AccountServiceFactory.sync_records` → `sync_record` → `build_profile` |
| Profil & Talenta, Portofolio (Mahasiswa) | `saveProfile`, `savePortfolio`, `addSkill` | `POST /api/state/`, `POST /api/documents/upload/` | `__merge_owned_rows`, `__merge_profile_map`, `document_upload` |
| Ajukan Prestasi (Mahasiswa) | `submitAchievement` | `POST /api/state/` + upload bukti | `__student_achievement_changes` (status dikunci "Menunggu Validasi") |
| Validasi Prestasi (Admin) | `openAdminAchievementModal`, `submitAchievementValidation` | `POST /api/state/` | `save_state` (hanya Admin yang boleh mengubah status) |
| Bursa Proyek / Usulkan Proyek | `openApplyProjectModal`, `saveNewProject` | `POST /api/state/` | `__student_project_changes`, `__visible_projects` |
| Tinjau Usulan Proyek (Dosen) | `openReviewProposalModal`, `submitReviewProposal` | `POST /api/state/` | `__lecturer_project_changes` |
| Dokumentasi Tahapan (Mahasiswa) | `submitMilestone` | upload + `POST /api/state/` | `_student_is_project_member`, `__keep_student_milestone_status` |
| Verifikasi Dokumentasi & Nilai (Dosen) | `submitMilestoneVerification`, `saveGrade` | `POST /api/state/` | `__lecturer_project_changes` |
| Talent Pool & Undangan | `openInviteTalentModal`, `openInvitationsModal` | `POST /api/state/` | `__merge_invitations` |
| Notifikasi | `openNotifications` | `POST /api/state/` | `__merge_notifications` |
| Pengumuman, Data Master, SKPI (Admin) | `saveNewAnnouncement`, `saveNewCategory`, `saveFinalizeSkpi` | `POST /api/state/` | `save_state` (hanya Admin yang boleh mengubah) |
| Pratinjau / unduh berkas | `openStoredDocument`, `getStoredDocument` | `GET /api/documents/<id>/` | `views.document_detail` + `can_access_document` |
| Hapus berkas | `removeStoredDocument` | `POST /api/documents/<id>/delete/` | `views.document_delete` + `can_delete_document` |

## 2. Struktur direktori

```text
kreasi_django/
├── manage.py
├── start.sh                 # Perintah start hosting (migrate + gunicorn)
├── .env.example             # Contoh variabel environment
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
    ├── tests.py              # 13 tes otomatis (OOP, login, hak akses, sinkronisasi, berkas)
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

## 4. Penerapan 4 pilar OOP (berdasarkan bukti kode)

Setiap pilar dijelaskan dengan pola yang sama: **definisi singkat → di mana → bagaimana kerjanya → manfaat nyata**. Semua nama class/method di bawah ada di kode.

> **Satu kalimat per pilar (untuk dihafal):**
> - **Enkapsulasi:** aturan akses data dibungkus dalam satu class (`KreasiStateRepository`); luar class cukup memanggil method publiknya.
> - **Abstraksi:** class abstrak (`BaseAccountService`) hanya menetapkan *apa* yang harus ada, bukan *bagaimana* isinya.
> - **Pewarisan:** class anak memakai ulang kode induk (`PortalUser` dari `AbstractUser`; 3 layanan akun dari `BaseAccountService`).
> - **Polimorfisme:** method bernama sama (`build_profile`) menghasilkan perilaku berbeda tergantung objeknya (mahasiswa/dosen/admin).

### 4.1 Enkapsulasi (*encapsulation*)

**Definisi:** membungkus data dan aturan pengolahannya dalam satu class, serta menyembunyikan detail internal dari pemakai class.

**Di mana:** `portal/repository.py`, class `KreasiStateRepository`.

**Cara kerja:**

| Bagian | Jenis | Fungsi |
|---|---|---|
| `get_state()`, `get_state_for(actor)`, `save_state(payload, actor, base_version)`, `get_version()` | **Antarmuka publik** | Satu-satunya pintu yang dipakai `views.py`. |
| `STATE_KEY`, `MAX_STATE_BYTES` | Atribut class | Aturan yang dibungkus: nama record data utama dan batas ukuran 8 MB. |
| `__state_record`, `__validate_payload`, `__remove_password_fields`, `__visible_projects`, `__apply_role_boundaries`, `__preserve_concurrent_rows`, `__merge_*`, `__student_*`, `__lecturer_*`, `__admin_project_changes` | **Detail internal** (awalan `__`) | Aturan rumit "siapa boleh melihat/mengubah apa" disembunyikan di sini. |

**Alur nyata:** `state_view()` di `views.py` **tidak pernah menyentuh database state secara langsung**. GET memanggil `REPOSITORY.get_state_for(user)`; POST memanggil `REPOSITORY.save_state(...)`. Di dalam, repository memeriksa bentuk data, membandingkannya dengan data lama server, mengembalikan bagian yang tidak boleh diubah peran itu, lalu menyimpan dalam transaksi.

**Manfaat nyata:** mahasiswa yang mengubah status prestasinya menjadi "Disetujui" lewat DevTools browser tetap gagal: `__student_achievement_changes` memulihkan status dari data server. Jika aturan akses berubah, cukup mengubah satu class.

**Catatan jujur:** awalan `__` memicu *name-mangling* Python, yang menandai method sebagai internal. Ini bukan kunci keamanan mutlak; keamanan sebenarnya berasal dari pemeriksaan peran di dalam method-nya. Atribut model seperti `PortalUser.role` bersifat publik.

### 4.2 Abstraksi (*abstraction*)

**Definisi:** menampilkan "apa yang harus dilakukan" dan menyembunyikan "bagaimana caranya"; di Python, lewat class abstrak.

**Di mana:** `portal/services.py`, class `BaseAccountService(ABC)`.

```python
class BaseAccountService(ABC):          # ABC = class abstrak
    role = None

    @abstractmethod
    def build_profile(self, record): ...            # wajib ditulis anak

    @abstractmethod
    def serialize_login_profile(self, user): ...    # wajib ditulis anak
```

**Cara kerja:** karena ada `@abstractmethod`, `BaseAccountService()` **tidak bisa dibuat objeknya** (Python melempar `TypeError`), dan class anak yang lupa menulis kedua method juga tidak bisa dibuat. Class dasar menjadi **kontrak**: semua layanan akun pasti punya dua kemampuan itu.

**Manfaat nyata:** kode login dan repository cukup memanggil `build_profile()` / `serialize_login_profile()` tanpa tahu rincian profil tiap peran. Tidak ada satu method raksasa berisi `if role == ...`.

### 4.3 Pewarisan (*inheritance*)

**Definisi:** class anak memakai atribut dan method class induk, lalu menambah atau mengganti sesuai kebutuhan.

**Pewarisan yang ada di kode (induk langsung ditulis di tanda kurung):**

| Class anak | Induk | Yang diwarisi / ditambah |
|---|---|---|
| `PortalUser` (`models.py`) | `AbstractUser` | Mewarisi username, hash sandi, `is_active`, grup, permission, `set_password()`. Menambah `role`, `identifier`, `full_name`, `profile_data`. |
| `BaseAccountService` | `ABC` | Mekanisme class abstrak. |
| `StudentAccountService`, `LecturerAccountService`, `AdminAccountService` (`services.py`) | `BaseAccountService` | Mewarisi `sync_record()` (satu kali ditulis, dipakai tiga anak). Menulis ulang `build_profile()` & `serialize_login_profile()`. |
| `PortalUserAdmin` | `UserAdmin` | Form admin akun lengkap; hanya menambah bagian "KREASI". |
| `AppStateAdmin`, `UploadedDocumentAdmin` | `ModelAdmin` | Tampilan admin model. |
| `PortalConfig` | `AppConfig` | Konfigurasi aplikasi. |
| `Command` (`create_kreasi_admin.py`) | `BaseCommand` | Struktur perintah `manage.py`. |

**Jenis pewarisan (diagram):**

```text
                 ABC
                  │
         BaseAccountService            <- induk bersama
        ┌─────────┼──────────┐
 Student      Lecturer      Admin      <- 3 anak langsung dari 1 induk
 AccountService  AccountService  AccountService
```

| Jenis | Status | Bukti |
|---|---|---|
| **Tunggal** (*single*) | Ada | Setiap class di atas hanya punya satu induk langsung, mis. `StudentAccountService(BaseAccountService)`. |
| **Bertingkat** (*multilevel*) | Ada | `ABC → BaseAccountService → StudentAccountService` (tiga tingkat). |
| **Hierarkis** (*hierarchical*) | Ada | Tiga layanan akun berbagi induk `BaseAccountService`. |
| **Berganda** (*multiple*) | **Tidak ada** | Tidak ada deklarasi `class X(A, B)` pada kode proyek. |
| **Hibrida** (*hybrid*) | Tidak berdiri sendiri | Struktur layanan akun merupakan gabungan bertingkat + hierarkis. Karena definisi "hibrida" berbeda antar referensi (sebagian mensyaratkan pewarisan berganda), jelaskan pola konkretnya, yaitu bertingkat dan hierarkis. |

**Manfaat nyata:** logika menyimpan akun (`sync_record`: cari akun, hash sandi, validasi kebijakan sandi) ditulis **satu kali** di induk, bukan tiga kali. Perbaikan di induk langsung berlaku untuk mahasiswa, dosen, dan admin.

### 4.4 Polimorfisme (*polymorphism*)

**Definisi:** pemanggilan method yang sama menghasilkan perilaku berbeda tergantung jenis objeknya.

**Di mana:** `portal/services.py` (utama) dan `__str__()` di `portal/models.py`.

| Method | Mahasiswa | Dosen | Admin |
|---|---|---|---|
| `build_profile(record)` | identitas = **NIM**, + angkatan, kelas | identitas = **NIP**, + `mataKuliahDiampu` | identitas admin + email |
| `serialize_login_profile(user)` | menambah `nim`, `angkatan`, `kelas` | menambah `nip`, `mataKuliahDiampu` | menambah `nip` |

**Dua titik pemanggilan polimorfik:**

```python
# 1) services.py — AccountServiceFactory.serialize()  (dipakai saat LOGIN)
return cls.for_role(user.role).serialize_login_profile(user)

# 2) services.py — BaseAccountService.sync_record()   (dipakai saat ADMIN menyimpan akun)
profile = self.build_profile(record)
```

Baris-baris itu **identik untuk semua peran**; Python memilih versi method sesuai objek yang sebenarnya (*dynamic dispatch*). Selain itu, `__str__()` di-*override* pada `PortalUser`, `AppState`, dan `UploadedDocument` agar tampil bermakna di Django Admin.

**Peran `AccountServiceFactory`:** ia **bukan** induk pewarisan. Ia hanya menyimpan tabel `_services = {"student": ..., "lecturer": ..., "admin": ...}` dan mengembalikan objek yang cocok lewat `for_role()` (pola *Factory*).

**Yang tidak diklaim:** tidak ada *method overloading* berbasis signature; bukti polimorfisme di proyek ini adalah *overriding* dan pemanggilan melalui objek terpilih.

### 4.5 Skenario demo untuk presentasi

Jalankan dari folder proyek dengan `python manage.py shell` (setelah `migrate`):

```python
# ABSTRAKSI — class abstrak tidak bisa dibuat objeknya
from portal.services import BaseAccountService
BaseAccountService()          # -> TypeError: Can't instantiate abstract class ...

# PEWARISAN — anak memakai method induk
from portal.services import StudentAccountService
StudentAccountService.sync_record is BaseAccountService.sync_record   # -> True (tidak ditulis ulang)
from portal.models import PortalUser
PortalUser.__mro__[1].__name__                                         # -> 'AbstractUser'
PortalUser.__bases__                                                   # -> (AbstractUser,)  satu induk = tunggal
StudentAccountService.__mro__                                          # rantai: Student -> Base -> ABC -> object

# POLIMORFISME — satu pemanggilan, hasil berbeda
from portal.services import AccountServiceFactory
rec = {"username": "x", "nim": "2501001", "nip": "198001", "name": "Uji"}
for role in ("student", "lecturer", "admin"):
    print(role, AccountServiceFactory.for_role(role).build_profile(rec))
# student  -> identifier '2501001' (NIM)    lecturer -> identifier '198001' (NIP)

# ENKAPSULASI — antarmuka publik vs internal
from portal.repository import KreasiStateRepository
r = KreasiStateRepository()
r.get_version()                       # publik: bisa dipanggil
r.__validate_payload({})              # -> AttributeError (nama internal tersamar oleh name-mangling)
```

**Demo di aplikasi (enkapsulasi/otorisasi):** login sebagai mahasiswa → ajukan prestasi → buka DevTools, ubah `status` menjadi "Disetujui" pada permintaan simpan → muat ulang: status tetap "Menunggu Validasi" karena server memulihkannya.

### 4.6 Tanya-jawab yang mungkin muncul

| Pertanyaan | Jawaban |
|---|---|
| Mengapa `views.py` memakai fungsi, bukan class? | Function-based view cukup untuk endpoint sederhana. OOP diterapkan pada lapisan data, akun, dan aturan akses, tempat ada banyak aturan yang perlu dikelompokkan. |
| Apa bedanya abstraksi dan enkapsulasi? | Abstraksi menetapkan **kontrak** (apa yang harus ada). Enkapsulasi **membungkus dan menyembunyikan** detail agar hanya antarmuka publik yang dipakai. |
| Apakah `__nama` benar-benar privat? | Tidak mutlak. Python hanya mengubah namanya (*name-mangling*); keamanan datang dari pemeriksaan peran di kode. |
| Mengapa ada `AccountServiceFactory`? | Agar pemanggil tidak perlu `if/else` untuk memilih class. Menambah peran baru cukup menambah satu class dan satu baris di `_services`. |
| Apakah ada pewarisan berganda? | Tidak. Setiap class hanya punya satu induk langsung. |
| Mengapa data fitur disimpan sebagai satu JSON (`AppState`)? | Untuk mempertahankan renderer JavaScript lama tanpa mengubah tampilan. Konsekuensinya data belum dipecah jadi tabel relasional (lihat bagian 10). |
| Bagaimana sandi disimpan? | Hanya sebagai hash (`set_password`). Tidak ada sandi mentah di `profile_data` maupun JSON state. |

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
- `version` pada `AppState` dinaikkan hanya bila isi data benar-benar berubah. Browser memeriksa `GET /api/state/version/` tiap 10 detik dan memuat ulang tampilan bila versinya berbeda (sinkronisasi antar perangkat).
- `saveDB()` di JavaScript memakai antrean Promise untuk menjaga urutan permintaan simpan. Pembatasan keamanan tetap dijalankan di backend.

### 6.4 Unggah, pratinjau, dan hapus dokumen

1. Frontend mengirim file dan metadata ke `POST /api/documents/upload/`.
2. `document_upload()` memeriksa sesi, keberadaan file, ukuran maksimal 10 MB, ekstensi yang diizinkan, bentuk metadata, dan beberapa syarat kepemilikan berdasarkan role/purpose.
3. File disimpan melalui `UploadedDocument.file`; metadata seperti nama asli, tipe MIME, ukuran, pengunggah, dan konteks disimpan di database.
4. `GET /api/documents/<uuid>/` memeriksa hak pratinjau dan mengembalikan file asli. Tipe konten ditentukan server dari ekstensi; hanya PDF, gambar, dan teks biasa yang tampil inline, lainnya diunduh.
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
$env:DJANGO_DEBUG = "1"      # WAJIB untuk uji lokal (HTTP biasa); tanpa ini cookie login ditandai secure
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

## 9. Deployment (simulasi/uji coba)

Docker dan lingkungan server disediakan hosting. Yang perlu diatur hanya berikut ini (contoh lengkap di `.env.example`).

**Perintah start:** `./start.sh` (menjalankan `migrate`, `collectstatic`, membuat admin awal bila belum ada, lalu `gunicorn` di `$PORT`, default 8000). Dependensi: `pip install -r requirements.txt`.

**Variabel environment:**

| Variabel | Fungsi |
|---|---|
| `DJANGO_CSRF_TRUSTED_ORIGINS` | **Wajib bila lewat HTTPS**, mis. `https://contoh.domain.id`; tanpa ini login/simpan ditolak (403). |
| `DJANGO_ALLOWED_HOSTS` | Domain dipisah koma. Kosong = semua host diterima. |
| `DB_NAME`, `DJANGO_MEDIA_ROOT` | **Arahkan ke volume persisten** (mis. `/data/db.sqlite3`, `/data/media`). Jika tetap di folder aplikasi, data dan berkas hilang saat redeploy. |
| `KREASI_ADMIN_USERNAME`, `KREASI_ADMIN_PASSWORD` | Admin awal dibuat sekali oleh `start.sh`; redeploy tidak menimpa kata sandi yang sudah diubah. |
| `DJANGO_SECRET_KEY` | Opsional; bila kosong dibuat otomatis dan disimpan di samping database. |
| `DJANGO_HTTPS=0` | Hanya bila situs diakses lewat HTTP biasa (cookie tidak diberi flag secure). |

Catatan perilaku:

- `DEBUG` kini **mati secara default**; aktifkan lokal dengan `DJANGO_DEBUG=1`.
- SQLite dikonfigurasi dengan WAL dan transaksi `IMMEDIATE` agar beberapa pengguna dapat menyimpan bersamaan tanpa "database is locked" atau saling menimpa.
- Berkas unggahan hanya dapat diakses lewat `/api/documents/<id>/` (login + izin). Tipe konten ditentukan dari ekstensi di server; hanya PDF, gambar, dan teks biasa yang ditampilkan inline, lainnya diunduh.
- **Sinkronisasi:** setiap penyimpanan menaikkan nomor versi data. Browser memeriksa versi tiap 10 detik dan memuat ulang tampilan bila pengguna lain mengubah data (ditunda saat dialog terbuka, sedang mengetik, atau ada penyimpanan berjalan). Snapshot Admin yang usang tidak menghapus prestasi/portofolio/undangan yang dibuat pengguna lain.
- `GET /healthz/` tersedia untuk health check hosting.
- Cadangkan database **dan** `DJANGO_MEDIA_ROOT`.

## 10. Batasan arsitektur yang perlu diketahui

- Sebagian besar data fitur frontend tetap disimpan dalam satu field JSON di `AppState`. Cara ini membantu mempertahankan renderer lama, tetapi bukan pengganti skema relasional terpisah untuk proyek, anggota, tahapan dokumentasi, prestasi, notifikasi, atau SKPI.
- Model akun (`PortalUser`) dan dokumen (`UploadedDocument`) tersimpan pada tabel Django tersendiri. File fisik berada di storage yang dipilih melalui `MEDIA_ROOT`.
- Proyek ini menggunakan function-based views. OOP paling terlihat pada model, repository, layanan akun, Django Admin, dan custom management command.
- Metode helper dengan awalan `__` dimaksudkan sebagai detail internal melalui name-mangling, bukan batas keamanan yang tidak dapat ditembus.
- Tes otomatis ada di `portal/tests.py` (13 tes: pembuktian 4 pilar OOP, login, pembatasan peran, sinkronisasi versi, dan unggah berkas). Jalankan dengan `python manage.py test`. Tes ini belum mencakup klik antarmuka di browser; uji tampilan tetap dilakukan manual.

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
