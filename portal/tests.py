"""Tes otomatis KREASI. Jalankan:  python manage.py test

Dua kelompok:
  1. OOPTests      : membuktikan 4 pilar OOP berjalan seperti yang dijelaskan di README.
  2. FeatureTests  : membuktikan login, pembatasan peran, sinkronisasi versi, dan berkas.
"""
import json
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from .models import PortalUser
from .repository import KreasiStateRepository
from .services import (AccountServiceFactory, AdminAccountService, BaseAccountService,
                       LecturerAccountService, StudentAccountService)


class OOPTests(TestCase):
    def test_abstraksi_kelas_abstrak_tidak_bisa_dibuat(self):
        with self.assertRaises(TypeError):
            BaseAccountService()

    def test_pewarisan_dan_hierarki(self):
        for anak in (StudentAccountService, LecturerAccountService, AdminAccountService):
            self.assertEqual(anak.__bases__, (BaseAccountService,))  # satu induk langsung
        self.assertEqual(PortalUser.__bases__[0].__name__, "AbstractUser")
        # sync_record ditulis sekali di induk dan dipakai ketiga anak
        self.assertIs(StudentAccountService.sync_record, BaseAccountService.sync_record)

    def test_polimorfisme_hasil_berbeda_per_peran(self):
        rec = {"username": "u", "nim": "2501001", "nip": "198001", "name": "Uji"}
        mhs = AccountServiceFactory.for_role("student").build_profile(rec)
        dsn = AccountServiceFactory.for_role("lecturer").build_profile(rec)
        self.assertEqual(mhs["identifier"], "2501001")
        self.assertEqual(dsn["identifier"], "198001")
        self.assertIn("mataKuliahDiampu", dsn)
        self.assertNotIn("mataKuliahDiampu", mhs)

    def test_factory_menolak_peran_tak_dikenal(self):
        with self.assertRaises(ValueError):
            AccountServiceFactory.for_role("tamu")

    def test_enkapsulasi_method_internal_tersamar(self):
        repo = KreasiStateRepository()
        self.assertTrue(hasattr(repo, "get_state_for"))
        self.assertFalse(hasattr(repo, "__validate_payload"))
        self.assertTrue(hasattr(repo, "_KreasiStateRepository__validate_payload"))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class FeatureTests(TestCase):
    def setUp(self):
        self.admin = Client(enforce_csrf_checks=True)
        self.admin.get("/")
        PortalUser.objects.create_superuser("admin", password="AdminKuat#2026", role="admin", full_name="Admin")
        self._login(self.admin, "admin", "AdminKuat#2026", "admin")
        got = self.admin.get("/api/state/").json()
        state = got["state"]
        state["users"] += [
            {"id": "u1", "username": "2501001", "password": "Mahasiswa#123", "role": "student", "name": "Budi",
             "nim": "2501001", "angkatan": "2025", "kelas": "A", "active": True},
        ]
        r = self._post(self.admin, "/api/state/", {"state": state, "baseVersion": got["version"]})
        self.assertTrue(r.json()["ok"], r.content)
        self.mhs = Client(enforce_csrf_checks=True)
        self.mhs.get("/")
        self._login(self.mhs, "2501001", "Mahasiswa#123", "student")

    def _post(self, client, url, data):
        return client.post(url, data=json.dumps(data), content_type="application/json",
                           HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)

    def _login(self, client, username, password, role):
        r = self._post(client, "/api/auth/login/", {"username": username, "password": password, "role": role})
        self.assertEqual(r.status_code, 200, r.content)

    def test_login_salah_ditolak_dan_peran_harus_cocok(self):
        c = Client(enforce_csrf_checks=True); c.get("/")
        self.assertEqual(self._post(c, "/api/auth/login/", {"username": "admin", "password": "salah", "role": "admin"}).status_code, 401)
        self.assertEqual(self._post(c, "/api/auth/login/", {"username": "2501001", "password": "Mahasiswa#123", "role": "admin"}).status_code, 401)

    def test_tanpa_csrf_ditolak(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post("/api/auth/login/", data="{}", content_type="application/json").status_code, 403)

    def test_state_tidak_memuat_password(self):
        users = self.mhs.get("/api/state/").json()["state"]["users"]
        self.assertTrue(all("password" not in u for u in users))

    def test_mahasiswa_tidak_bisa_menyetujui_prestasi_sendiri(self):
        got = self.mhs.get("/api/state/").json()
        st = got["state"]
        st["achievements"].append({"id": "a1", "nim": "2501001", "title": "Juara", "status": "Disetujui"})
        self.assertTrue(self._post(self.mhs, "/api/state/", {"state": st, "baseVersion": got["version"]}).json()["ok"])
        saved = self.admin.get("/api/state/").json()["state"]["achievements"]
        self.assertEqual(saved[0]["status"], "Menunggu Validasi")

    def test_versi_naik_hanya_bila_data_berubah(self):
        got = self.admin.get("/api/state/").json()
        v = self._post(self.admin, "/api/state/", {"state": got["state"], "baseVersion": got["version"]}).json()["version"]
        self.assertEqual(v, got["version"])
        self.assertEqual(self.admin.get("/api/state/version/").json()["version"], v)

    def test_snapshot_admin_usang_tidak_menghapus_prestasi_baru(self):
        stale = self.admin.get("/api/state/").json()
        got = self.mhs.get("/api/state/").json()
        st = got["state"]
        st["achievements"].append({"id": "a1", "nim": "2501001", "title": "Juara"})
        self._post(self.mhs, "/api/state/", {"state": st, "baseVersion": got["version"]})
        for u in stale["state"]["users"]:
            u.pop("password", None)
        stale["state"]["announcements"].append({"id": "n1", "title": "Info"})
        self._post(self.admin, "/api/state/", {"state": stale["state"], "baseVersion": stale["version"]})
        self.assertEqual(len(self.admin.get("/api/state/").json()["state"]["achievements"]), 1)

    def test_upload_tipe_aman_dan_ekstensi_terlarang(self):
        token = self.mhs.cookies["csrftoken"].value
        meta = json.dumps({"purpose": "portfolio", "nim": "2501001"})
        f = SimpleUploadedFile("bukti.txt", b"<script>x</script>", content_type="text/html")
        r = self.mhs.post("/api/documents/upload/", {"file": f, "metadata": meta}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 200, r.content)
        d = self.mhs.get(f"/api/documents/{r.json()['id']}/")
        self.assertTrue(d["Content-Type"].startswith("text/plain"))
        bad = SimpleUploadedFile("x.html", b"x")
        self.assertEqual(self.mhs.post("/api/documents/upload/", {"file": bad, "metadata": meta}, HTTP_X_CSRFTOKEN=token).status_code, 400)
        other = json.dumps({"purpose": "portfolio", "nim": "999"})
        r2 = self.mhs.post("/api/documents/upload/", {"file": SimpleUploadedFile("a.pdf", b"%PDF"), "metadata": other}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r2.status_code, 403)

    def test_logout_mengakhiri_sesi(self):
        self._post(self.mhs, "/api/auth/logout/", {})
        self.assertFalse(self.mhs.get("/api/session/").json()["authenticated"])
