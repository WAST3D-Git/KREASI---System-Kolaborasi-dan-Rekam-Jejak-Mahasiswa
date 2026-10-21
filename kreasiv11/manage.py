#!/usr/bin/env python
"""Utilitas command line untuk menjalankan tugas administrasi Django."""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kreasi_project.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
