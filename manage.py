#!/usr/bin/env python
"""Perintah untuk menjalankan perintah administrasi Django pada proyek KREASI."""
import os
import sys

def main():
    # Menentukan konfigurasi proyek sebelum perintah Django dijalankan.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kreasi_site.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
