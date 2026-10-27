"""Mendaftarkan model agar data dapat diperiksa melalui Django Admin."""
from django.contrib import admin
from .models import ApplicationState, StoredDocument

@admin.register(ApplicationState)
class ApplicationStateAdmin(admin.ModelAdmin):
    """Menampilkan ringkasan state tanpa harus membuka JSON secara default."""
    list_display = ("key", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")

@admin.register(StoredDocument)
class StoredDocumentAdmin(admin.ModelAdmin):
    """Memudahkan pemeriksaan metadata dokumen yang tersimpan di server."""
    list_display = ("id", "original_name", "content_type", "size", "created_at")
    search_fields = ("id", "original_name")
    readonly_fields = ("created_at", "updated_at")
