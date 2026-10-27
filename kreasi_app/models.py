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
    """Menyimpan data kerja KREASI dalam satu record JSON dengan getter/setter.

    Data utama tetap berada pada kolom database bernama ``payload``. Di dalam
    Python, field disimpan sebagai ``_payload_data`` dan diakses melalui property
    ``payload`` serta method get_payload()/set_payload() agar pembacaan dan perubahan
    dapat diarahkan melalui satu tempat yang jelas.
    """
    key = models.CharField(max_length=80, unique=True, default="kreasi-default")
    # Garis bawah menandai field internal; db_column menjaga nama kolom database tetap "payload".
    _payload_data = models.JSONField(
        db_column="payload",
        default=dict,
        help_text="Data proyek, akun demo, prestasi, dan pengaturan.",
    )

    @property
    def payload(self):
        """Getter: memberi salinan payload supaya pemanggil tidak mengubah data internal langsung."""
        return self.get_payload()

    @payload.setter
    def payload(self, data):
        """Setter: memvalidasi dan menyalin payload saat atribut payload diisi."""
        self.set_payload(data)

    def get_payload(self):
        """Mengambil salinan data KREASI melalui getter yang disediakan model."""
        return deepcopy(getattr(self, "_payload_data", None) or {})

    def set_payload(self, data):
        """Mengubah payload melalui setter setelah memastikan bentuk datanya dictionary.

        Penyalinan data mencegah list atau dictionary dari pemanggil mengubah state
        model secara tidak sengaja setelah setter selesai dipanggil.
        """
        if not isinstance(data, dict):
            raise ValueError("Data payload harus berupa dictionary/objek JSON.")
        self._payload_data = deepcopy(data)

    def read_payload(self):
        """Nama lama yang dipertahankan agar pemanggil sebelumnya tetap kompatibel."""
        return self.get_payload()

    def replace_payload(self, data):
        """Nama lama untuk proses tulis; perubahan tetap melewati setter yang sama."""
        self.set_payload(data)

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
