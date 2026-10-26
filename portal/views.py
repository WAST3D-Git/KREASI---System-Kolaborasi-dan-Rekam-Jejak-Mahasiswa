"""Endpoint HTTP KREASI (lapisan PINTU MASUK / controller).

Alur singkat: browser memanggil URL -> urls.py meneruskan ke fungsi di sini -> fungsi memeriksa
login & bentuk permintaan -> pekerjaan berat diserahkan ke class lain:
    * data & hak akses fitur -> KreasiStateRepository (repository.py)   [ENKAPSULASI]
    * bentuk profil per peran -> AccountServiceFactory  (services.py)   [POLIMORFISME]
    * berkas                  -> model UploadedDocument (models.py)

Catatan: file ini sengaja memakai FUNGSI (function-based view), bukan class. OOP utama proyek
ada di models.py, services.py, repository.py, dan admin.py.

Peta endpoint -> fitur:
    index            GET  /                          halaman utama (HTML)
    session_info     GET  /api/session/              pulihkan login setelah refresh
    login_view       POST /api/auth/login/           tombol Masuk
    logout_view      POST /api/auth/logout/          tombol Keluar
    state_view       GET/POST /api/state/            baca / simpan semua data fitur
    state_version    GET  /api/state/version/        cek ada data baru (sinkronisasi)
    document_upload  POST /api/documents/upload/     unggah bukti/portofolio/dokumentasi
    document_detail  GET  /api/documents/<id>/       pratinjau/unduh berkas
    document_delete  POST /api/documents/<id>/delete/ hapus berkas
    health           GET  /healthz/                  pemeriksaan kesehatan hosting
"""
import json
import mimetypes
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import FileResponse, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .models import UploadedDocument
from .repository import KreasiStateRepository
from .services import AccountServiceFactory

# Batas berkas diperiksa pada server; validasi browser saja tidak cukup.
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".csv", ".txt", ".zip",
}
# Hanya tipe ini yang boleh dirender inline di browser; selainnya dipaksa unduh.
INLINE_SAFE_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/webp", "text/plain",
}
# Satu objek repository dipakai seluruh request; data persisten tetap berada di DB Django.
REPOSITORY = KreasiStateRepository()


def json_error(message, status=400):
    """Bentuk respons error JSON seragam: {"ok": false, "message": ...} dengan kode status HTTP."""
    return JsonResponse({"ok": False, "message": message}, status=status)


def body_json(request):
    """Baca isi permintaan sebagai JSON; kembalikan None bila rusak atau bukan objek."""
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        return data if isinstance(data, dict) else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def profile_for(user):
    """Profil pengguna untuk browser setelah login/pemulihan sesi.
    Isi data berbeda per peran karena memanggil AccountServiceFactory.serialize() (POLIMORFISME).
    """
    data = AccountServiceFactory.serialize(user)
    data["is_superuser"] = bool(user.is_superuser)
    data["is_staff"] = bool(user.is_staff)
    return data


INDEX_FILE = Path(__file__).resolve().parent / "static" / "portal" / "index.html"
_index_cache = {"mtime": None, "html": ""}


def _index_html():
    """Baca index.html sekali lalu simpan di memori; dibaca ulang hanya bila berkas berubah."""
    mtime = INDEX_FILE.stat().st_mtime
    if _index_cache["mtime"] != mtime:
        _index_cache.update(mtime=mtime, html=INDEX_FILE.read_text(encoding="utf-8"))
    return _index_cache["html"]


@ensure_csrf_cookie
@require_GET
def index(request):
    """FITUR: Halaman utama (landing, login, dan seluruh portal ada di satu file HTML).
    @ensure_csrf_cookie: memasang cookie CSRF agar permintaan POST berikutnya sah.
    """
    get_token(request)
    response = HttpResponse(_index_html(), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-cache"  # pembaruan frontend langsung terlihat setelah deploy
    return response


@require_GET
def health(request):
    """Pemeriksaan kesehatan ringan untuk hosting; tidak membuka data apa pun."""
    return JsonResponse({"ok": True})


@require_GET
def session_info(request):
    """FITUR: Tetap login setelah halaman dimuat ulang. Browser bertanya "sesi masih aktif?";
    bila ya, server mengirim profil sesuai peran.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False})
    return JsonResponse({"authenticated": True, "user": profile_for(request.user)})


@require_POST
def login_view(request):
    """FITUR: Login. Memakai mekanisme autentikasi Django (sandi dibandingkan dengan hash).

    Peran yang dipilih di layar login harus cocok dengan peran akun. Pesan kegagalan sengaja
    SAMA untuk semua penyebab (username salah, sandi salah, akun nonaktif, peran salah) agar
    penyerang tidak bisa mengetahui apakah suatu akun ada.
    """
    data = body_json(request)
    if not data:
        return json_error("Permintaan login tidak valid.")
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    requested_role = str(data.get("role", ""))
    if not username or not password:
        return json_error("Username dan kata sandi wajib diisi.")

    user = authenticate(request, username=username, password=password)  # Django mencocokkan hash sandi
    # Pesan generik sengaja sama untuk username, kata sandi, status, dan role salah,
    # agar respons tidak membocorkan keberadaan akun.
    if not user or not user.is_active or user.role != requested_role:
        return json_error("Akun tidak terdaftar di sistem", status=401)
    login(request, user)  # membuat sesi login di server (cookie sesi dikirim ke browser)
    return JsonResponse({"ok": True, "user": profile_for(user)})


@require_POST
def logout_view(request):
    """FITUR: Logout. Mengakhiri sesi di server (bukan sekadar mengganti tampilan)."""
    if request.user.is_authenticated:
        logout(request)
    return JsonResponse({"ok": True})


@require_http_methods(["GET", "POST"])
def state_view(request):
    """FITUR: Sumber & tujuan SEMUA data fitur (dashboard, proyek, prestasi, akun, SKPI, dll.).

      GET : kirim data yang boleh dilihat peran ini + nomor versi  (repository.get_state_for)
      POST: simpan perubahan dari browser dengan pembatasan peran   (repository.save_state)

    View hanya "pengantar"; aturan akses ada di KreasiStateRepository (ENKAPSULASI).
    `baseVersion` = versi data yang dipegang browser, dipakai untuk menangani data usang.
    """
    if not request.user.is_authenticated:
        return json_error("Sesi login diperlukan.", status=401)
    if request.method == "GET":
        # Versi dibaca sebelum state: bila ada penyimpanan di antaranya, klien hanya
        # menyegarkan sekali lagi (aman), bukan melewatkan perubahan.
        version = REPOSITORY.get_version()
        return JsonResponse({"ok": True, "version": version, "state": REPOSITORY.get_state_for(request.user)})

    payload = body_json(request)
    if not payload or not isinstance(payload.get("state"), dict):
        return json_error("Data sistem tidak valid.")
    base_version = payload.get("baseVersion")
    if not isinstance(base_version, int) or isinstance(base_version, bool):
        base_version = None
    try:
        data, version = REPOSITORY.save_state(payload["state"], request.user, base_version)
    except ValueError as exc:
        return json_error(str(exc))
    return JsonResponse({"ok": True, "version": version})


@require_GET
def state_version(request):
    """FITUR: Sinkronisasi. Endpoint ringan yang hanya mengembalikan nomor versi data."""
    if not request.user.is_authenticated:
        return json_error("Sesi login diperlukan.", status=401)
    return JsonResponse({"ok": True, "version": REPOSITORY.get_version()})


def _student_is_project_member(user, metadata):
    """[Pembantu izin] Apakah mahasiswa ini pembuat/anggota resmi proyek (atau kelompok) tsb?
    Dicek dari data SERVER, bukan dari NIM yang dikirim browser (karena bisa dipalsukan).
    Dipakai untuk izin unggah dokumentasi dan izin melihat berkas.
    """
    nim = str(user.identifier or "")
    state = REPOSITORY.get_state()
    project_id = str(metadata.get("projectId", ""))
    group_id = str(metadata.get("groupId") or "")
    project = next((p for p in state.get("projects", []) if str(p.get("id", "")) == project_id), None)
    if not project:
        return False
    # Pembuat proyek boleh mengunggah dokumentasi proyeknya sendiri.
    if str(project.get("creatorNim", "")) == nim:
        return True
    if group_id:
        groups = project.get("groups", []) if isinstance(project.get("groups"), list) else []
        group = next((g for g in groups if str(g.get("id", "")) == group_id), None)
        members = group.get("members", []) if isinstance(group, dict) and isinstance(group.get("members"), list) else []
        return any(isinstance(member, dict) and str(member.get("nim", "")) == nim and member.get("approved", True) is not False for member in members)
    members = project.get("members", []) if isinstance(project.get("members"), list) else []
    return any(isinstance(member, dict) and str(member.get("nim", "")) == nim and member.get("approved", True) is not False for member in members)


def can_access_document(user, document):
    """[Izin LIHAT berkas] Admin & dosen: boleh. Mahasiswa: pengunggahnya atau anggota proyek terkait.
    Dipisah dari izin hapus agar "boleh lihat" tidak otomatis berarti "boleh hapus".
    """
    if not user.is_authenticated:
        return False
    if user.role in {"admin", "lecturer"}:
        return True
    return document.uploaded_by_id == user.id or _student_is_project_member(user, document.metadata or {})


@require_POST
def document_upload(request):
    """FITUR: Unggah berkas (bukti prestasi, portofolio, lampiran proyek, dokumentasi tahapan).

    Pemeriksaan di SERVER (pemeriksaan di browser saja tidak cukup): login, ukuran maksimal
    10 MB, ekstensi diizinkan, metadata valid, dan untuk mahasiswa: kepemilikan sesuai tujuan
    unggahan (`purpose`) — portofolio/bukti prestasi harus atas NIM sendiri, dokumentasi harus
    oleh anggota proyek. Tipe konten ditentukan dari ekstensi, bukan dari klaim browser.
    """
    if not request.user.is_authenticated:
        return json_error("Sesi login diperlukan.", status=401)
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return json_error("Pilih berkas yang akan diunggah.")
    if uploaded_file.size > MAX_FILE_SIZE:
        return json_error("Ukuran berkas maksimal 10 MB.")
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return json_error("Format berkas tidak didukung.")
    try:
        metadata = json.loads(request.POST.get("metadata", "{}"))
        if not isinstance(metadata, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        return json_error("Metadata berkas tidak valid.")

    user = request.user
    purpose = str(metadata.get("purpose", ""))
    if user.role == "student":
        if purpose in {"portfolio", "achievement-proof"} and str(metadata.get("nim", "")) != str(user.identifier):
            return json_error("Anda hanya dapat mengunggah dokumen untuk akun sendiri.", status=403)
        if purpose == "milestone" and not _student_is_project_member(user, metadata):
            return json_error("Dokumentasi hanya dapat dikirim oleh anggota proyek/kelompok terkait.", status=403)
        if purpose == "project-attachment" and str(metadata.get("nim", user.identifier)) != str(user.identifier):
            return json_error("Lampiran proyek tidak sesuai dengan akun aktif.", status=403)

    record = UploadedDocument.objects.create(
        file=uploaded_file,
        original_name=Path(uploaded_file.name).name[:255],
        # Tipe ditentukan dari ekstensi (tervalidasi), bukan header klien yang dapat dipalsukan.
        content_type=mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream",
        size=uploaded_file.size,
        uploaded_by=user,
        metadata=metadata,
    )
    return JsonResponse({"ok": True, "id": str(record.id), "name": record.original_name, "size": record.size})


@require_GET
def document_detail(request, document_id):
    """FITUR: Pratinjau/unduh berkas. Memeriksa login lalu izin (can_access_document).
    Hanya PDF, gambar, dan teks biasa yang ditampilkan langsung; tipe lain dipaksa diunduh
    agar berkas berbahaya (mis. HTML) tidak dijalankan di domain situs.
    """
    if not request.user.is_authenticated:
        return json_error("Sesi login diperlukan.", status=401)
    try:
        document = UploadedDocument.objects.get(pk=document_id)
    except UploadedDocument.DoesNotExist:
        return json_error("Berkas tidak ditemukan.", status=404)
    if not can_access_document(request.user, document):
        return json_error("Anda tidak berwenang membuka berkas ini.", status=403)
    try:
        content = document.file.open("rb")
    except (FileNotFoundError, OSError):
        return json_error("Berkas fisik tidak ditemukan di penyimpanan server.", status=404)
    # Tipe dihitung ulang dari ekstensi agar data lama dengan tipe palsu (mis. text/html) aman.
    content_type = mimetypes.guess_type(document.original_name)[0] or "application/octet-stream"
    disposition = "inline" if content_type in INLINE_SAFE_TYPES else "attachment"
    response = FileResponse(content, content_type=content_type)
    safe_name = quote(document.original_name)
    response["Content-Disposition"] = f"{disposition}; filename*=UTF-8''{safe_name}"
    response["X-Document-Name"] = safe_name
    response["X-Content-Type-Options"] = "nosniff"
    return response


def can_delete_document(user, document):
    """[Izin HAPUS berkas] Admin & pengunggah: boleh. Lainnya hanya bila terkait proyeknya:
    mahasiswa (pembuat/anggota), dosen (pemilik/pembimbing proyek).
    """
    if not user.is_authenticated:
        return False
    if user.role == "admin" or document.uploaded_by_id == user.id:
        return True
    project_id = str((document.metadata or {}).get("projectId", ""))
    if not project_id:
        return False
    project = next((p for p in REPOSITORY.get_state().get("projects", [])
                    if str(p.get("id", "")) == project_id), None)
    if not project:
        return False
    identity = str(user.identifier or "")
    metadata = document.metadata or {}
    if user.role == "student":
        if str(project.get("creatorNim", "")) == identity:
            return True
        group_id = str(metadata.get("groupId") or "")
        if group_id:
            groups = project.get("groups", []) if isinstance(project.get("groups"), list) else []
            group = next((row for row in groups if str(row.get("id", "")) == group_id), None)
            members = group.get("members", []) if isinstance(group, dict) and isinstance(group.get("members"), list) else []
            return any(isinstance(member, dict) and str(member.get("nim", "")) == identity and member.get("approved", True) is not False for member in members)
        members = project.get("members", []) if isinstance(project.get("members"), list) else []
        return any(isinstance(member, dict) and str(member.get("nim", "")) == identity and member.get("approved", True) is not False for member in members)
    if user.role == "lecturer":
        owner_nip = str(project.get("ownerNip", ""))
        if owner_nip:
            return owner_nip == identity
        return identity in {str(project.get("creatorNip", "")), str(project.get("supervisorNip", ""))}
    return False


@require_POST
def document_delete(request, document_id):
    """FITUR: Hapus berkas (file fisik + catatan database) bila can_delete_document mengizinkan."""
    if not request.user.is_authenticated:
        return json_error("Sesi login diperlukan.", status=401)
    try:
        document = UploadedDocument.objects.get(pk=document_id)
    except UploadedDocument.DoesNotExist:
        return json_error("Berkas tidak ditemukan.", status=404)
    if not can_delete_document(request.user, document):
        return json_error("Anda tidak berwenang menghapus berkas ini.", status=403)
    # POST dipakai untuk penghapusan agar permintaan tetap kompatibel dengan kebijakan CSRF.
    document.file.delete(save=False)  # 1) hapus file fisik dari MEDIA_ROOT
    document.delete()                 # 2) hapus catatannya di database
    return JsonResponse({"ok": True})
