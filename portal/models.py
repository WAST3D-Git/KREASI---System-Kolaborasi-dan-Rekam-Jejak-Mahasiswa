"""Model basis data KREASI (lapisan DATA).

Peta singkat untuk presentasi
-----------------------------
Ada 3 tabel database, masing-masing dibuat dari satu class Python (model Django / ORM):

| Class              | Tabel yang dibuat    | Dipakai oleh fitur                                   |
|--------------------|----------------------|------------------------------------------------------|
| PortalUser         | portal_portaluser    | Login, peran (mahasiswa/dosen/admin), Manajemen Akun |
| AppState           | portal_appstate      | Semua data fitur: proyek, prestasi, SKPI, dll        |
| UploadedDocument   | portal_uploadeddocument | Unggah bukti prestasi, portofolio, dokumentasi    |

Konsep OOP yang paling terlihat di file ini
-------------------------------------------
* PEWARISAN TUNGGAL : PortalUser(AbstractUser) -> mewarisi fitur login bawaan Django.
* POLIMORFISME      : method __str__() di-override pada ketiga class.
* ENKAPSULASI       : data + aturan data dibungkus dalam satu class (mis. pilihan peran
                      dikunci di enum `Role`, bukan teks bebas yang tersebar di banyak tempat).
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class PortalUser(AbstractUser):
    """Akun pengguna KREASI: mahasiswa, dosen, atau admin.

    FITUR YANG MEMAKAI
        - Login/Logout            -> views.login_view / logout_view
        - Manajemen Akun (Admin)  -> services.sync_record menulis ke tabel ini
        - Pembatasan menu & data  -> atribut `role` dibaca repository & views

    OOP: PEWARISAN TUNGGAL
        Hanya ada SATU induk langsung: `AbstractUser` (bawaan Django). Dari induk ini
        kita mendapat TANPA menulis ulang: username, password (hash), email, is_active,
        is_staff, is_superuser, grup & permission, serta method set_password() dan
        check_password(). Kita hanya MENAMBAH 4 atribut khusus KREASI di bawah.

        Mengapa tidak membuat sendiri? Menulis sistem login dari nol rawan celah
        keamanan; pewarisan memungkinkan memakai komponen yang sudah teruji.
    """

    # Enum peran. Dipakai agar nilai peran hanya salah satu dari tiga pilihan ini
    # (mencegah salah ketik seperti "Student"/"mhs" yang membuat akses bocor/rusak).
    class Role(models.TextChoices):
        STUDENT = "student", "Mahasiswa"
        LECTURER = "lecturer", "Dosen"
        ADMIN = "admin", "Administrator"

    # --- Atribut tambahan KREASI (di luar bawaan AbstractUser) ---
    # Peran akun. db_index=True mempercepat pencarian akun per peran.
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT, db_index=True)
    # NIM (mahasiswa) atau NIP (dosen). Dipakai sebagai "identitas" untuk mencocokkan
    # kepemilikan data (mis. prestasi milik NIM tertentu) di repository.py.
    identifier = models.CharField(max_length=80, blank=True, db_index=True, help_text="NIM/NIP atau pengenal akun")
    full_name = models.CharField(max_length=150, blank=True)
    # Data profil tambahan per peran (angkatan, kelas, mata kuliah diampu, dst.) dalam JSON.
    # Password TIDAK pernah disimpan di sini; password hanya ada sebagai hash di kolom bawaan.
    profile_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        # POLIMORFISME (method overriding): menimpa __str__() milik induk agar Django Admin
        # dan log menampilkan nama lengkap, bukan teks standar "PortalUser object (1)".
        return self.full_name or self.username


class AppState(models.Model):
    """Penyimpan SEMUA data fitur dalam satu record JSON (kunci "main").

    FITUR YANG MEMAKAI
        Proyek, prestasi, portofolio, undangan, notifikasi, pengumuman, data master
        (kategori, mata kuliah, poin MEXS), dan finalisasi SKPI.

    MENGAPA SATU RECORD JSON?
        Frontend (index.html) sejak awal bekerja dengan satu objek JavaScript besar (`db`).
        Menyimpannya apa adanya menjaga tampilan & interaksi tetap sama persis. Konsekuensinya
        (dijelaskan jujur di README): data ini belum dipecah menjadi tabel relasional.

    `version` naik 1 setiap kali isi berubah. Browser lain membandingkan nomor ini untuk
    mengetahui "ada data baru" dan menyegarkan tampilan (fitur sinkronisasi multi-pengguna).

    Tidak ada akses langsung ke class ini dari views; semua lewat KreasiStateRepository
    (lihat repository.py) -> itulah ENKAPSULASI.
    """
    key = models.CharField(max_length=32, unique=True, default="main")
    data = models.JSONField(default=dict)
    version = models.PositiveBigIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # POLIMORFISME (overriding __str__): tampil sebagai "KREASI state v12" di Django Admin.
        return f"KREASI state v{self.version}"


class UploadedDocument(models.Model):
    """Satu berkas yang diunggah pengguna (file fisik + catatannya di database).

    FITUR YANG MEMAKAI
        Bukti prestasi, portofolio, lampiran proyek, dan dokumentasi tahapan proyek
        (views.document_upload / document_detail / document_delete).

    PEMBAGIAN TUGAS PENYIMPANAN
        - File aslinya  -> folder MEDIA_ROOT (lewat FileField)
        - Catatan/metadata (nama asli, ukuran, siapa yang unggah, untuk proyek mana)
          -> tabel database ini

    RELASI: `uploaded_by` = ForeignKey ke PortalUser (relasi 1 akun : banyak dokumen).
        on_delete=PROTECT -> akun yang masih punya dokumen tidak bisa dihapus langsung.
        Karena itu sistem menonaktifkan akun (is_active=False), bukan menghapusnya.
    """
    # UUID dipakai sebagai ID (bukan angka 1,2,3) agar alamat berkas tidak mudah ditebak.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="kreasi_documents/%Y/%m/")  # dikelompokkan per tahun/bulan
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, default="application/octet-stream")
    size = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.ForeignKey(PortalUser, on_delete=models.PROTECT, related_name="uploaded_documents")
    # Konteks unggahan, mis. {"purpose": "milestone", "projectId": "...", "groupId": "..."}.
    # Dipakai views.py untuk memutuskan siapa yang boleh melihat/menghapus.
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # POLIMORFISME (overriding __str__): daftar dokumen di Django Admin menampilkan nama berkas.
        return self.original_name
