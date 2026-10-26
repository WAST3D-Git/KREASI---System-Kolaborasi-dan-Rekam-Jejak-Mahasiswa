"""Repositori data KREASI (lapisan ATURAN DATA & HAK AKSES) — inti penerapan ENKAPSULASI.

Gambaran besar
--------------
Browser memegang satu objek JavaScript besar (`db`) berisi semua data fitur. Setiap ada
perubahan, browser mengirim "salinan" objek itu ke server (POST /api/state/). Masalahnya:
browser bisa dimanipulasi (mis. lewat DevTools), sehingga SERVER tidak boleh percaya begitu saja.

File ini adalah "penjaga gerbang" server. Ia melakukan dua hal:
  1. MEMBACA : memberi tiap peran hanya data yang berhak ia lihat  (get_state_for)
  2. MENYIMPAN: memeriksa & membatasi apa yang boleh diubah tiap peran (save_state)

Contoh nyata: mahasiswa mengubah status prestasinya menjadi "Disetujui" lewat DevTools.
save_state() akan MENGEMBALIKAN status itu ke nilai lama di server (__student_achievement_changes).

Fitur yang bergantung pada file ini: seluruh data aplikasi (proyek, prestasi, portofolio,
undangan, notifikasi, pengumuman, data master, SKPI) dan sinkronisasi antar pengguna.
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
    """Bentuk data awal yang kosong (tanpa akun/proyek/prestasi contoh).

    FITUR: dipakai saat sistem baru pertama kali dijalankan (mis. oleh perintah
    create_kreasi_admin) dan sebagai nilai cadangan bila record state belum ada.
    Ini FUNGSI biasa (bukan class); hanya pembentuk struktur kerangka data.
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
    """Pengelola baca/filter/validasi/simpan seluruh data fitur KREASI.

    OOP: ENKAPSULASI (poin utama untuk presentasi)
      * Satu class memegang SEMUA aturan akses data. View (views.py) hanya memanggil
        3 method publik: get_state(), get_state_for(), save_state() (+ get_version()).
      * Detail rumit disembunyikan di method berawalan DUA garis bawah (`__nama`). Python
        mengubah nama method seperti ini secara internal (name-mangling) sehingga tidak
        nyaman dipanggil dari luar class. CATATAN JUJUR: ini penanda "internal", bukan
        kunci keamanan mutlak; keamanan sebenarnya berasal dari pemeriksaan peran di
        dalam method-method ini.
      * Atribut class STATE_KEY dan MAX_STATE_BYTES adalah aturan yang dibungkus di sini.

    Manfaat: bila aturan akses berubah, cukup mengubah satu tempat, bukan menyisir banyak view.
    """
    STATE_KEY = "main"
    MAX_STATE_BYTES = 8 * 1024 * 1024

    def __state_record(self, lock=False):
        """[Internal] Ambil record AppState tunggal ("main") dari database.

        `lock=True` dipakai saat menyimpan: pada database yang mendukung (mis. PostgreSQL)
        baris dikunci agar dua pengguna tidak menimpa satu sama lain. Pada SQLite, penguncian
        dilakukan oleh pengaturan transaction_mode=IMMEDIATE di settings.py.
        """
        queryset = AppState.objects.filter(key=self.STATE_KEY)
        if lock:
            queryset = queryset.select_for_update()
        return queryset.first()

    def get_version(self):
        """Nomor versi data saat ini.

        FITUR: Sinkronisasi antar pengguna/perangkat. Browser memanggil endpoint ringan
        /api/state/version/ tiap 10 detik; bila nomor berbeda dari yang ia pegang, ia memuat ulang data.
        """
        return AppState.objects.filter(key=self.STATE_KEY).values_list("version", flat=True).first() or 0

    def __validate_payload(self, payload):
        """[Internal] Pemeriksaan bentuk data dari browser SEBELUM disimpan.

        Menolak payload yang kehilangan bagian utama atau salah tipe (mis. `projects` bukan daftar),
        tidak bisa diubah ke JSON, atau lebih dari MAX_STATE_BYTES (8 MB). Tujuannya mencegah data
        rusak/terpotong menimpa data sah (contoh: tab lama mengirim data tidak lengkap).
        """
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
        """Salinan LENGKAP data (tanpa filter peran).

        HANYA untuk pemakaian internal server (mis. views.py memeriksa keanggotaan proyek saat
        unggah dokumen). Tidak pernah dikirim mentah ke browser; browser selalu lewat get_state_for().
        """
        record = self.__state_record()
        return deepcopy(record.data) if record else empty_portal_state()

    def get_state_for(self, actor):
        """Data yang BOLEH dilihat oleh pengguna yang sedang login (dibedakan per peran).

        FITUR: dipanggil oleh views.state_view (GET /api/state/) setiap login, muat ulang halaman,
        dan penyegaran otomatis. Menentukan isi Dashboard, Proyek, Prestasi, Talent Pool, dst.

        Aturan per peran:
          * ADMIN    : semua data (kecuali field password).
          * MAHASISWA: hanya prestasi/portofolio/undangan/SKPI/profil MILIKNYA; daftar akun hanya
                       data umum; proyek sesuai aturan keterkaitan (lihat __visible_projects).
          * DOSEN    : proyek yang relevan, talent pool, serta profil mahasiswa tanpa nomor telepon.
        Hasilnya adalah SALINAN (deepcopy) sehingga penyaringan tidak mengubah data asli di database.
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
        """[Internal] Buang field `password` dari daftar akun sebelum dikirim ke browser.
        Sandi sebenarnya hanya ada sebagai hash di tabel PortalUser; ini pengaman lapis kedua.
        """
        for row in state.get("users", []) if isinstance(state.get("users"), list) else []:
            if isinstance(row, dict):
                row.pop("password", None)

    def __visible_projects(self, state, actor, profile):
        """[Internal] Tentukan proyek mana yang terlihat oleh seorang pengguna.

        FITUR: Bursa Proyek (mahasiswa), Manajemen Proyek (dosen).
          * Kategori umum (kompetisi, magang, dsb.)   -> terlihat oleh mahasiswa & dosen.
          * "Proyek Mata Kuliah" & "Informatika untuk Masyarakat" -> hanya terlihat bila pengguna
            terkait (pembuat, anggota, pendaftar, pembimbing) atau sesuai angkatan/kelas/mata kuliah.
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
    def save_state(self, payload: dict, actor, base_version=None):
        """Validasi, batasi sesuai peran, lalu SIMPAN data ke database dalam satu transaksi.

        FITUR: dipanggil oleh views.state_view (POST /api/state/) setiap kali pengguna melakukan
        aksi yang menyimpan data (ajukan prestasi, daftar proyek, validasi, ubah akun, dll.).

        Urutan langkah:
          1. __validate_payload   : cek bentuk data.
          2. kunci record         : agar penyimpan bersamaan antre, tidak saling menimpa.
          3. __apply_role_boundaries : kembalikan bagian yang tidak boleh diubah peran ini.
          4. (Admin saja) sinkronkan tabel PortalUser lewat AccountServiceFactory.sync_records.
          5. buang field password dari data JSON.
          6. simpan; `version` naik HANYA bila isi benar-benar berubah.

        `base_version` = versi data yang dipegang browser saat memuat. Bila berbeda dari server
        (browser Admin memegang data usang), baris buatan pengguna lain dipertahankan
        (__preserve_concurrent_rows) sehingga tidak terhapus tanpa sengaja.
        @transaction.atomic: bila ada kesalahan di tengah jalan, semua perubahan dibatalkan.
        """
        self.__validate_payload(payload)
        record = self.__state_record(lock=True)  # kunci baris: penyimpan lain menunggu giliran
        previous = deepcopy(record.data) if record else empty_portal_state()  # "data lama" server
        incoming = deepcopy(payload)
        incoming = self.__apply_role_boundaries(previous, incoming, actor)  # langkah inti keamanan
        # Snapshot Admin yang usang (pengguna lain menyimpan sejak Admin memuat data) tidak
        # boleh menghapus baris yang dibuat mahasiswa/dosen pada selang waktu tersebut.
        if (actor.role == "admin" and record is not None and base_version is not None
                and int(base_version) != record.version):
            incoming = self.__preserve_concurrent_rows(previous, incoming, actor)

        # Sinkronkan kredensial akun hanya ketika administrator mengirim daftar akun.
        # Data yang disimpan di JSON tidak pernah berisi kata sandi mentah.
        # (Hanya Admin yang berhak mengubah akun; peran lain sudah dikunci di langkah sebelumnya.)
        if actor.role == "admin" and isinstance(payload.get("users"), list):
            AccountServiceFactory.sync_records(payload["users"])

        incoming.setdefault("users", previous.get("users", []))
        incoming.setdefault("masterData", previous.get("masterData", empty_portal_state()["masterData"]))
        for field in ("users",):
            for user_row in incoming.get(field, []):
                if isinstance(user_row, dict):
                    user_row.pop("password", None)
        if record is None:
            record = AppState(key=self.STATE_KEY, data=incoming, version=1)
            record.save()
        elif record.data != incoming:
            # Versi hanya naik bila isi benar-benar berubah; simpan ulang yang identik
            # tidak memicu penyegaran di klien lain.
            record.data = incoming
            record.version += 1
            record.save()
        return deepcopy(record.data), record.version

    def __preserve_concurrent_rows(self, old, new, actor):
        """[Internal] Gabungkan snapshot Admin yang USANG dengan data terbaru server.

        Skenario: Admin membuka halaman, lalu mahasiswa mengajukan prestasi baru. Bila Admin menyimpan
        sesuatu dengan data lamanya, prestasi baru itu bisa hilang. Method ini mempertahankan baris
        yang ada di server tetapi tidak ada di snapshot Admin (prestasi, portofolio, undangan, talent
        pool), menggabungkan notifikasi per pembaca, dan memakai profil mahasiswa versi server.
        """
        for key, id_field in (("achievements", "id"), ("portfolios", "id"), ("invitations", "id"),
                              ("talentPool", "nim")):
            incoming = [row for row in new.get(key, []) if isinstance(row, dict)]
            seen = {str(row.get(id_field, "")) for row in incoming}
            extra = [deepcopy(row) for row in old.get(key, [])
                     if isinstance(row, dict) and str(row.get(id_field, "")) not in seen]
            new[key] = incoming + extra
        new["notifications"] = self.__merge_notifications(old.get("notifications", []), new.get("notifications", []), actor)
        old_profiles = old.get("studentProfiles", {}) if isinstance(old.get("studentProfiles"), dict) else {}
        new_profiles = new.get("studentProfiles", {}) if isinstance(new.get("studentProfiles"), dict) else {}
        new["studentProfiles"] = {**deepcopy(new_profiles), **deepcopy(old_profiles)}
        return new

    def __apply_role_boundaries(self, old: dict, new: dict, actor):
        """[Internal] PUSAT aturan "siapa boleh mengubah apa" (otorisasi sisi server).

        Prinsipnya: data dari browser dianggap USULAN. Untuk bagian yang bukan hak peran tsb,
        usulan diganti dengan data lama server. Pemeriksaan di JavaScript (menu disembunyikan,
        tombol dinonaktifkan) hanya kenyamanan UI; yang menentukan adalah method ini.

          * ADMIN    : mengelola akun, data master, pengumuman, validasi prestasi, SKPI.
          * DOSEN    : hanya proyek yang ia miliki/bimbing + undangan & notifikasinya sendiri.
          * MAHASISWA: hanya data miliknya; tidak bisa menyetujui diri sendiri (status proyek,
                       validasi prestasi, verifikasi dokumentasi dipulihkan ke nilai server).
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
        """[Internal] Rapikan referensi proyek ketika Admin mengubah/menghapus akun.

        FITUR: Manajemen Akun. Bila NIM/NIP/nama berubah, referensi di proyek ikut diperbarui; bila
        akun mahasiswa dihapus, keanggotaannya dilepas dan proyek yang ia buat dibersihkan. Isi proyek
        lain (judul, nilai, dokumen) tidak diubah oleh Admin dari sini.
        """
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
        """[Internal] Gabungkan undangan kolaborasi (dosen mengundang mahasiswa dari Talent Pool).

        Pengguna hanya bisa menambah/mengubah/menghapus undangan MILIKNYA (mahasiswa: yang ditujukan
        kepadanya; dosen: yang ia kirim). Undangan pihak lain dipertahankan apa adanya.
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
        """[Internal] Gabungkan notifikasi: isi lama tak bisa diubah klien, hanya status "sudah dibaca"
        milik akun sendiri (kunci `readBy`) yang boleh berubah. Notifikasi baru boleh ditambahkan.
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
        """[Internal] Ganti hanya baris milik satu identitas (mis. NIM) dan biarkan baris orang lain.
        Dipakai untuk portofolio dan talent pool milik mahasiswa.
        """
        retained = [deepcopy(row) for row in old_rows if str(row.get(owner_key, "")) != owner_value]
        changed = [deepcopy(row) for row in new_rows if str(row.get(owner_key, "")) == owner_value]
        return retained + changed

    def __merge_profile_map(self, old_map, new_map, owner_value):
        """[Internal] Perbarui profil satu mahasiswa (bio, keahlian, telepon) tanpa menyentuh profil mahasiswa lain."""
        result = deepcopy(old_map if isinstance(old_map, dict) else {})
        if isinstance(new_map, dict) and owner_value in new_map:
            result[owner_value] = deepcopy(new_map[owner_value])
        return result

    def __student_achievement_changes(self, old_rows, new_rows, nim):
        """[Internal] Aturan prestasi mahasiswa.

        FITUR: Rekam Jejak Prestasi. Mahasiswa boleh MENGAJUKAN prestasi (status awal otomatis
        "Menunggu Validasi") dan mengedit data pengajuan, tetapi `status`, `validatedBy`, dan
        `validatedAt` selalu dipulihkan dari server: hanya Admin yang menentukan hasil validasi.
        """
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
        """[Internal] Aturan perubahan proyek oleh mahasiswa.

        FITUR: Bursa Proyek, Usulkan Proyek, Proyek Saya.
          * Proyek baru buatan mahasiswa selalu berstatus "Diajukan" (menunggu tinjauan dosen).
          * Pada proyek orang lain, data inti (judul, kategori, kuota, dsb.) dikunci; mahasiswa
            hanya boleh ikut serta/mendaftar.
          * Status proyek & kepemilikan dosen tidak bisa diubah mahasiswa.
          * Proyek yang tidak ikut terkirim tidak dihapus oleh sesi mahasiswa.
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
        """[Internal] Cegah mahasiswa menyetujui dokumentasinya sendiri.

        FITUR: Dokumentasi tahapan proyek (milestone). Status "Disetujui", `verifiedBy`, `verifiedAt`,
        dan `reviewNote` dipulihkan dari server; verifikasi hanya hak dosen.
        """
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
        """[Internal] Aturan perubahan proyek oleh dosen.

        FITUR: Manajemen Proyek (dosen). Bila proyek sudah punya pemilik (`ownerNip`), hanya pemilik
        itu yang boleh mengubah/menghapus. Bila belum, boleh oleh pembimbing/pembuat, atau
        dosen yang meninjau usulan berstatus "Diajukan" pada kategori selain Proyek Mata Kuliah /
        Informatika untuk Masyarakat. Proyek orang lain dikembalikan ke nilai lama.
        """
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
