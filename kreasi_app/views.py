"""View halaman dan API yang menghubungkan antarmuka KREASI dengan Django."""
import json
from urllib.parse import quote
from django.contrib.auth import logout as django_logout
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.http import content_disposition_header
from .models import ApplicationState, StoredDocument
from .services import AccountServiceFactory, StateService, DocumentService

state_service = StateService()
document_service = DocumentService()

@ensure_csrf_cookie
def home(request):
    """Menampilkan HTML asli sebagai template sambil menyiapkan cookie CSRF."""
    return render(request, "kreasi_app/index.html")

@require_http_methods(["GET", "PUT"])
def state_api(request):
    """Mengirim atau menyimpan state aplikasi dalam database, dengan bentuk JSON yang sama."""
    if request.method == "GET":
        return JsonResponse({"data": state_service.load_state()})
    try:
        if len(request.body) > 22 * 1024 * 1024:
            return JsonResponse({"error": "Data terlalu besar untuk disimpan."}, status=413)
        body = json.loads(request.body.decode("utf-8"))
        state_service.store_state(body.get("data"), request.session.get("kreasi_role"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Isi permintaan bukan JSON yang valid."}, status=400)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except PermissionError as error:
        return JsonResponse({"error": str(error)}, status=403)
    return JsonResponse({"ok": True})

@require_POST
def session_api(request):
    """Memeriksa kredensial akun dummy lalu membuat sesi Django untuk perubahan data."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Permintaan login tidak dapat dibaca."}, status=400)
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    data = state_service.load_state() or {}
    users = data.get("users", []) if isinstance(data, dict) else []
    user = next((item for item in users if str(item.get("username", "")) == username), None)
    if not user or str(user.get("password", "")) != password:
        return JsonResponse({"error": "Username atau kata sandi tidak sesuai."}, status=401)
    if not user.get("active", True):
        return JsonResponse({"error": "Akun sedang nonaktif."}, status=403)
    role = str(user.get("role", ""))
    try:
        # Factory memilih service profil berdasarkan peran; setiap service membentuk field-nya sendiri.
        login_profile = AccountServiceFactory.serialize(user)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=403)
    request.session.cycle_key()  # Mengganti ID sesi setelah login untuk mengurangi risiko session fixation.
    request.session["kreasi_role"] = role
    request.session["kreasi_username"] = username
    request.session["kreasi_identity"] = str(user.get("nim") or user.get("nip") or user.get("id") or "")
    request.session["kreasi_profile"] = login_profile  # Simpan profil aman untuk kebutuhan sesi berikutnya.
    return JsonResponse({"ok": True, "role": role, "profile": login_profile})

@require_POST
def session_logout_api(request):
    """Menghapus sesi Django saat pengguna keluar dari portal KREASI."""
    request.session.flush()
    django_logout(request)
    return JsonResponse({"ok": True})

@require_http_methods(["POST", "GET", "DELETE"])
def document_api(request, document_id=None):
    """Menyimpan, mengambil, atau menghapus dokumen yang diunggah pada alur kerja KREASI."""
    role = request.session.get("kreasi_role")
    if not role:
        return JsonResponse({"error": "Silakan masuk terlebih dahulu untuk mengelola berkas."}, status=401)
    if request.method == "POST":
        uploaded = request.FILES.get("file")
        try:
            metadata_raw = request.POST.get("metadata", "{}")
            metadata = json.loads(metadata_raw)
            document = document_service.create(uploaded, metadata, role)
        except (json.JSONDecodeError, ValueError) as error:
            return JsonResponse({"error": str(error)}, status=400)
        except PermissionError as error:
            return JsonResponse({"error": str(error)}, status=403)
        return JsonResponse({"id": document.id, "name": document.original_name, "size": document.size}, status=201)
    if not document_id:
        return JsonResponse({"error": "ID dokumen wajib diisi."}, status=400)
    if request.method == "DELETE":
        try:
            removed = document_service.delete(document_id, role)
        except PermissionError as error:
            return JsonResponse({"error": str(error)}, status=403)
        return JsonResponse({"ok": True, "deleted": removed})
    try:
        document = document_service.get(document_id, role)
    except PermissionError as error:
        return JsonResponse({"error": str(error)}, status=403)
    if not document or not document.file:
        return JsonResponse({"error": "Berkas tidak ditemukan."}, status=404)
    # FileResponse mengalirkan file dari disk sehingga berkas tidak perlu dimuat seluruhnya ke memori.
    response = FileResponse(document.file.open("rb"), content_type=document.content_type or "application/octet-stream")
    response["X-Document-Name"] = quote(document.original_name or "dokumen")
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = content_disposition_header(False, document.original_name or "dokumen")
    return response
