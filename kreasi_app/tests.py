"""Pengujian model, service OOP, dan endpoint utama aplikasi KREASI."""
import json

from django.test import TestCase, Client

from .models import ApplicationState
from .services import (
    AccountServiceFactory,
    AdminAccountService,
    BaseAccountService,
    BaseStateRepository,
    DjangoStateRepository,
    LecturerAccountService,
    StateService,
    StudentAccountService,
)


class AccountServiceTests(TestCase):
    """Menguji kontrak BaseAccountService dan pemilihan service untuk tiga peran."""

    def test_factory_selects_service_for_each_role(self):
        """Factory harus mengembalikan turunan yang sesuai dengan peran akun."""
        self.assertIsInstance(AccountServiceFactory.for_role("student"), StudentAccountService)
        self.assertIsInstance(AccountServiceFactory.for_role("lecturer"), LecturerAccountService)
        self.assertIsInstance(AccountServiceFactory.for_role("admin"), AdminAccountService)

    def test_base_account_service_is_abstract(self):
        """Kelas dasar tidak boleh dipakai langsung karena kontraknya belum lengkap."""
        with self.assertRaises(TypeError):
            BaseAccountService()

    def test_student_profile_keeps_academic_fields_without_password(self):
        """Profil mahasiswa menyertakan data yang dibutuhkan portal tanpa mengekspos password."""
        raw_user = {
            "id": "u-1", "username": "250001", "password": "password123", "role": "student",
            "name": "Aditya Pratama", "nim": "250001", "angkatan": "2025", "kelas": "A",
            "mataKuliahDiambil": ["Basis Data"], "active": True,
        }
        profile = AccountServiceFactory.serialize(raw_user)
        self.assertEqual(profile["role"], "student")
        self.assertEqual(profile["nim"], "250001")
        self.assertEqual(profile["mataKuliahDiambil"], ["Basis Data"])
        self.assertNotIn("password", profile)

    def test_lecturer_profile_contains_course_assignments(self):
        """Profil dosen menampilkan mata kuliah yang diampu sesuai fitur portal dosen."""
        raw_user = {
            "username": "1990", "role": "lecturer", "name": "Dosen Demo", "nip": "1990",
            "mataKuliahDiampu": [{"course": "Basis Data", "kelas": ["A"]}],
        }
        profile = AccountServiceFactory.serialize(raw_user)
        self.assertEqual(profile["role"], "lecturer")
        self.assertEqual(profile["nip"], "1990")
        self.assertEqual(profile["mataKuliahDiampu"][0]["course"], "Basis Data")

    def test_admin_profile_contains_role_details(self):
        """Profil admin menampilkan jabatan administratif dan menghilangkan field rahasia."""
        raw_user = {
            "username": "admin", "password": "password123", "role": "admin",
            "name": "Admin Demo", "nip": "1985", "jabatan": "Administrator Program Studi",
        }
        profile = AccountServiceFactory.serialize(raw_user)
        self.assertEqual(profile["role"], "admin")
        self.assertEqual(profile["jabatan"], "Administrator Program Studi")
        self.assertNotIn("password", profile)

    def test_unknown_role_is_rejected(self):
        """Factory menolak peran selain mahasiswa, dosen, atau administrator."""
        with self.assertRaises(ValueError):
            AccountServiceFactory.for_role("visitor")


class ApplicationStateGetterSetterTests(TestCase):
    """Memastikan getter/setter menjaga payload sebagai data yang dikelola model."""

    def test_getter_returns_a_copy(self):
        """Perubahan pada salinan hasil getter tidak boleh mengubah payload di model."""
        state = ApplicationState.objects.create(
            key="getter-copy-test",
            payload={"projects": [{"id": "PRJ-001"}]},
        )
        # Pastikan getter juga bekerja setelah data dibaca lagi dari database.
        state.refresh_from_db()
        copied_payload = state.get_payload()
        copied_payload["projects"][0]["id"] = "CHANGED"

        self.assertEqual(state.get_payload()["projects"][0]["id"], "PRJ-001")

    def test_setter_copies_input_and_property_uses_getter_setter(self):
        """Setter dan property payload harus menyalin data input sebelum disimpan."""
        state = ApplicationState(key="getter-setter-test")
        original = {"courses": ["Basis Data"]}
        state.set_payload(original)
        original["courses"].append("Data yang diubah dari luar")
        state.save()
        state.refresh_from_db()

        self.assertEqual(state.payload, {"courses": ["Basis Data"]})
        state.payload = {"courses": ["Rekayasa Perangkat Lunak"]}
        state.save()
        state.refresh_from_db()
        self.assertEqual(state.get_payload(), {"courses": ["Rekayasa Perangkat Lunak"]})

    def test_setter_rejects_non_dictionary_payload(self):
        """Setter menolak tipe data yang bukan objek JSON yang digunakan sebagai state."""
        state = ApplicationState(key="getter-setter-invalid-test")
        with self.assertRaises(ValueError):
            state.set_payload(["bukan", "dictionary"])


class StateServiceTests(TestCase):
    """Memastikan state tersimpan, terisolasi, dan akses tanpa login ditolak setelah bootstrap."""

    def setUp(self):
        # Database tes terpisah sehingga tidak menyentuh data demo nyata.
        self.service = StateService()

    def test_state_round_trip(self):
        """Data JSON yang ditulis service harus dapat dibaca kembali tanpa perubahan."""
        sample = {"projects": [{"id": "PRJ-TEST"}], "masterData": {"courses": ["Basis Data"]}}
        self.service.store_state(sample, actor_role=None)
        self.assertEqual(self.service.load_state(), sample)

    def test_store_is_rejected_after_bootstrap_without_role(self):
        """Penulisan lanjutan memerlukan peran sesi yang diizinkan."""
        self.service.store_state({"seed": True}, actor_role=None)
        with self.assertRaises(PermissionError):
            self.service.store_state({"seed": False}, actor_role=None)

    def test_repository_obeys_abstraction(self):
        """Repository Django adalah implementasi konkret dari kontrak abstrak repository."""
        repository: BaseStateRepository = DjangoStateRepository()
        repository.save({"hello": "KREASI"}, "abstraction-test")
        self.assertEqual(repository.load("abstraction-test"), {"hello": "KREASI"})

    def test_state_endpoint_requires_login_to_update_existing_state(self):
        """API tidak menerima perubahan data dari sesi yang belum masuk."""
        ApplicationState.objects.create(key="kreasi-default", payload={"a": 1})
        client = Client(enforce_csrf_checks=False)
        response = client.put("/api/state/", data=json.dumps({"data": {"a": 2}}), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_login_endpoint_uses_account_service_factory(self):
        """Endpoint login memakai service yang tepat dan tidak mengirim kata sandi ke UI."""
        ApplicationState.objects.create(key="kreasi-default", payload={
            "users": [{
                "id": "u-admin", "username": "admin", "password": "password123",
                "role": "admin", "name": "Admin Demo", "nip": "1985",
                "jabatan": "Administrator Program Studi", "active": True,
            }]
        })
        client = Client(enforce_csrf_checks=False)
        response = client.post(
            "/api/session/",
            data=json.dumps({"username": "admin", "password": "password123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["profile"]["role"], "admin")
        self.assertNotIn("password", response.json()["profile"])


class HomePageTests(TestCase):
    """Memeriksa halaman dan jalur API pokok tetap tersedia."""

    def test_homepage_loads(self):
        """Halaman utama harus tetap mengirimkan wadah aplikasi HTML asli."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KREASI")
        self.assertContains(response, 'id="app"')

    def test_empty_state_api_returns_null(self):
        """API state mengembalikan null ketika data demo belum disimpan dari browser."""
        response = self.client.get("/api/state/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["data"])
