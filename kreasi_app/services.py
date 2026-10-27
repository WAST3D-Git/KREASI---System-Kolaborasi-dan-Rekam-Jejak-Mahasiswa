"""Layanan bisnis KREASI yang dipisahkan dari tampilan dan endpoint Django.

File ini memperlihatkan pola OOP dengan contoh yang langsung dipakai oleh aplikasi:
- BaseAccountService menjadi kontrak bersama layanan tiga jenis akun.
- AccountServiceFactory memilih layanan berdasarkan peran akun.
- Repository menyimpan state, sedangkan service mengatur validasi dan izin.
"""
from abc import ABC, abstractmethod
from copy import deepcopy
import json
import uuid

from django.db import transaction

from .models import ApplicationState, StoredDocument

MAX_STATE_BYTES = 20 * 1024 * 1024
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
ALLOWED_ROLES = {"student", "lecturer", "admin"}


class BaseAccountService(ABC):
    """Kelas dasar abstrak untuk layanan akun Admin, Mahasiswa, dan Dosen.

    Kelas ini menetapkan kontrak yang sama bagi semua peran. Proses umum seperti
    normalisasi record berada di sini, sementara rincian profil ditentukan oleh
    kelas turunan agar bentuk data tetap sesuai dengan kebutuhan tiap portal.
    """

    role = None  # Setiap layanan turunan menetapkan peran yang ditanganinya.

    def _base_fields(self, record):
        """Membentuk data dasar akun tanpa menyertakan kata sandi.

        Helper ini menjaga bentuk dasar profil konsisten untuk semua peran dan
        mencegah field password ikut masuk ke data profil yang akan ditampilkan.
        """
        return {
            "id": str(record.get("id", "")),
            "username": str(record.get("username", "")),
            "role": self.role,
            "name": str(record.get("name", "")),
            "email": str(record.get("email", "")),
            "active": bool(record.get("active", True)),
            "prodi": str(record.get("prodi", "")),
            "avatar": str(record.get("avatar", "")),
        }

    def sync_record(self, record):
        """Menormalkan record akun sebelum dipakai oleh proses layanan lain.

        Method ini tidak menyimpan data baru ke database; ia membuat salinan
        profil yang bentuknya konsisten dan membiarkan record sumber tetap utuh.
        Implementasi profil dipilih otomatis melalui method milik kelas turunan.
        """
        if not isinstance(record, dict):
            raise ValueError("Data akun harus berbentuk objek/dictionary.")
        return self.build_profile(dict(record))

    @abstractmethod
    def build_profile(self, record: dict) -> dict:
        """Kontrak untuk menormalkan field khusus Mahasiswa, Dosen, atau Admin."""
        raise NotImplementedError

    @abstractmethod
    def serialize_login_profile(self, user: dict) -> dict:
        """Kontrak untuk menyiapkan profil aman yang boleh dikirim ke frontend."""
        raise NotImplementedError


class StudentAccountService(BaseAccountService):
    """Menyediakan normalisasi dan profil sesi khusus akun Mahasiswa.

    Data tambahan seperti NIM, angkatan, kelas, IPK, dan mata kuliah yang diambil
    digunakan oleh fitur Profil & Talenta, proyek mata kuliah, serta dashboard.
    """

    role = "student"

    def build_profile(self, record: dict) -> dict:
        """Menggabungkan field umum dengan data akademik mahasiswa."""
        profile = self._base_fields(record)
        profile.update({
            "nim": str(record.get("nim", "")),
            "angkatan": str(record.get("angkatan", "")),
            "kelas": str(record.get("kelas", "")),
            "gpa": record.get("gpa"),
            # Salin daftar agar perubahan pada profil tidak mengubah record sumber.
            "mataKuliahDiambil": list(record.get("mataKuliahDiambil", []))
            if isinstance(record.get("mataKuliahDiambil", []), list) else [],
        })
        return profile

    def serialize_login_profile(self, user: dict) -> dict:
        """Mengirim identitas dan ringkasan akademik mahasiswa tanpa kata sandi."""
        profile = self.build_profile(user)
        allowed = ("id", "username", "role", "name", "email", "active", "avatar",
                   "prodi", "nim", "angkatan", "kelas", "gpa", "mataKuliahDiambil")
        return {key: profile[key] for key in allowed if key in profile}


class LecturerAccountService(BaseAccountService):
    """Menyediakan data profil yang diperlukan akun Dosen.

    Informasi NIP, jabatan, keahlian, mata kuliah, pendidikan, dan publikasi
    berhubungan langsung dengan fitur Profil Dosen, Talent Pool, dan Manajemen Proyek.
    """

    role = "lecturer"

    def build_profile(self, record: dict) -> dict:
        """Menggabungkan field umum dengan informasi akademik dosen."""
        profile = self._base_fields(record)
        for field in ("bidangKeahlian", "mataKuliahDiampu", "pendidikan", "publikasi"):
            value = record.get(field, [])
            profile[field] = list(value) if isinstance(value, list) else []
        profile.update({
            "nip": str(record.get("nip", "")),
            "nidn": str(record.get("nidn", "")),
            "jabatanFungsional": str(record.get("jabatanFungsional", "")),
        })
        return profile

    def serialize_login_profile(self, user: dict) -> dict:
        """Mengirim identitas dan ringkasan pengampuan dosen ke frontend."""
        profile = self.build_profile(user)
        allowed = ("id", "username", "role", "name", "email", "active", "avatar",
                   "prodi", "nip", "nidn", "jabatanFungsional", "bidangKeahlian",
                   "mataKuliahDiampu")
        return {key: profile[key] for key in allowed if key in profile}


class AdminAccountService(BaseAccountService):
    """Menyediakan profil akun Administrator Program Studi.

    Data identitas dan jabatan digunakan untuk konteks pengelolaan akun, validasi
    prestasi, data master, rekapitulasi, finalisasi, dan pencetakan SKPI.
    """

    role = "admin"

    def build_profile(self, record: dict) -> dict:
        """Menggabungkan field umum dengan identitas administrator."""
        profile = self._base_fields(record)
        profile.update({
            "nip": str(record.get("nip", "")),
            "jabatan": str(record.get("jabatan", "")),
        })
        return profile

    def serialize_login_profile(self, user: dict) -> dict:
        """Mengirim data minimum administrator yang diperlukan antarmuka."""
        profile = self.build_profile(user)
        allowed = ("id", "username", "role", "name", "email", "active", "avatar",
                   "prodi", "nip", "jabatan")
        return {key: profile[key] for key in allowed if key in profile}


class AccountServiceFactory:
    """Memilih layanan akun tanpa membuat view memeriksa setiap peran satu per satu.

    Factory ini menjadi satu pintu untuk mendapatkan layanan yang tepat dan untuk
    membuat payload profil login yang aman bagi frontend KREASI.
    """

    _services = {
        "student": StudentAccountService,
        "lecturer": LecturerAccountService,
        "admin": AdminAccountService,
    }

    @classmethod
    def for_role(cls, role: str) -> BaseAccountService:
        """Mengembalikan service sesuai peran atau menolak peran yang tidak dikenal."""
        service_class = cls._services.get(str(role or ""))
        if service_class is None:
            raise ValueError("Peran akun tidak dikenal.")
        return service_class()

    @classmethod
    def normalize(cls, record: dict) -> dict:
        """Menormalkan satu record dengan layanan berdasarkan peran record itu."""
        if not isinstance(record, dict):
            raise ValueError("Data akun harus berbentuk objek/dictionary.")
        service = cls.for_role(record.get("role"))
        return service.sync_record(record)

    @classmethod
    def serialize(cls, user: dict) -> dict:
        """Membuat profil login aman melalui method yang sesuai dengan jenis akun."""
        service = cls.for_role(user.get("role"))
        normalized = service.sync_record(user)
        # Pemanggilan ini bersifat polimorfik: implementasi yang dijalankan mengikuti role.
        return service.serialize_login_profile(normalized)


class BaseStateRepository(ABC):
    """Kontrak abstrak untuk mengambil dan menyimpan state aplikasi KREASI."""

    @abstractmethod
    def load(self, key="kreasi-default"):
        """Mengambil state dengan kunci tertentu; detail baca disediakan turunan."""
        raise NotImplementedError

    @abstractmethod
    def save(self, data, key="kreasi-default"):
        """Menyimpan state; detail tulis disediakan turunan."""
        raise NotImplementedError


class DjangoStateRepository(BaseStateRepository):
    """Implementasi repository yang membaca dan menulis record melalui ORM Django."""

    def load(self, key="kreasi-default"):
        """Mengambil salinan payload agar pemanggil tidak mengubah model tanpa sengaja."""
        record = ApplicationState.objects.filter(key=key).first()
        return record.get_payload() if record else None

    @transaction.atomic
    def save(self, data, key="kreasi-default"):
        """Menyimpan payload dalam transaksi agar perubahan tetap utuh."""
        record, _created = ApplicationState.objects.select_for_update().get_or_create(key=key)
        record.set_payload(data)
        record.save()
        return record


class PermissionService:
    """Mengumpulkan aturan dasar peran yang digunakan endpoint state dan dokumen."""

    def role_can_write(self, role):
        """Memastikan perubahan lanjutan hanya datang dari sesi dengan peran dikenal."""
        return role in ALLOWED_ROLES

    def role_can_manage_documents(self, role):
        """Memastikan fitur berkas hanya dipakai setelah sesi peran dikenali tersedia."""
        return role in ALLOWED_ROLES


class StateService:
    """Mengatur validasi dan penyimpanan state tanpa mengikat diri ke detail repository.

    Enkapsulasi diterapkan lewat satu pintu baca/tulis. Repository dan aturan izin
    disuntikkan sebagai objek, bukan melalui multiple inheritance, sehingga tiap
    bagian mudah diganti atau diuji secara terpisah.
    """

    state_key = "kreasi-default"

    def __init__(self, repository=None, permissions=None):
        """Menyiapkan repository serta layanan izin, memakai implementasi Django secara default."""
        self.repository = repository or DjangoStateRepository()
        self.permissions = permissions or PermissionService()

    def load_state(self):
        """Mengambil state KREASI yang tersimpan atau None ketika aplikasi masih baru."""
        return self.repository.load(self.state_key)

    def store_state(self, data, actor_role=None):
        """Memvalidasi ukuran dan bentuk payload sebelum menyerahkannya ke repository.

        Penyimpanan pertama diperbolehkan agar frontend dapat memasukkan data dummy.
        Setelah ada record, setiap perubahan perlu berasal dari sesi dengan peran sah.
        """
        if not isinstance(data, dict):
            raise ValueError("Format data harus berupa objek JSON.")
        encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > MAX_STATE_BYTES:
            raise ValueError("Data aplikasi terlalu besar untuk disimpan.")
        already_initialized = ApplicationState.objects.filter(key=self.state_key).exists()
        if already_initialized and not self.permissions.role_can_write(actor_role):
            raise PermissionError("Silakan masuk menggunakan akun demo sebelum mengubah data.")
        # Salinan data memisahkan objek dari pemanggil sebelum disimpan ke database.
        return self.repository.save(deepcopy(data), self.state_key)


class DocumentService:
    """Mengelola file bukti prestasi dan dokumentasi proyek pada server Django."""

    max_file_size = MAX_DOCUMENT_BYTES

    def __init__(self, permissions=None):
        """Menerima aturan izin agar pemeriksaan akses dapat dipakai ulang dan diuji."""
        self.permissions = permissions or PermissionService()

    def create(self, uploaded_file, metadata=None, actor_role=None):
        """Memeriksa izin dan ukuran, lalu menyimpan berkas serta metadata dokumen."""
        if not self.permissions.role_can_manage_documents(actor_role):
            raise PermissionError("Silakan masuk terlebih dahulu untuk mengunggah berkas.")
        if uploaded_file is None:
            raise ValueError("Berkas belum dipilih.")
        if uploaded_file.size > self.max_file_size:
            raise ValueError("Ukuran berkas melebihi batas 25 MB.")
        # ID acak dipakai sebagai kunci aman; nama asli tetap disimpan untuk tampilan.
        document = StoredDocument(
            id="DOC-" + uuid.uuid4().hex[:16].upper(),
            original_name=uploaded_file.name[:255],
            content_type=uploaded_file.content_type or "application/octet-stream",
            size=uploaded_file.size,
            metadata=metadata if isinstance(metadata, dict) else {},
        )
        document.file.save(uploaded_file.name, uploaded_file, save=False)
        document.save()
        return document

    def get(self, document_id, actor_role=None):
        """Mencari berkas untuk dipratinjau atau diunduh setelah izin diperiksa."""
        if not self.permissions.role_can_manage_documents(actor_role):
            raise PermissionError("Silakan masuk terlebih dahulu untuk membuka berkas.")
        return StoredDocument.objects.filter(pk=document_id).first()

    def delete(self, document_id, actor_role=None):
        """Menghapus file fisik dan record metadata yang merujuk pada file tersebut."""
        if not self.permissions.role_can_manage_documents(actor_role):
            raise PermissionError("Silakan masuk terlebih dahulu untuk menghapus berkas.")
        document = StoredDocument.objects.filter(pk=document_id).first()
        if not document:
            return False
        # FileField.delete menghapus file server sebelum record database dihapus.
        document.file.delete(save=False)
        document.delete()
        return True
