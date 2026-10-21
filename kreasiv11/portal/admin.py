from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppState, PortalUser, UploadedDocument

# Kelas Admin berikut mewarisi komponen Django Admin dan hanya mengatur kolom/form,
# sehingga pengelolaan model KREASI memakai mekanisme autentikasi serta permission Django.

@admin.register(PortalUser)
class PortalUserAdmin(UserAdmin):
    """Pewarisan tunggal dari UserAdmin untuk menambahkan field khusus akun KREASI."""
    list_display = ("username", "full_name", "role", "identifier", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("KREASI", {"fields": ("role", "identifier", "full_name", "profile_data")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("KREASI", {"fields": ("role", "identifier", "full_name", "profile_data")}),)

@admin.register(AppState)
class AppStateAdmin(admin.ModelAdmin):
    """Pewarisan tunggal dari ModelAdmin untuk melihat versi snapshot sistem."""
    list_display = ("key", "version", "updated_at")
    readonly_fields = ("version", "updated_at")

@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    """Pewarisan tunggal dari ModelAdmin untuk audit metadata dokumen unggahan."""
    list_display = ("original_name", "content_type", "size", "uploaded_by", "created_at")
    readonly_fields = ("created_at",)
