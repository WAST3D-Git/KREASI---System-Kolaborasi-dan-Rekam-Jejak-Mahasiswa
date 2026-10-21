"""Model basis data KREASI dan hubungan dengan fasilitas autentikasi Django.

`PortalUser` menyimpan identitas dan metadata peran; `AppState` menampung snapshot
state frontend; `UploadedDocument` menyimpan metadata berkas serta relasi pengunggah.
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class PortalUser(AbstractUser):
    """Akun portal dengan metadata peran di samping kredensial Django.

    PEWARISAN TUNGGAL: kelas ini memiliki satu kelas induk langsung, `AbstractUser`.
    Karena itu, username, password hash, status aktif, grup, permission, dan fungsi
    autentikasi diwarisi dari Django; atribut khusus KREASI ditambahkan di bawah ini.
    """
    # Enumerasi menjaga nilai peran agar konsisten antara backend, sesi, dan frontend.
    class Role(models.TextChoices):
        STUDENT = "student", "Mahasiswa"
        LECTURER = "lecturer", "Dosen"
        ADMIN = "admin", "Administrator"

    # Atribut-atribut berikut adalah bagian data domain KREASI yang melengkapi
    # atribut bawaan AbstractUser. `profile_data` menyimpan metadata tambahan per peran.
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT, db_index=True)
    identifier = models.CharField(max_length=80, blank=True, db_index=True, help_text="NIM/NIP atau pengenal akun")
    full_name = models.CharField(max_length=150, blank=True)
    profile_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        # Override representasi objek agar admin/log menampilkan nama yang mudah dikenali.
        return self.full_name or self.username


class AppState(models.Model):
    """Agregat JSON untuk mempertahankan kontrak data renderer JavaScript KREASI.

    Model ini tidak memiliki foreign key ke `PortalUser`: satu record `key="main"`
    menampung kumpulan state yang dibatasi aksesnya oleh `KreasiStateRepository`.
    `version` dinaikkan tiap penyimpanan agar perubahan state mudah dilacak.
    """
    key = models.CharField(max_length=32, unique=True, default="main")
    data = models.JSONField(default=dict)
    version = models.PositiveBigIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KREASI state v{self.version}"


class UploadedDocument(models.Model):
    """Berkas fisik tersimpan di server, bukan hanya nama/ukuran di browser.

    Relasi `uploaded_by` adalah ForeignKey ke `PortalUser`: satu akun dapat memiliki
    banyak dokumen (`related_name="uploaded_documents"`). FileField menyimpan path
    berkas di storage `MEDIA_ROOT`, sedangkan kolom lain menyimpan metadata dan audit.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="kreasi_documents/%Y/%m/")
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, default="application/octet-stream")
    size = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.ForeignKey(PortalUser, on_delete=models.PROTECT, related_name="uploaded_documents")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Representasi ramah manusia untuk daftar dokumen di Django Admin.
        return self.original_name
