"""Layanan akun per peran (lapisan LOGIKA AKUN) — inti penerapan OOP pada KREASI.

Masalah yang diselesaikan
-------------------------
Mahasiswa, dosen, dan admin sama-sama "akun", tetapi bentuk profilnya berbeda:
  * Mahasiswa : NIM, angkatan, kelas
  * Dosen     : NIP, daftar mata kuliah yang diampu
  * Admin     : NIP/identitas admin saja
Tanpa OOP, kode akan penuh `if role == "student": ... elif role == "lecturer": ...`.
Dengan OOP, tiap peran punya class sendiri dan semuanya diperlakukan seragam.

Peta class (hierarki pewarisan)
-------------------------------
        ABC                         <- bawaan Python untuk membuat class abstrak
         |
  BaseAccountService                <- ABSTRAKSI: kontrak + proses bersama
     /       |        \\
Student   Lecturer    Admin         <- PEWARISAN HIERARKIS (3 anak, 1 induk)
AccountService  AccountService  AccountService

  AccountServiceFactory              <- BUKAN induk; hanya "pemilih" class berdasarkan peran

Siapa memanggil file ini?
-------------------------
  * views.profile_for()                   -> AccountServiceFactory.serialize()      (saat login/sesi)
  * repository.save_state() (aksi Admin)  -> AccountServiceFactory.sync_records()   (Manajemen Akun)
"""
from abc import ABC, abstractmethod
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

# Mengambil model akun aktif (PortalUser) tanpa meng-import-nya langsung.
User = get_user_model()


class BaseAccountService(ABC):
    """Kelas dasar ABSTRAK untuk semua layanan akun.

    OOP: ABSTRAKSI
        Mewarisi `ABC` dan menandai dua method dengan @abstractmethod. Artinya:
        (1) class ini TIDAK bisa dibuat objeknya langsung: BaseAccountService() -> error;
        (2) setiap class turunan WAJIB menulis kedua method itu, kalau tidak, ia juga
            tidak bisa dibuat objeknya.
        Class dasar hanya menetapkan APA yang harus ada, bukan BAGAIMANA isinya.

    OOP: PEWARISAN BERTINGKAT
        Rantai: ABC -> BaseAccountService -> (Student/Lecturer/Admin)AccountService.

    Method `sync_record()` di bawah ditulis SEKALI di sini dan dipakai ketiga anak
    (menghindari duplikasi kode). Ini pola "Template Method": kerangka langkah
    ditetapkan induk, sedangkan langkah yang berbeda-beda (build_profile) diisi anak.
    """
    # Diisi tiap anak: "student" / "lecturer" / "admin". Menjadi identitas peran class tsb.
    role = None

    @abstractmethod
    def build_profile(self, record: dict) -> dict:
        """[WAJIB DI-OVERRIDE] Ubah data akun dari frontend menjadi profil baku backend."""

    @abstractmethod
    def serialize_login_profile(self, user) -> dict:
        """[WAJIB DI-OVERRIDE] Susun data profil yang dikirim ke browser setelah login."""

    def sync_record(self, record: dict):
        """Simpan/perbarui SATU akun di tabel PortalUser dari data yang dikirim Admin.

        FITUR: Manajemen Akun (Admin) -> tombol Tambah Akun, Ubah Akun, Reset Sandi.
        DIPANGGIL OLEH: AccountServiceFactory.sync_records() (satu kali per akun).

        Langkah (sama untuk semua peran):
          1. Cari akun lama (berdasarkan username, atau ID frontend bila username diubah).
          2. Panggil self.build_profile(record) -> bagian yang BERBEDA per peran.
          3. Buang kata sandi dari data profil (sandi tidak boleh tersimpan sebagai teks).
          4. Bila ada sandi baru: validasi kebijakan keamanan, lalu simpan sebagai HASH.
          5. Simpan ke database.

        OOP: POLIMORFISME (dynamic dispatch). Pada langkah 2, `self` bisa berupa
        StudentAccountService, LecturerAccountService, atau AdminAccountService. Python
        otomatis menjalankan build_profile() milik class yang sebenarnya, tanpa `if role`.
        """
        username = str(record.get("username", "")).strip()
        if not username:
            return None

        frontend_id = str(record.get("id", ""))
        user = User.objects.filter(username=username).first()
        if user is None and frontend_id:
            # Admin mengubah NIM/NIP/username -> akun lama dikenali lewat ID frontend
            # yang tersimpan di profile_data, agar tidak terbentuk akun ganda.
            user = next((item for item in User.objects.all() if str(item.profile_data.get("id", "")) == frontend_id), None)
        is_new = user is None
        if is_new:
            user = User(username=username)

        profile = self.build_profile(record)  # <-- titik polimorfisme
        safe_profile = deepcopy(record)
        safe_profile.pop("password", None)  # sandi mentah tidak ikut disimpan
        user.username = username
        user.role = self.role
        user.identifier = str(profile.get("identifier", username))
        user.full_name = str(profile.get("name", username))[:150]
        user.email = str(profile.get("email", ""))[:254]
        user.profile_data = safe_profile
        user.is_active = bool(record.get("active", True))
        if "password" in record and str(record.get("password") or ""):
            try:
                # Aturan sandi dicek di SERVER (min. 8 karakter, bukan sandi umum, dll.),
                # bukan hanya di form browser yang bisa dilewati.
                validate_password(str(record["password"]), user)
            except ValidationError as exc:
                raise ValueError("Kata sandi tidak memenuhi kebijakan keamanan: " + "; ".join(exc.messages)) from exc
            user.set_password(str(record["password"]))  # disimpan sebagai hash, bukan teks
        elif is_new:
            user.set_unusable_password()  # akun baru tanpa sandi tidak bisa dipakai login
        user.save()
        return user


class StudentAccountService(BaseAccountService):
    """Layanan akun MAHASISWA.

    OOP: PEWARISAN TUNGGAL (satu induk langsung: BaseAccountService) + PEMENUHAN
    ABSTRAKSI (mengimplementasikan kedua method abstrak) + POLIMORFISME (override).
    Identitas utama mahasiswa = NIM.
    """
    role = "student"

    def build_profile(self, record: dict) -> dict:
        """Profil baku mahasiswa: identitas = NIM, ditambah angkatan dan kelas.
        Dipakai oleh sync_record() saat Admin menyimpan akun mahasiswa."""
        return {
            "identifier": str(record.get("nim") or record.get("username") or ""),
            "name": str(record.get("name") or "Mahasiswa"),
            "email": str(record.get("email") or ""),
            "angkatan": str(record.get("angkatan") or ""),
            "kelas": str(record.get("kelas") or ""),
        }

    def serialize_login_profile(self, user) -> dict:
        """Data sesi mahasiswa untuk browser: NIM, angkatan, kelas.
        Dipanggil lewat AccountServiceFactory.serialize() -> views.profile_for()."""
        data = deepcopy(user.profile_data or {})
        data.update({"username": user.username, "role": user.role, "identifier": user.identifier,
                     "name": user.full_name or data.get("name") or "Mahasiswa", "email": user.email,
                     "nim": data.get("nim") or user.identifier, "angkatan": data.get("angkatan", ""),
                     "kelas": data.get("kelas", "")})
        data.pop("password", None)  # pengaman tambahan: sandi tidak pernah dikirim ke browser
        return data


class LecturerAccountService(BaseAccountService):
    """Layanan akun DOSEN.

    OOP: anak ke-2 dari BaseAccountService (PEWARISAN HIERARKIS). Method yang sama
    (build_profile & serialize_login_profile) di-override dengan isi berbeda -> POLIMORFISME.
    Identitas utama dosen = NIP; membawa daftar mata kuliah yang diampu.
    """
    role = "lecturer"

    def build_profile(self, record: dict) -> dict:
        """Profil baku dosen: identitas = NIP, ditambah `mataKuliahDiampu`
        (dipakai untuk menentukan proyek mata kuliah mana yang terlihat oleh dosen)."""
        return {
            "identifier": str(record.get("nip") or record.get("username") or ""),
            "name": str(record.get("name") or "Dosen"),
            "email": str(record.get("email") or ""),
            "mataKuliahDiampu": record.get("mataKuliahDiampu", []) if isinstance(record.get("mataKuliahDiampu", []), list) else [],
        }

    def serialize_login_profile(self, user) -> dict:
        """Data sesi dosen untuk browser: NIP dan mata kuliah yang diampu."""
        data = deepcopy(user.profile_data or {})
        data.update({"username": user.username, "role": user.role, "identifier": user.identifier,
                     "name": user.full_name or data.get("name") or "Dosen", "email": user.email,
                     "nip": data.get("nip") or user.identifier,
                     "mataKuliahDiampu": data.get("mataKuliahDiampu", [])})
        data.pop("password", None)
        return data


class AdminAccountService(BaseAccountService):
    """Layanan akun ADMINISTRATOR.

    OOP: anak ke-3 dari BaseAccountService (PEWARISAN HIERARKIS). Profil admin paling
    sederhana: hanya identitas dan kontak.
    """
    role = "admin"

    def build_profile(self, record: dict) -> dict:
        """Profil baku admin: identitas, nama, email (tanpa angkatan/kelas/mata kuliah)."""
        return {
            "identifier": str(record.get("nip") or record.get("username") or "admin"),
            "name": str(record.get("name") or "Administrator"),
            "email": str(record.get("email") or ""),
        }

    def serialize_login_profile(self, user) -> dict:
        """Data sesi admin untuk browser: identitas administrator."""
        data = deepcopy(user.profile_data or {})
        data.update({"username": user.username, "role": user.role, "identifier": user.identifier,
                     "name": user.full_name or data.get("name") or "Administrator", "email": user.email,
                     "nip": data.get("nip") or user.identifier})
        data.pop("password", None)
        return data


class AccountServiceFactory:
    """Pemilih layanan akun berdasarkan peran (pola Factory).

    PENTING UNTUK PRESENTASI: class ini BUKAN bagian hierarki pewarisan dan tidak
    mewarisi apa pun. Tugasnya hanya: "diberi teks peran -> kembalikan objek layanan
    yang cocok". Dengan begitu views.py dan repository.py tidak perlu tahu class
    mana untuk peran mana (dan tidak perlu if/else).

    Seluruh method-nya @classmethod: dipanggil langsung lewat nama class, tanpa membuat objek.
    """
    # Tabel pemetaan peran -> class. Menambah peran baru cukup menambah satu baris di sini
    # (plus class layanannya). Awalan "_" = konvensi "untuk pemakaian internal class ini".
    _services = {
        "student": StudentAccountService,
        "lecturer": LecturerAccountService,
        "admin": AdminAccountService,
    }

    @classmethod
    def for_role(cls, role: str) -> BaseAccountService:
        """Buat objek layanan untuk satu peran. Peran tak dikenal -> ValueError (gagal cepat)."""
        service_class = cls._services.get(role)
        if not service_class:
            raise ValueError("Peran akun tidak dikenal.")
        return service_class()

    @classmethod
    @transaction.atomic
    def sync_records(cls, records) -> None:
        """Sinkronkan SELURUH daftar akun dari layar Manajemen Akun Admin.

        FITUR: Manajemen Akun (Admin). DIPANGGIL OLEH: repository.save_state().
        @transaction.atomic = semua-atau-tidak-sama-sekali: bila satu akun gagal
        (mis. sandi lemah), perubahan akun lain pada permintaan yang sama dibatalkan.

        Akun yang tidak lagi ada di daftar DINONAKTIFKAN (bukan dihapus) agar:
        sesi loginnya tidak bisa dipakai lagi, dan jejak dokumen (relasi PROTECT) tetap aman.
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
            cls.for_role(role).sync_record(record)  # polimorfisme: tiap peran, class berbeda
            seen.add(username)

        if seen:
            User.objects.exclude(username__in=seen).filter(role__in=["student", "lecturer", "admin"], is_superuser=False).update(is_active=False)

    @classmethod
    def serialize(cls, user) -> dict:
        """Bentuk data profil untuk browser sesuai peran `user`.

        FITUR: Login & pemulihan sesi. DIPANGGIL OLEH: views.profile_for().
        POLIMORFISME: baris pemanggilan sama untuk semua peran, tetapi hasilnya
        mengikuti class peran tersebut (mahasiswa dapat NIM, dosen dapat NIP, dst.).
        """
        return cls.for_role(user.role).serialize_login_profile(user)
