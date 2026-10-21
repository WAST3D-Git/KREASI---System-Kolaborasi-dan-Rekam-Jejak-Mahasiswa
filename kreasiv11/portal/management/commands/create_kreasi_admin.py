"""Perintah Django untuk membuat/memperbarui administrator awal KREASI."""
from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.repository import KreasiStateRepository, empty_portal_state
from portal.models import AppState

User = get_user_model()

class Command(BaseCommand):
    """Pewarisan tunggal dari `BaseCommand`, sesuai konvensi custom command Django.

    Django memanggil `add_arguments()` untuk konfigurasi CLI dan `handle()` untuk alur
    pembuatan akun. Transaksi menjaga akun administrator dan state awal tetap konsisten.
    """
    help = "Membuat akun administrator awal KREASI tanpa data demo."

    def add_arguments(self, parser):
        """Daftarkan opsi command tanpa memasukkan kredensial sebagai nilai wajib."""
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default=None)
        parser.add_argument("--name", default="Administrator Program Studi")
        parser.add_argument("--email", default="")

    @transaction.atomic
    def handle(self, *args, **options):
        """Validasi password, simpan akun dengan hash, lalu siapkan state kosong."""
        username = options["username"].strip()
        password = options["password"] or getpass("Kata sandi administrator (minimal 8 karakter): ")
        if len(password) < 8:
            raise CommandError("Kata sandi minimal 8 karakter.")
        name = options["name"].strip() or "Administrator Program Studi"
        email = options["email"].strip()
        user, created = User.objects.get_or_create(username=username)
        user.role = "admin"
        user.identifier = username
        user.full_name = name
        user.first_name = name[:150]
        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        profile = {
            "id": f"admin-{username}", "username": username, "role": "admin", "name": name,
            "nip": username, "email": email, "prodi": "S1 Informatika", "active": True,
            "createdAt": "Admin awal Django",
        }
        user.profile_data = profile
        try:
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError("Kata sandi tidak memenuhi kebijakan keamanan: " + "; ".join(exc.messages)) from exc
        user.save()

        state_record, _ = AppState.objects.get_or_create(key="main", defaults={"data": empty_portal_state()})
        state = state_record.data or empty_portal_state()
        state.setdefault("users", [])
        existing = next((row for row in state["users"] if row.get("username") == username), None)
        if existing is None:
            state["users"].append(profile.copy())
        else:
            existing.update(profile)
            existing.pop("password", None)
        # Data awal hanya berupa akun administrator; tidak ada proyek, prestasi, atau akun demo.
        state_record.data = state
        state_record.version += 1
        state_record.save()
        action = "dibuat" if created else "diperbarui"
        self.stdout.write(self.style.SUCCESS(f"Akun administrator '{username}' berhasil {action}."))
