"""Model database KREASI beserta penjelasan sederhana untuk pembelajaran OOP."""
from copy import deepcopy
from django.db import models

class TimestampedModel(models.Model):
    """Kelas dasar abstrak yang menyediakan waktu pembuatan dan perubahan data.

    Inheritance ini menghindari penulisan dua kolom waktu yang sama pada setiap model.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Waktu data pertama kali dibuat.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Waktu terakhir data diubah.")

    class Meta:
        # Abstract berarti tabel dibuat untuk setiap model turunan, bukan untuk kelas ini.
        abstract = True

class ApplicationState(TimestampedModel):
    """Menyimpan seluruh data kerja antarmuka KREASI dalam satu record JSON.

    Struktur JSON mengikuti objek data JavaScript versi HTML asal sehingga bentuk UI,
    data dummy, dan interaksi lama tetap dapat digunakan tanpa migrasi isi satu per satu.
    """
    key = models.CharField(max_length=80, unique=True, default="kreasi-default")
    payload = models.JSONField(default=dict, help_text="Data proyek, akun demo, prestasi, dan pengaturan.")

    def read_payload(self):
        """Mengembalikan salinan data agar pemanggil tidak mengubah isi model secara tidak sengaja."""
        return deepcopy(self.payload or {})

    def replace_payload(self, data):
        """Mengganti isi data melalui satu method sehingga validasi dilakukan oleh service."""
        self.payload = deepcopy(data)

    def __str__(self):
        """Menampilkan label yang mudah dikenali pada halaman admin Django."""
        return f"Status aplikasi: {self.key}"

class StoredDocument(TimestampedModel):
    """Menyimpan berkas yang diunggah untuk bukti prestasi dan dokumentasi proyek."""
    id = models.CharField(primary_key=True, max_length=40)
    file = models.FileField(upload_to="kreasi_documents/%Y/%m/")
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150, default="application/octet-stream")
    size = models.PositiveBigIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        """Menampilkan nama asli berkas pada halaman admin."""
        return self.original_name or self.id
