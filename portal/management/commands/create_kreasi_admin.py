"""Perintah terminal untuk membuat akun ADMIN pertama.

Mengapa perlu? Aplikasi tidak menyertakan akun contoh; akun mahasiswa dan dosen dibuat oleh
Admin melalui menu Manajemen Akun. Admin pertama harus dibuat lewat terminal:

    python manage.py create_kreasi_admin --username admin

Sandi diminta lewat prompt tersembunyi, atau dari variabel KREASI_ADMIN_PASSWORD bila tanpa
terminal (hosting). Opsi --only-if-missing membuat perintah aman dijalankan di setiap deploy.
"""
import os
import sys
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
    """OOP: PEWARISAN TUNGGAL dari `BaseCommand` (bawaan Django). Django otomatis mengenali file
    di folder management/commands sebagai perintah `manage.py <nama-file>`. Kita mengisi dua
    method yang dipanggil Django: add_arguments() (opsi CLI) dan handle() (isi perintah).
    @transaction.atomic membuat akun admin dan data awal tersimpan bersamaan atau batal bersamaan.
    """
    help = "Membuat akun administrator awal KREASI tanpa data demo."

    def add_arguments(self, parser):
        """Mendaftarkan opsi: --username, --password, --name, --email, --only-if-missing."""
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default=None)
        parser.add_argument("--name", default="Administrator Program Studi")
        parser.add_argument("--email", default="")
        parser.add_argument("--only-if-missing", action="store_true",
                            help="Lewati bila akun sudah ada (aman dijalankan di setiap deploy).")

    @transaction.atomic
    def handle(self, *args, **options):
        """Isi perintah: (1) lewati bila --only-if-missing dan akun ada; (2) ambil sandi; (3) buat/perbarui
        akun admin (sandi di-hash, dicek kebijakan keamanan); (4) catat admin di data aplikasi (AppState)
        agar tampil di menu Manajemen Akun.
        """
        username = options["username"].strip()
        if options["only_if_missing"] and User.objects.filter(username=username).exists():
            self.stdout.write(f"Akun '{username}' sudah ada; dilewati.")
            return
        password = options["password"] or os.environ.get("KREASI_ADMIN_PASSWORD")
        if not password:
            if not sys.stdin.isatty():
                raise CommandError("Tanpa terminal interaktif, set KREASI_ADMIN_PASSWORD atau gunakan --password.")
            password = getpass("Kata sandi administrator (minimal 8 karakter): ")
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
