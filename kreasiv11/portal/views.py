"""Endpoint HTTP untuk frontend KREASI.

Modul ini menggunakan function-based views Django (bukan class-based views). View bertugas
membaca request, memeriksa sesi/format, dan membentuk respons; aturan bisnis state didelegasikan
ke `KreasiStateRepository`, sedangkan bentuk profil akun didelegasikan ke `AccountServiceFactory`.
Permintaan tulis menggunakan middleware CSRF Django.
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
# Satu objek repository dipakai seluruh request; data persisten tetap berada di DB Django.
REPOSITORY = KreasiStateRepository()


def json_error(message, status=400):
    return JsonResponse({"ok": False, "message": message}, status=status)


def body_json(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        return data if isinstance(data, dict) else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def profile_for(user):
    """Bentuk payload sesi dengan serialisasi yang ditentukan service peran."""
    data = AccountServiceFactory.serialize(user)
    data["is_superuser"] = bool(user.is_superuser)
    data["is_staff"] = bool(user.is_staff)
    return data


@ensure_csrf_cookie
@require_GET
def index(request):
    """Sajikan frontend statis asli tanpa memproses sintaks JavaScript sebagai template."""
    get_token(request)
    source = Path(__file__).resolve().parent / "static" / "portal" / "index.html"
    return HttpResponse(source.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")


@require_GET
def session_info(request):
    """Berikan status sesi saat ini agar halaman dapat memulihkan login setelah reload."""
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False})
    return JsonResponse({"authenticated": True, "user": profile_for(request.user)})


@require_POST
def login_view(request):
    """Autentikasi username/password, cocokkan role, lalu buat sesi Django."""
    data = body_json(request)
    if not data:
        return json_error("Permintaan login tidak valid.")
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    requested_role = str(data.get("role", ""))
    if not username or not password:
        return json_error("Username dan kata sandi wajib diisi.")

    user = authenticate(request, username=username, password=password)
    # Pesan generik sengaja sama untuk username, kata sandi, status, dan role salah,
    # agar respons tidak membocorkan keberadaan akun.
    if not user or not user.is_active or user.role != requested_role:
        return json_error("Akun tidak terdaftar di sistem", status=401)
    login(request, user)
    return JsonResponse({"ok": True, "user": profile_for(user)})


@require_POST
def logout_view(request):
    """Akhiri sesi server; perubahan UI saja tidak menggantikan logout Django."""
    if request.user.is_authenticated:
        logout(request)
    return JsonResponse({"ok": True})


@require_http_methods(["GET", "POST"])
def state_view(request):
    """GET membaca state sesuai role; POST menyimpan lewat repository yang memvalidasi hak."""
    if not request.user.is_authenticated:
        return json_error("Sesi login diperlukan.", status=401)
    if request.method == "GET":
        return JsonResponse({"ok": True, "state": REPOSITORY.get_state_for(request.user)})

    payload = body_json(request)
    if not payload or not isinstance(payload.get("state"), dict):
        return json_error("Data sistem tidak valid.")
    try:
        data, version = REPOSITORY.save_state(payload["state"], request.user)
    except ValueError as exc:
        return json_error(str(exc))
    return JsonResponse({"ok": True, "version": version})


def _student_is_project_member(user, metadata):
    """Periksa keanggotaan langsung di server; metadata NIM dari browser tidak dipercaya."""
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
    """Pisahkan hak pratinjau dari keberadaan ID dokumen yang dikirim browser."""
    if not user.is_authenticated:
        return False
    if user.role in {"admin", "lecturer"}:
        return True
    return document.uploaded_by_id == user.id or _student_is_project_member(user, document.metadata or {})


@require_POST
def document_upload(request):
    """Terima unggahan dengan batas ukuran/ekstensi dan validasi kepemilikan berdasarkan role."""
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
        content_type=uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream",
        size=uploaded_file.size,
        uploaded_by=user,
        metadata=metadata,
    )
    return JsonResponse({"ok": True, "id": str(record.id), "name": record.original_name, "size": record.size})


@require_GET
def document_detail(request, document_id):
    """Kirim berkas asli untuk pratinjau setelah sesi dan izin akses diperiksa."""
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
    response = FileResponse(content, content_type=document.content_type)
    safe_name = quote(document.original_name)
    response["Content-Disposition"] = f"inline; filename*=UTF-8''{safe_name}"
    response["X-Document-Name"] = safe_name
    response["X-Content-Type-Options"] = "nosniff"
    return response


def can_delete_document(user, document):
    """Periksa hak penghapusan secara terpisah dari hak melihat/pratinjau dokumen.

    Admin dan pengunggah dapat menghapus berkas; mahasiswa/dosen lain harus cocok dengan
    identitas pemilik atau hubungan mereka dengan proyek sesuai metadata yang disimpan.
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
    """Hapus metadata dan file fisik hanya jika pengguna memiliki hak penghapusan."""
    if not request.user.is_authenticated:
        return json_error("Sesi login diperlukan.", status=401)
    try:
        document = UploadedDocument.objects.get(pk=document_id)
    except UploadedDocument.DoesNotExist:
        return json_error("Berkas tidak ditemukan.", status=404)
    if not can_delete_document(request.user, document):
        return json_error("Anda tidak berwenang menghapus berkas ini.", status=403)
    # POST dipakai untuk penghapusan agar permintaan tetap kompatibel dengan kebijakan CSRF.
    document.file.delete(save=False)
    document.delete()
    return JsonResponse({"ok": True})
