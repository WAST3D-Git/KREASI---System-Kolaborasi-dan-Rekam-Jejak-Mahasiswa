"""Repositori data portal KREASI.

Frontend lama mengirim satu snapshot state JavaScript. Untuk mempertahankan renderer,
state domain UI tetap disimpan sebagai agregat JSON pada `AppState`, sedangkan kredensial
akun dan metadata berkas disimpan melalui model relasional Django.

DESAIN ENKAPSULASI: view memakai antarmuka publik `get_state()`, `get_state_for()`, dan
`save_state()`. Detail pemilihan record, validasi struktur, pemfilteran akses, dan penggabungan
perubahan disimpan di metode `__...`. Nama ganda memicu name-mangling Python, tetapi bukan
mekanisme keamanan; kontrol akses sebenarnya dilakukan oleh logika validasi metode ini.
"""
from copy import deepcopy
import json

from django.db import transaction

from .models import AppState
from .services import AccountServiceFactory

DEFAULT_CATEGORIES = [
    "Informatika untuk Masyarakat", "Proyek Mata Kuliah", "Kompetisi", "Magang",
    "Wirausaha", "Organisasi & Kepemimpinan", "Minat & Bakat",
    "Internasionalisasi & Summit", "Rekognisi", "Penelitian & Hibah",
]
DEFAULT_COURSES = [
    "Rekayasa Perangkat Lunak", "Jaringan Komputer", "Basis Data",
    "Kecerdasan Buatan", "Jaringan & Keamanan Siber", "Sistem Informasi",
    "Kerja Praktik / Magang", "Skripsi / Tugas Akhir", "KKN / Informatika untuk Masyarakat",
]


def empty_portal_state():
    """Buat bentuk state awal dengan struktur yang diharapkan frontend.

    Ini fungsi pembentuk data, bukan class/model OOP. Daftar domain dimulai kosong agar
    tidak ada akun/proyek/prestasi contoh; nilai master dipertahankan untuk konfigurasi awal.
    """
    return {
        "users": [], "announcements": [], "talentPool": [], "projects": [],
        "achievements": [], "portfolios": [], "invitations": [], "notifications": [],
        "skpiFinalizations": [], "studentProfiles": {},
        "studentProfile": {"phone": "", "bio": "", "skills": []},
        "masterData": {
            "projectCategories": deepcopy(DEFAULT_CATEGORIES), "courses": deepcopy(DEFAULT_COURSES),
            "classes": ["A", "B", "C"], "courseOfferings": [],
            "achievementCategories": [], "mexsThreshold": 1000,
        },
    }


class KreasiStateRepository:
    """Mengelola baca, filter, validasi, dan simpan state KREASI.

    `STATE_KEY` mengidentifikasi record agregat tunggal, sedangkan `MAX_STATE_BYTES`
    membatasi besar payload. Kelas ini menjadi batas data backend agar view tidak mengubah
    `AppState` secara langsung dan agar pembatasan peran diterapkan sebelum penyimpanan.
    """
    STATE_KEY = "main"
    MAX_STATE_BYTES = 8 * 1024 * 1024

    def __state_record(self):
        """Metode privat (`__...`) mengenkapsulasi pemilihan record singleton."""
        record = AppState.objects.filter(key=self.STATE_KEY).first()
        return record

    def __validate_payload(self, payload):
        """Validasi internal sebelum JSON disimpan ke basis data."""
        if not isinstance(payload, dict):
            raise ValueError("Format data sistem tidak valid.")
        # Frontend mengirim snapshot lengkap. Menolak array/objek utama yang hilang atau
        # bertipe salah mencegah payload parsial menghapus data tanpa sengaja.
        expected = {
            "users": list, "announcements": list, "talentPool": list, "projects": list,
            "achievements": list, "portfolios": list, "invitations": list, "notifications": list,
            "skpiFinalizations": list, "studentProfiles": dict, "studentProfile": dict, "masterData": dict,
        }
        for field, expected_type in expected.items():
            if field not in payload or not isinstance(payload[field], expected_type):
                raise ValueError(f"Struktur data '{field}' tidak valid atau tidak lengkap.")
        try:
            encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ValueError("Data sistem tidak dapat diserialisasi.") from exc
        if len(encoded) > self.MAX_STATE_BYTES:
            raise ValueError("Data sistem terlalu besar untuk disimpan sekaligus.")

    def get_state(self):
        """Antarmuka baca internal-server untuk memperoleh salinan snapshot penuh."""
        record = self.__state_record()
        return deepcopy(record.data) if record else empty_portal_state()

    def get_state_for(self, actor):
        """Kembalikan subset state yang boleh dilihat pengguna yang sedang login.

        Admin mendapat state yang sudah dibersihkan dari field password; mahasiswa dan
        dosen memperoleh kumpulan user, proyek, notifikasi, dan profil sesuai role/identitas.
        Hasilnya adalah salinan data, sehingga filter tidak mengubah snapshot asli di DB.
        """
        state = self.get_state()
        if actor.role == "admin":
            self.__remove_password_fields(state)
            return state

        role = actor.role
        identity = str(actor.identifier or "")
        profile = actor.profile_data if isinstance(actor.profile_data, dict) else {}
        identity_fields = {
            "id", "username", "role", "name", "nim", "nip", "prodi", "angkatan", "kelas",
            "active", "avatar", "mataKuliahDiambil", "mataKuliahDiampu", "semester", "poin",
            "prestasi", "jabatan", "skills", "mexs", "portfolioCount", "achievementCount",
        }
        state["users"] = [
            {key: deepcopy(value) for key, value in row.items() if key in identity_fields}
            for row in state.get("users", [])
            if isinstance(row, dict) and row.get("role") in {"student", "lecturer"}
            and row.get("active", True)
        ]
        state["projects"] = self.__visible_projects(state, actor, profile)
        state["notifications"] = [
            item for item in state.get("notifications", [])
            if isinstance(item, dict)
            and (not item.get("recipientRole") or item.get("recipientRole") == role)
            and (not item.get("recipientNim") or str(item.get("recipientNim")) == identity)
            and (not item.get("recipientNip") or str(item.get("recipientNip")) == identity)
        ]

        if role == "student":
            state["achievements"] = [row for row in state.get("achievements", [])
                                     if str(row.get("nim", "")) == identity]
            state["portfolios"] = [row for row in state.get("portfolios", [])
                                   if str(row.get("nim", "")) == identity]
            state["talentPool"] = [row for row in state.get("talentPool", [])
                                   if str(row.get("nim", "")) == identity]
            profiles = state.get("studentProfiles", {})
            own_profile = profiles.get(identity, {}) if isinstance(profiles, dict) else {}
            state["studentProfiles"] = {identity: deepcopy(own_profile)} if own_profile else {}
            state["studentProfile"] = deepcopy(own_profile) if isinstance(own_profile, dict) else {}
            state["invitations"] = [row for row in state.get("invitations", [])
                                    if str(row.get("nim", "")) == identity]
            state["skpiFinalizations"] = [row for row in state.get("skpiFinalizations", [])
                                          if str(row.get("nim", "")) == identity]
        elif role == "lecturer":
            # Talent pool, portofolio dan profil publik diperlukan pada katalog talenta.
            # Nomor telepon mahasiswa lain tidak ikut diekspos ke akun dosen.
            profiles = state.get("studentProfiles", {})
            state["studentProfiles"] = {
                str(nim): {key: deepcopy(value) for key, value in row.items() if key in {"bio", "skills"}}
                for nim, row in profiles.items() if isinstance(row, dict)
            } if isinstance(profiles, dict) else {}
            state["studentProfile"] = {}
            state["skpiFinalizations"] = []
            state["invitations"] = [row for row in state.get("invitations", [])
                                    if str(row.get("sender", "")) == str(actor.full_name or "")
                                    or str(row.get("senderNip", row.get("lecturerNip", ""))) == identity]
        self.__remove_password_fields(state)
        return state

    def __remove_password_fields(self, state):
        """Helper privat yang membuang password legacy dari data profil browser.

        Kredensial autentikasi tetap disimpan/hash oleh `PortalUser`; field password pada
        snapshot UI lama tidak boleh dikirim kembali dalam respons JSON.
        """
        for row in state.get("users", []) if isinstance(state.get("users"), list) else []:
            if isinstance(row, dict):
                row.pop("password", None)

    def __visible_projects(self, state, actor, profile):
        """Helper privat untuk menerapkan aturan visibilitas proyek menurut role.

        Proyek umum tersedia sesuai kategori master; kategori Proyek Mata Kuliah dan
        Informatika untuk Masyarakat memiliki aturan keterkaitan dengan akun/proyek/kelas.
        """
        role = actor.role
        identity = str(actor.identifier or "")
        master = state.get("masterData", {}) if isinstance(state.get("masterData"), dict) else {}
        configured = set(master.get("projectCategories", DEFAULT_CATEGORIES))
        private_categories = {"Proyek Mata Kuliah", "Informatika untuk Masyarakat"}
        public_categories = configured - private_categories
        courses = profile.get("mataKuliahDiambil")
        projects = state.get("projects", [])
        visible = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            category = project.get("category")
            if role == "lecturer":
                if (category in public_categories
                        or str(project.get("supervisorNip", "")) == identity
                        or str(project.get("creatorNip", "")) == identity
                        or str(project.get("ownerNip", "")) == identity):
                    visible.append(project)
                continue

            related = str(project.get("creatorNim", "")) == identity
            for member in project.get("members", []) if isinstance(project.get("members"), list) else []:
                related = related or (isinstance(member, dict) and str(member.get("nim", "")) == identity)
            for applicant in project.get("applicants", []) if isinstance(project.get("applicants"), list) else []:
                related = related or (isinstance(applicant, dict) and str(applicant.get("nim", "")) == identity)
            groups = project.get("groups", []) if isinstance(project.get("groups"), list) else []
            for group in groups:
                for member in group.get("members", []) if isinstance(group.get("members"), list) else []:
                    related = related or (isinstance(member, dict) and str(member.get("nim", "")) == identity)

            if related or category in public_categories:
                visible.append(project)
                continue
            if category == "Proyek Mata Kuliah" and project.get("status") == "Active" and not project.get("studentCreated"):
                cohort = str(profile.get("angkatan") or "")
                klass = str(profile.get("kelas") or "")
                project_cohort = str(project.get("angkatan") or "")
                project_classes = project.get("kelas", [])
                class_ok = not project_classes or (isinstance(project_classes, list) and klass in project_classes)
                course_ok = courses is None or not isinstance(courses, list) or project.get("course") in courses
                if (not project_cohort or project_cohort == cohort) and class_ok and course_ok:
                    visible.append(project)
        return visible

    @transaction.atomic
    def save_state(self, payload: dict, actor):
        """Validasi, terapkan batas role, lalu simpan snapshot dalam satu transaksi.

        Proses utamanya: validasi bentuk data -> salin data -> terapkan kebijakan role ->
        bila Admin mengubah daftar akun, sinkronkan tabel PortalUser -> hapus password dari
        snapshot -> simpan/increment versi AppState. Atomic mencegah simpan setengah jalan.
        """
        self.__validate_payload(payload)
        previous = self.get_state()
        incoming = deepcopy(payload)
        incoming = self.__apply_role_boundaries(previous, incoming, actor)

        # Sinkronkan kredensial akun hanya ketika administrator mengirim daftar akun.
        # Data yang disimpan di JSON tidak pernah berisi kata sandi mentah.
        if actor.role == "admin" and isinstance(payload.get("users"), list):
            AccountServiceFactory.sync_records(payload["users"])

        incoming.setdefault("users", previous.get("users", []))
        incoming.setdefault("masterData", previous.get("masterData", empty_portal_state()["masterData"]))
        for field in ("users",):
            for user_row in incoming.get(field, []):
                if isinstance(user_row, dict):
                    user_row.pop("password", None)
        record = self.__state_record()
        if record is None:
            record = AppState(key=self.STATE_KEY, data=incoming, version=1)
        else:
            record.data = incoming
            record.version += 1
        record.save()
        return deepcopy(record.data), record.version

    def __apply_role_boundaries(self, old: dict, new: dict, actor):
        """Pusat pembatasan perubahan state sisi server.

        Metode privat ini mencegah otorisasi hanya bergantung pada tombol/menu UI:
        Admin mengelola akun/master; dosen mengelola proyek terkait; mahasiswa hanya
        mengubah data miliknya dan tidak dapat memberi persetujuan sendiri.
        """
        new.setdefault("users", old.get("users", []))
        if actor.role != "admin":
            # Akun, data master, pengumuman, dan finalisasi SKPI hanya dikelola Admin.
            for key in ("users", "masterData", "announcements", "skpiFinalizations"):
                new[key] = deepcopy(old.get(key, empty_portal_state().get(key, [])))

        if actor.role == "admin":
            # Admin tidak mengedit isi proyek dari halaman monitor. Namun, perubahan
            # identitas akun dan penghapusan akun harus diselaraskan dengan referensi proyek.
            new["projects"] = self.__admin_project_changes(
                old.get("projects", []), new.get("projects", []),
                old.get("users", []), new.get("users", []),
            )
            # Operasi Manajemen Akun memperbarui NIM/profil talenta dan menghapus baris
            # milik akun yang dihapus. Data SKPI/prestasi dan master data dikelola Admin.
            new["studentProfile"] = deepcopy(old.get("studentProfile", {}))
            return new

        if actor.role == "lecturer":
            # Dosen dapat mengelola proyek yang menjadi ruang kerjanya; profil/prestasi
            # mahasiswa, portofolio, dan finalisasi SKPI tidak diubah dari sesi dosen.
            for key in ("achievements", "portfolios", "studentProfiles", "studentProfile", "talentPool", "skpiFinalizations"):
                new[key] = deepcopy(old.get(key, empty_portal_state().get(key, [])))
            new["announcements"] = deepcopy(old.get("announcements", []))
            new["users"] = deepcopy(old.get("users", []))
            new["masterData"] = deepcopy(old.get("masterData", empty_portal_state()["masterData"]))
            new["projects"] = self.__lecturer_project_changes(old.get("projects", []), new.get("projects", []), actor.identifier)
            new["invitations"] = self.__merge_invitations(old.get("invitations", []), new.get("invitations", []), actor)
            new["notifications"] = self.__merge_notifications(old.get("notifications", []), new.get("notifications", []), actor)
            return new

        if actor.role == "student":
            nim = str(actor.identifier or "")
            new["projects"] = self.__student_project_changes(old.get("projects", []), new.get("projects", []), nim)
            new["portfolios"] = self.__merge_owned_rows(old.get("portfolios", []), new.get("portfolios", []), "nim", nim)
            new["talentPool"] = self.__merge_owned_rows(old.get("talentPool", []), new.get("talentPool", []), "nim", nim)
            new["achievements"] = self.__student_achievement_changes(old.get("achievements", []), new.get("achievements", []), nim)
            new["studentProfiles"] = self.__merge_profile_map(old.get("studentProfiles", {}), new.get("studentProfiles", {}), nim)
            new["invitations"] = self.__merge_invitations(old.get("invitations", []), new.get("invitations", []), actor)
            new["notifications"] = self.__merge_notifications(old.get("notifications", []), new.get("notifications", []), actor)
            old_profiles = old.get("studentProfiles", {})
            new_profiles = new.get("studentProfiles", {})
            new["studentProfile"] = deepcopy(new_profiles.get(nim, old_profiles.get(nim, new.get("studentProfile", {}))) or {})
            # Pengumuman, pengguna, master data, dan finalisasi dilindungi pada blok di atas.
            return new

        return old

    def __admin_project_changes(self, old_projects, new_projects, old_users, new_users):
        """Sesuaikan referensi identitas anggota saat Admin mengubah akun; jaga isi proyek."""
        old_user_by_id = {str(row.get("id", "")): row for row in old_users if isinstance(row, dict)}
        new_user_by_id = {str(row.get("id", "")): row for row in new_users if isinstance(row, dict)}
        removed = [row for uid, row in old_user_by_id.items() if uid not in new_user_by_id]
        removed_nims = {str(row.get("nim") or row.get("username") or "") for row in removed if row.get("role") == "student"}
        removed_nips = {str(row.get("nip") or row.get("username") or "") for row in removed if row.get("role") == "lecturer"}
        removed_names = {str(row.get("name") or "") for row in removed if row.get("role") == "lecturer"}

        student_updates, lecturer_updates = [], []
        for uid, old_user in old_user_by_id.items():
            current = new_user_by_id.get(uid)
            if not current or current.get("role") != old_user.get("role"):
                continue
            if old_user.get("role") == "student":
                student_updates.append((str(old_user.get("nim") or old_user.get("username") or ""), current))
            elif old_user.get("role") == "lecturer":
                lecturer_updates.append((str(old_user.get("nip") or old_user.get("username") or ""), old_user, current))

        incoming_ids = {str(row.get("id", "")) for row in new_projects if isinstance(row, dict)}
        incoming_ids.discard("")
        output = []
        for original in old_projects:
            if not isinstance(original, dict):
                continue
            project = deepcopy(original)
            pid = str(project.get("id", ""))
            if pid not in incoming_ids:
                deleted_student_project = str(project.get("creatorNim", "")) in removed_nims
                deleted_lecturer_project = (
                    str(project.get("creatorNip", "")) in removed_nips
                    or str(project.get("ownerNip", "")) in removed_nips
                    or str(project.get("supervisorNip", "")) in removed_nips
                    or (not project.get("supervisorNip") and str(project.get("supervisor", "")) in removed_names)
                    or (not project.get("creatorNip") and str(project.get("creator", "")) in removed_names and "dosen" in str(project.get("creatorRole", "")).lower())
                )
                if deleted_student_project or deleted_lecturer_project:
                    continue

            # Perubahan identitas hanya memperbarui referensi; judul, status, nilai, dan dokumen tetap dikelola server.
            creator_nim = str(project.get("creatorNim", ""))
            for old_nim, current in student_updates:
                new_nim = str(current.get("nim") or current.get("username") or "")
                if creator_nim and creator_nim == old_nim:
                    project["creatorNim"] = new_nim
                    project["creator"] = current.get("name", project.get("creator", ""))
                    project["department"] = current.get("prodi", project.get("department", ""))
                for collection_key in ("members", "applicants"):
                    rows = project.get(collection_key, []) if isinstance(project.get(collection_key), list) else []
                    for member in rows:
                        if isinstance(member, dict) and str(member.get("nim", "")) == old_nim:
                            member["nim"] = new_nim
                            member["name"] = current.get("name", member.get("name", ""))
                            member["prodi"] = current.get("prodi", member.get("prodi", ""))
                groups = project.get("groups", []) if isinstance(project.get("groups"), list) else []
                for group in groups:
                    members = group.get("members", []) if isinstance(group, dict) and isinstance(group.get("members"), list) else []
                    for member in members:
                        if isinstance(member, dict) and str(member.get("nim", "")) == old_nim:
                            member["nim"] = new_nim
                            member["name"] = current.get("name", member.get("name", ""))
                            member["prodi"] = current.get("prodi", member.get("prodi", ""))

            # Menghapus akun mahasiswa hanya menghapus keanggotaan/pengajuannya, bukan anggota lain.
            project["members"] = [m for m in project.get("members", []) if not isinstance(m, dict) or str(m.get("nim", "")) not in removed_nims]
            project["applicants"] = [m for m in project.get("applicants", []) if not isinstance(m, dict) or str(m.get("nim", "")) not in removed_nims]
            for group in project.get("groups", []) if isinstance(project.get("groups"), list) else []:
                if isinstance(group, dict) and isinstance(group.get("members"), list):
                    group["members"] = [m for m in group["members"] if not isinstance(m, dict) or str(m.get("nim", "")) not in removed_nims]

            for old_nip, old_user, current in lecturer_updates:
                new_nip = str(current.get("nip") or current.get("username") or "")
                for field in ("supervisorNip", "creatorNip", "ownerNip"):
                    if str(project.get(field, "")) == old_nip:
                        project[field] = new_nip
                old_name = str(old_user.get("name", ""))
                new_name = str(current.get("name", old_name))
                if str(project.get("supervisor", "")) == old_name:
                    project["supervisor"] = new_name
                if str(project.get("creator", "")) == old_name and "dosen" in str(project.get("creatorRole", "")).lower():
                    project["creator"] = new_name
            output.append(project)
        return output

    def __merge_invitations(self, old_rows, new_rows, actor):
        """Gabungkan undangan yang dikirim/diterima oleh akun aktif saja.

        Data undangan milik pengguna lain dipertahankan agar satu role tidak dapat
        menghapus atau mengganti undangan dari tampilan state yang telah difilter.
        """
        identity = str(actor.identifier or "")
        name = str(actor.full_name or "")

        def owned(row):
            if actor.role == "student":
                return str(row.get("nim", "")) == identity
            if actor.role == "lecturer":
                return (str(row.get("senderNip", row.get("lecturerNip", ""))) == identity
                        or (bool(name) and str(row.get("sender", "")) == name))
            return False

        old_rows = [deepcopy(row) for row in old_rows if isinstance(row, dict)]
        new_rows = [deepcopy(row) for row in new_rows if isinstance(row, dict)]
        incoming_by_id = {str(row.get("id", "")): row for row in new_rows}
        old_ids = {str(row.get("id", "")) for row in old_rows}
        output = []
        for old in old_rows:
            rid = str(old.get("id", ""))
            incoming = incoming_by_id.get(rid)
            if owned(old) and incoming and owned(incoming):
                output.append(incoming)
            elif owned(old) and incoming is None:
                # Hilangnya undangan dari tampilan terfilter milik pemanggil berarti undangan itu ditangani/dihapus.
                continue
            else:
                output.append(old)
        for row in new_rows:
            rid = str(row.get("id", ""))
            if rid not in old_ids and owned(row):
                output.append(row)
        return output

    def __merge_notifications(self, old_rows, new_rows, actor):
        """Pertahankan isi notifikasi; izinkan perubahan status baca untuk akun sendiri.

        Kunci `readBy` dibedakan menurut role dan identitas agar status baca pengguna lain
        tidak tertimpa oleh snapshot yang dikirim dari browser.
        """
        identity = str(actor.identifier or "")
        if actor.role == "admin":
            account_key = f"admin:{identity or 'admin'}"
        elif actor.role == "lecturer":
            account_key = f"lecturer:{identity}"
        else:
            account_key = f"student:{identity}"
        old_rows = [deepcopy(row) for row in old_rows if isinstance(row, dict)]
        new_rows = [deepcopy(row) for row in new_rows if isinstance(row, dict)]
        incoming_by_id = {str(row.get("id", "")): row for row in new_rows}
        old_ids = {str(row.get("id", "")) for row in old_rows}
        output = []
        for old in old_rows:
            incoming = incoming_by_id.get(str(old.get("id", "")))
            if incoming is not None:
                original_read = old.get("readBy") if isinstance(old.get("readBy"), dict) else {}
                incoming_read = incoming.get("readBy") if isinstance(incoming.get("readBy"), dict) else {}
                if account_key in incoming_read:
                    original_read[account_key] = bool(incoming_read[account_key])
                old["readBy"] = original_read
            # Notifikasi yang tidak muncul pada respons terfilter tetap dipertahankan bagi pemiliknya.
            output.append(old)
        # Notifikasi baru dapat ditambahkan; isi notifikasi lama tidak dapat diubah klien.
        for row in new_rows:
            if str(row.get("id", "")) not in old_ids:
                output.append(row)
        return output

    def __merge_owned_rows(self, old_rows, new_rows, owner_key, owner_value):
        """Ganti hanya baris milik identitas tertentu dan pertahankan baris lain."""
        retained = [deepcopy(row) for row in old_rows if str(row.get(owner_key, "")) != owner_value]
        changed = [deepcopy(row) for row in new_rows if str(row.get(owner_key, "")) == owner_value]
        return retained + changed

    def __merge_profile_map(self, old_map, new_map, owner_value):
        """Perbarui satu profil mahasiswa tanpa menimpa profil mahasiswa lain."""
        result = deepcopy(old_map if isinstance(old_map, dict) else {})
        if isinstance(new_map, dict) and owner_value in new_map:
            result[owner_value] = deepcopy(new_map[owner_value])
        return result

    def __student_achievement_changes(self, old_rows, new_rows, nim):
        """Izinkan pengajuan prestasi mahasiswa, tetapi pertahankan hasil validasi Admin."""
        old_by_id = {str(row.get("id")): row for row in old_rows if str(row.get("nim", "")) == nim}
        retained = [deepcopy(row) for row in old_rows if str(row.get("nim", "")) != nim]
        changed = []
        for row in new_rows:
            if str(row.get("nim", "")) != nim:
                continue
            row = deepcopy(row)
            old_row = old_by_id.get(str(row.get("id")))
            if old_row:
                # Mahasiswa boleh memperbarui metadata pengajuan, tetapi tidak dapat
                # mengubah hasil validasi yang hanya boleh ditetapkan Admin.
                for key in ("status", "validatedBy", "validatedAt"):
                    row[key] = old_row.get(key, "Menunggu Validasi" if key == "status" else "-")
            else:
                row["status"] = "Menunggu Validasi"
                row["validatedBy"] = "-"
                row["validatedAt"] = "-"
            changed.append(row)
        return retained + changed

    def __student_project_changes(self, old_projects, new_projects, nim):
        """Batasi mahasiswa pada proyek terkait dan jangan izinkan persetujuan mandiri.

        Perubahan kandidat dibandingkan dengan snapshot tersimpan; status proyek, pemilik,
        dan status verifikasi dokumentasi yang ditetapkan pihak berwenang tetap dikunci.
        """
        old_by_id = {str(item.get("id")): item for item in old_projects}
        output = []
        seen = set()
        for candidate in new_projects:
            if not isinstance(candidate, dict):
                continue
            pid = str(candidate.get("id", ""))
            old = old_by_id.get(pid)
            seen.add(pid)
            if old is None:
                if str(candidate.get("creatorNim", "")) == nim:
                    candidate = deepcopy(candidate)
                    candidate["status"] = "Diajukan"
                    candidate["studentCreated"] = True
                    output.append(candidate)
                continue
            related = (str(old.get("creatorNim", "")) == nim
                       or any(str(item.get("nim", "")) == nim for item in old.get("members", []))
                       or any(str(item.get("nim", "")) == nim for item in old.get("applicants", [])))
            if old.get("isGroup"):
                related = related or any(
                    any(str(member.get("nim", "")) == nim for member in group.get("members", []))
                    for group in old.get("groups", [])
                )
            if not related:
                output.append(deepcopy(old))
                continue
            item = deepcopy(candidate)
            # Status persetujuan tidak boleh ditentukan oleh sesi mahasiswa.
            item["status"] = old.get("status", "Diajukan")
            item["ownerNip"] = old.get("ownerNip", "")
            item["ownerName"] = old.get("ownerName", "")
            item["ownedAt"] = old.get("ownedAt", "")
            if str(old.get("creatorNim", "")) != nim:
                # Untuk proyek milik pihak lain, metadata identitas/kuota inti tidak bisa diubah.
                for key in ("title", "category", "course", "creator", "creatorNim", "creatorNip", "supervisor",
                            "supervisorNip", "department", "mitra", "lokasi", "period", "description", "requirements",
                            "membersNeeded", "isGroup", "groupCount", "membersPerGroup", "angkatan", "kelas", "studentCreated"):
                    item[key] = deepcopy(old.get(key))
            self.__keep_student_milestone_status(old, item)
            output.append(item)
        # Record lama yang hilang dari payload tidak dihapus oleh sesi mahasiswa.
        for old in old_projects:
            if str(old.get("id", "")) not in seen:
                output.append(deepcopy(old))
        return output

    def __keep_student_milestone_status(self, old_project, new_project):
        """Pulihkan status verifikasi dari server agar mahasiswa tidak menyetujui dokumen sendiri."""
        def keep(old_rows, new_rows):
            old_by_key = {str(row.get("key", row.get("id", ""))): row for row in old_rows if isinstance(row, dict)}
            for row in new_rows:
                if not isinstance(row, dict):
                    continue
                prior = old_by_key.get(str(row.get("key", row.get("id", ""))))
                if not prior:
                    if row.get("status") == "Disetujui":
                        row["status"] = "Menunggu Verifikasi"
                    continue
                if row.get("status") == "Disetujui":
                    row["status"] = prior.get("status", "Belum Dimulai")
                for key in ("verifiedBy", "verifiedAt", "reviewNote"):
                    row[key] = prior.get(key, "")
        keep(old_project.get("milestones", []) if isinstance(old_project.get("milestones"), list) else [],
             new_project.get("milestones", []) if isinstance(new_project.get("milestones"), list) else [])
        old_groups = {str(group.get("id")): group for group in old_project.get("groups", [])}
        for group in new_project.get("groups", []):
            old_group = old_groups.get(str(group.get("id")))
            if not old_group:
                continue
            keep(old_group.get("milestones", []) if isinstance(old_group.get("milestones"), list) else [],
                 group.get("milestones", []) if isinstance(group.get("milestones"), list) else [])

    def __lecturer_project_changes(self, old_projects, new_projects, nip):
        """Terima perubahan hanya pada proyek yang dapat dikelola dosen yang aktif."""
        old_by_id = {str(item.get("id")): item for item in old_projects}
        output, seen = [], set()
        for candidate in new_projects:
            if not isinstance(candidate, dict):
                continue
            pid = str(candidate.get("id", ""))
            old = old_by_id.get(pid)
            seen.add(pid)
            if old is None:
                if str(candidate.get("creatorNip", "")) == nip:
                    output.append(deepcopy(candidate))
                continue
            owner_nip = str(old.get("ownerNip", ""))
            # Bila pemilik sudah ditetapkan, hanya pemilik yang boleh mengubah/menghapus proyek.
            if owner_nip:
                permitted = owner_nip == nip
            else:
                permitted = (str(old.get("supervisorNip", "")) == nip
                             or str(old.get("creatorNip", "")) == nip
                             or (old.get("status") == "Diajukan"
                                 and old.get("category") not in {"Proyek Mata Kuliah", "Informatika untuk Masyarakat"}))
            output.append(deepcopy(candidate if permitted else old))
        for old in old_projects:
            if str(old.get("id", "")) not in seen:
                owner_nip = str(old.get("ownerNip", ""))
                owned = owner_nip == nip if owner_nip else nip in {
                    str(old.get("creatorNip", "")), str(old.get("supervisorNip", ""))
                }
                if not owned:
                    output.append(deepcopy(old))
        return output
