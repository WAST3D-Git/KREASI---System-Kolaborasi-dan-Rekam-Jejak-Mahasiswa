# Dibuat untuk struktur database awal KREASI.
from django.db import migrations, models

class Migration(migrations.Migration):
    """Membuat tabel state aplikasi dan metadata berkas untuk instalasi pertama."""
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="ApplicationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, help_text="Waktu data pertama kali dibuat.")),
                ("updated_at", models.DateTimeField(auto_now=True, help_text="Waktu terakhir data diubah.")),
                ("key", models.CharField(default="kreasi-default", max_length=80, unique=True)),
                ("payload", models.JSONField(default=dict, help_text="Data proyek, akun demo, prestasi, dan pengaturan.")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="StoredDocument",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, help_text="Waktu data pertama kali dibuat.")),
                ("updated_at", models.DateTimeField(auto_now=True, help_text="Waktu terakhir data diubah.")),
                ("id", models.CharField(max_length=40, primary_key=True, serialize=False)),
                ("file", models.FileField(upload_to="kreasi_documents/%Y/%m/")),
                ("original_name", models.CharField(max_length=255)),
                ("content_type", models.CharField(default="application/octet-stream", max_length=150)),
                ("size", models.PositiveBigIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={"abstract": False},
        ),
    ]
