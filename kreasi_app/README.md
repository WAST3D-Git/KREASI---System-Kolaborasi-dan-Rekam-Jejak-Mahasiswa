# Aplikasi KREASI

Lihat `../README.md` untuk panduan lengkap.

## Struktur layanan

- `BaseAccountService` menetapkan kontrak bersama layanan akun.
- `StudentAccountService`, `LecturerAccountService`, dan `AdminAccountService` menyiapkan profil sesuai peran.
- `AccountServiceFactory` memilih service dan dipakai oleh endpoint `POST /api/session/`.
- `StateService` menggunakan `DjangoStateRepository` dan `PermissionService` melalui komposisi untuk validasi serta penyimpanan state.
- `ApplicationState` menyediakan getter `get_payload()` dan setter `set_payload()`; property `payload` juga diarahkan ke dua method tersebut agar pembacaan mendapat salinan dan perubahan tervalidasi.
- `DocumentService` mengelola upload, pembacaan, dan penghapusan dokumen.

Komentar berbahasa Indonesia di dalam class dan method menjelaskan peran kode untuk pembelajaran OOP.
