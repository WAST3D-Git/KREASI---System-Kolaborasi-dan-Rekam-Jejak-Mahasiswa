"""Pendaftaran model ke Django Admin (/django-admin/) — halaman pengelolaan data bawaan Django.

File ini menunjukkan PEWARISAN: class admin di bawah mewarisi class bawaan Django lalu
hanya menyesuaikan kolom/formulirnya. Bukan bagian alur fitur utama KREASI.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppState, PortalUser, UploadedDocument

# Kelas Admin berikut mewarisi komponen Django Admin dan hanya mengatur kolom/form,
# sehingga pengelolaan model KREASI memakai mekanisme autentikasi serta permission Django.

@admin.register(PortalUser)
class PortalUserAdmin(UserAdmin):
    """Tampilan Django Admin untuk tabel akun (PortalUser) di alamat /django-admin/.

    OOP: PEWARISAN TUNGGAL dari `UserAdmin` (bawaan Django). Form tambah/ubah akun lengkap
    (sandi ter-hash, grup, permission) diwarisi; kita hanya MENAMBAH bagian "KREASI"
    (role, identifier, full_name, profile_data) pada `fieldsets`. Ini jalur cadangan untuk
    pengelola teknis; pengguna biasa mengelola akun lewat menu Manajemen Akun di aplikasi.
    """
    list_display = ("username", "full_name", "role", "identifier", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("KREASI", {"fields": ("role", "identifier", "full_name", "profile_data")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("KREASI", {"fields": ("role", "identifier", "full_name", "profile_data")}),)

@admin.register(AppState)
class AppStateAdmin(admin.ModelAdmin):
    """Tampilan admin untuk melihat nomor versi dan waktu pembaruan data aplikasi.
    OOP: PEWARISAN TUNGGAL dari `ModelAdmin`. `version` & `updated_at` dibuat read-only
    agar tidak diubah manual (versi hanya dinaikkan oleh repository.save_state).
    """
    list_display = ("key", "version", "updated_at")
    readonly_fields = ("version", "updated_at")

@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    """Tampilan admin untuk audit berkas unggahan (siapa mengunggah apa, ukuran, kapan).
    OOP: PEWARISAN TUNGGAL dari `ModelAdmin`.
    """
    list_display = ("original_name", "content_type", "size", "uploaded_by", "created_at")
    readonly_fields = ("created_at",)
