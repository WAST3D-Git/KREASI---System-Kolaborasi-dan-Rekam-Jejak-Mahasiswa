"""Layanan akun dan serialisasi profil untuk KREASI.

Modul ini memisahkan kebijakan akun dari function-based views sehingga alur sinkronisasi
serta format profil peran dapat dibaca, dirawat, dan diuji secara terpisah.
"""
from abc import ABC, abstractmethod
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

User = get_user_model()


class BaseAccountService(ABC):
    """Kontrak abstrak untuk layanan akun semua peran.

    ABSTRAKSI: `ABC` dan `@abstractmethod` mengharuskan subclass mengimplementasikan
    `build_profile()` dan `serialize_login_profile()`. PEWARISAN: kelas ini mewarisi
    `ABC`; tiga layanan konkret kemudian mewarisi kelas ini (pola bertingkat sekaligus
    hierarkis). `role` diisi oleh setiap subclass sebagai identitas perannya.
    """
    role = None

    @abstractmethod
    def build_profile(self, record: dict) -> dict:
        """Kontrak untuk mengubah record frontend menjadi atribut profil yang konsisten."""

    @abstractmethod
    def serialize_login_profile(self, user) -> dict:
        """Kontrak untuk membentuk profil sesi yang aman dan sesuai peran bagi UI."""

    def sync_record(self, record: dict):
        """Sinkronkan satu record UI dengan akun autentikasi Django.

        Alur umum yang dipakai semua peran: cari akun lama, bangun profil melalui
        `self.build_profile(record)`, hapus kata sandi dari metadata, validasi dan hash
        kata sandi baru bila ada, lalu simpan `PortalUser`. Pemanggilan `self.build_profile`
        memakai dynamic dispatch, sehingga implementasi subclass yang dipanggil.
        """
        username = str(record.get("username", "")).strip()
        if not username:
            return None

        frontend_id = str(record.get("id", ""))
        user = User.objects.filter(username=username).first()
        if user is None and frontend_id:
            # Membantu akun tetap dikenali saat Admin mengubah NIM/NIP/username.
            user = next((item for item in User.objects.all() if str(item.profile_data.get("id", "")) == frontend_id), None)
        is_new = user is None
        if is_new:
            user = User(username=username)

        profile = self.build_profile(record)
        safe_profile = deepcopy(record)
        safe_profile.pop("password", None)  # Kata sandi hanya disimpan oleh Django sebagai hash.
        user.username = username
        user.role = self.role
        user.identifier = str(profile.get("identifier", username))
        user.full_name = str(profile.get("name", username))[:150]
        user.email = str(profile.get("email", ""))[:254]
        user.profile_data = safe_profile
        user.is_active = bool(record.get("active", True))
        if "password" in record and str(record.get("password") or ""):
            try:
                # Validasi kata sandi dilakukan di backend; aturan tidak hanya mengandalkan form JS.
                validate_password(str(record["password"]), user)
            except ValidationError as exc:
                raise ValueError("Kata sandi tidak memenuhi kebijakan keamanan: " + "; ".join(exc.messages)) from exc
            user.set_password(str(record["password"]))
        elif is_new:
            user.set_unusable_password()
        user.save()
        return user


class StudentAccountService(BaseAccountService):
    """Layanan akun mahasiswa.

    PEWARISAN TUNGGAL: langsung mewarisi `BaseAccountService`; bersama dua layanan lain
    membentuk pewarisan hierarkis. Implementasi metode abstrak khusus untuk NIM, angkatan,
    kelas, dan bentuk profil mahasiswa.
    """
    role = "student"

    def build_profile(self, record: dict) -> dict:
        # Override kontrak abstrak: identitas akun mahasiswa utamanya adalah NIM.
        return {
            "identifier": str(record.get("nim") or record.get("username") or ""),
            "name": str(record.get("name") or "Mahasiswa"),
            "email": str(record.get("email") or ""),
            "angkatan": str(record.get("angkatan") or ""),
            "kelas": str(record.get("kelas") or ""),
        }

    def serialize_login_profile(self, user) -> dict:
        # Polimorfisme: payload login mahasiswa menyertakan NIM, angkatan, dan kelas.
        data = deepcopy(user.profile_data or {})
        data.update({"username": user.username, "role": user.role, "identifier": user.identifier,
                     "name": user.full_name or data.get("name") or "Mahasiswa", "email": user.email,
                     "nim": data.get("nim") or user.identifier, "angkatan": data.get("angkatan", ""),
                     "kelas": data.get("kelas", "")})
        data.pop("password", None)
        return data


class LecturerAccountService(BaseAccountService):
    """Layanan akun dosen; data pengajaran dibawa ke profil sesi.

    PEWARISAN TUNGGAL: langsung mewarisi `BaseAccountService`, sama seperti layanan
    mahasiswa dan admin. `build_profile()` serta `serialize_login_profile()` dioverride
    supaya NIP dan mata kuliah diampu digunakan, bukan metadata angkatan/kelas mahasiswa.
    """
    role = "lecturer"

    def build_profile(self, record: dict) -> dict:
        # Override kontrak abstrak: identitas akun dosen utamanya adalah NIP.
        return {
            "identifier": str(record.get("nip") or record.get("username") or ""),
            "name": str(record.get("name") or "Dosen"),
            "email": str(record.get("email") or ""),
            "mataKuliahDiampu": record.get("mataKuliahDiampu", []) if isinstance(record.get("mataKuliahDiampu", []), list) else [],
        }

    def serialize_login_profile(self, user) -> dict:
        # Polimorfisme: payload dosen menyertakan NIP dan mata kuliah yang diampu.
        data = deepcopy(user.profile_data or {})
        data.update({"username": user.username, "role": user.role, "identifier": user.identifier,
                     "name": user.full_name or data.get("name") or "Dosen", "email": user.email,
                     "nip": data.get("nip") or user.identifier,
                     "mataKuliahDiampu": data.get("mataKuliahDiampu", [])})
        data.pop("password", None)
        return data


class AdminAccountService(BaseAccountService):
    """Layanan profil administrator untuk pengelolaan akun dan data master.

    PEWARISAN TUNGGAL: implementasi konkret ketiga yang mewarisi `BaseAccountService`.
    Profil admin disederhanakan ke identitas dan informasi kontak yang diperlukan UI.
    """
    role = "admin"

    def build_profile(self, record: dict) -> dict:
        # Override kontrak abstrak dengan aturan identitas administrator.
        return {
            "identifier": str(record.get("nip") or record.get("username") or "admin"),
            "name": str(record.get("name") or "Administrator"),
            "email": str(record.get("email") or ""),
        }

    def serialize_login_profile(self, user) -> dict:
        # Polimorfisme: profil admin mengirim identitas yang dibutuhkan halaman administrasi.
        data = deepcopy(user.profile_data or {})
        data.update({"username": user.username, "role": user.role, "identifier": user.identifier,
                     "name": user.full_name or data.get("name") or "Administrator", "email": user.email,
                     "nip": data.get("nip") or user.identifier})
        data.pop("password", None)
        return data


class AccountServiceFactory:
    """Titik pemilihan layanan akun berdasarkan peran.

    Factory ini bukan bagian dari hierarki pewarisan layanan. Ia menyimpan pemetaan
    peran ke kelas konkret, lalu mengembalikan objek yang sesuai supaya view/repository
    tidak perlu mengetahui detail format profil dari setiap role.
    """
    # Satu sumber pemetaan role -> implementasi layanan. Garis bawah menunjukkan detail
    # internal kelas; ini konvensi akses internal Python, bukan proteksi keamanan mutlak.
    _services = {
        "student": StudentAccountService,
        "lecturer": LecturerAccountService,
        "admin": AdminAccountService,
    }

    @classmethod
    def for_role(cls, role: str) -> BaseAccountService:
        """Buat objek layanan konkret; gagal cepat jika nilai role tidak dikenal."""
        service_class = cls._services.get(role)
        if not service_class:
            raise ValueError("Peran akun tidak dikenal.")
        return service_class()

    @classmethod
    @transaction.atomic
    def sync_records(cls, records) -> None:
        """Sinkronkan daftar akun yang dikirim Admin sebagai satu transaksi DB.

        Setiap record diarahkan ke layanan melalui `for_role()`. Akun yang tak lagi ada
        dalam daftar dinonaktifkan agar sesi login tidak tetap dapat dipakai.
        """
        seen = set()
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict):
                continue
            role = str(record.get("role", ""))
            if role not in cls._services:
                continue
            username = str(record.get("username", "")).strip()
            if not username or len(username) > 150:
                continue
            cls.for_role(role).sync_record(record)
            seen.add(username)

        # Enkapsulasi kebijakan sinkronisasi: akun yang dihapus dari Manajemen Akun
        # dinonaktifkan di tabel autentikasi, bukan dihapus beserta jejak auditnya.
        if seen:
            User.objects.exclude(username__in=seen).filter(role__in=["student", "lecturer", "admin"], is_superuser=False).update(is_active=False)

    @classmethod
    def serialize(cls, user) -> dict:
        """Serialisasi polimorfik: metode yang sama menghasilkan payload sesuai role.

        `for_role()` memilih objek subclass, kemudian Python menjalankan versi override
        `serialize_login_profile()` milik Student/Lecturer/AdminAccountService.
        """
        return cls.for_role(user.role).serialize_login_profile(user)
