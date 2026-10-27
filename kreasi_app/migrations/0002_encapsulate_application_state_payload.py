"""Menyediakan getter/setter tanpa mengganti kolom database yang sudah berisi data."""
from django.db import migrations, models


class Migration(migrations.Migration):
    """Mengubah nama field di model, sambil mempertahankan nama kolom database payload."""

    dependencies = [
        ("kreasi_app", "0001_initial"),
    ]

    operations = [
        # Nama kolom fisik tetap "payload"; yang berubah hanya nama field Python.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameField(
                    model_name="applicationstate",
                    old_name="payload",
                    new_name="_payload_data",
                ),
                migrations.AlterField(
                    model_name="applicationstate",
                    name="_payload_data",
                    field=models.JSONField(
                        db_column="payload",
                        default=dict,
                        help_text="Data proyek, akun demo, prestasi, dan pengaturan.",
                    ),
                ),
            ],
        ),
    ]
