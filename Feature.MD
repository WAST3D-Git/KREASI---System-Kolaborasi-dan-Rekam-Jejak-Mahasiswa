# FEATURE — Fitur KREASI

Dokumen ini merangkum fitur yang terlihat di antarmuka KREASI `v11.2.html`. Versi Django mempertahankan halaman dan fungsi JavaScript sumber, kemudian menghubungkan penyimpanan data serta lampiran ke backend.

## 1. Halaman awal dan login

- **Halaman awal KREASI:** memperkenalkan sistem kolaborasi dan rekam jejak prestasi mahasiswa, beserta akses ke portal.
- **Login berbasis peran:** pengguna memilih portal Mahasiswa, Dosen, atau Administrator, lalu memasukkan username dan kata sandi.
- **Status akun:** login menolak username yang tidak terdaftar, kata sandi salah, akun nonaktif, atau peran yang tidak cocok.
- **Panduan penggunaan:** dialog panduan memberi arahan sesuai peran.
- **Keluar dari sistem:** konfirmasi ditampilkan sebelum halaman kembali ke tampilan awal.

## 2. Fitur mahasiswa

Menu portal mahasiswa terdiri dari Dashboard, Profil & Talenta, Rekam Jejak Prestasi, SKPI, Bursa Proyek, dan Proyek Saya.

### Dashboard

Menampilkan ringkasan aktivitas mahasiswa, proyek yang berkaitan, undangan kolaborasi, notifikasi, dan pengingat dokumen yang perlu ditindaklanjuti.

### Profil & Talenta

Mahasiswa dapat melihat profil akademik dan data talenta, memperbarui informasi profil yang diizinkan, mengelola daftar keahlian, serta menambah atau menghapus item portofolio beserta lampirannya. Informasi yang relevan disinkronkan dengan Katalog Talenta.

### Rekam Jejak Prestasi

Mahasiswa dapat mengajukan prestasi dan mengunggah berkas bukti. Status pengajuan ditampilkan agar mahasiswa mengetahui apakah bukti masih menunggu pemeriksaan, disetujui, ditolak, atau membutuhkan tindakan lanjutan. Lampiran yang masih terikat pada pengajuan dapat dihapus sesuai alur yang ditampilkan.

### SKPI mahasiswa

Mahasiswa dapat melihat pratinjau rekam jejak/SKPI. Pencetakan dokumen resmi dan proses finalisasi dikelola dari portal administrator.

### Bursa Proyek

Mahasiswa dapat menelusuri proyek, mencari teks, memfilter jenis proyek, membaca detail, dan mengajukan diri jika memenuhi syarat. Kategori umum dapat digunakan untuk kolaborasi. Proyek mata kuliah dan Informatika Untuk Masyarakat (IUM) mengikuti aturan visibilitas dan keanggotaan yang lebih ketat.

Form pendaftaran proyek memuat keahlian relevan, peran yang dilamar, dan motivasi. Sistem memeriksa kelengkapan data dan mencegah pendaftaran berulang pada proyek yang sama.

### Proyek Saya

Mahasiswa dapat melihat proyek yang dimiliki atau diikuti, status pendaftaran/keanggotaan, tahapan dokumentasi, catatan pembimbing, revisi, progres proyek, dan lampiran yang tersedia. Beberapa proyek mendukung kelompok dengan kapasitas anggota dan persetujuan keanggotaan.

### Undangan dan notifikasi

Undangan kolaborasi dapat dibuka untuk melihat detail, lalu diterima atau ditolak. Notifikasi dapat menampilkan pengingat seputar dokumen, revisi, serta undangan.

## 3. Fitur dosen

Menu portal dosen terdiri dari Dashboard Dosen, Profil Dosen, Talent Pool, dan Manajemen Proyek.

### Dashboard Dosen

Meringkas aktivitas proyek yang memerlukan perhatian dosen, terutama usulan proyek dan pekerjaan bimbingan yang masih menunggu tindakan.

### Profil Dosen

Menampilkan NIP, NIDN, jabatan fungsional, bidang keahlian, mata kuliah yang diampu, riwayat pendidikan, dan publikasi. Bentuk data profil mengikuti akun demo yang tersedia.

### Talent Pool

Dosen dapat menjelajahi data mahasiswa aktif beserta keahlian, IPK, portofolio, dan informasi pendukung yang tersedia di data demo. Informasi ini membantu pencarian kandidat dengan keahlian yang sesuai kebutuhan proyek.

### Manajemen Proyek dan usulan

Dosen dapat meninjau usulan proyek, membuat proyek, memperbarui detail proyek, dan melihat daftar proyek yang sesuai dengan kewenangannya. Kategori Proyek Mata Kuliah terkait dengan mata kuliah yang diampu serta angkatan/kelas yang telah ditentukan. Usulan tanpa dosen tujuan mengikuti aturan peninjauan yang tersedia pada logika aplikasi.

### Kelompok dan anggota

Untuk proyek berkelompok, dosen dapat mengelola kelompok, menambah atau menghapus kelompok, mengatur anggota, serta memeriksa usulan keanggotaan. Keanggotaan proyek mata kuliah mempertimbangkan mata kuliah, angkatan, kelas, kapasitas kelompok, dan persetujuan dosen.

### Verifikasi dokumentasi dan bimbingan

Tahapan dapat berisi proposal, perizinan, kaji etik/instrumen, laporan kemajuan, dokumentasi lapangan, laporan akhir, dan luaran. Dosen dapat memeriksa berkas, memberikan persetujuan atau meminta revisi, serta menuliskan catatan bimbingan sesuai tampilan detail proyek. Beberapa proyek dapat menambah tahapan secara manual.

### Penilaian proyek

Setelah seluruh dokumentasi target disetujui dan proyek/kelompok ditandai selesai, dosen dapat memberikan nilai proyek mata kuliah. Mode penilaian mendukung kelompok, individu, atau keduanya. Nilai numerik dikonversi ke predikat huruf secara otomatis.

## 4. Fitur administrator

Menu portal administrator terdiri dari Dashboard Admin, Validasi Prestasi, Manajemen Akun, Pengumuman Akademik, Kategori & Poin, dan Rekapitulasi & SKPI.

### Dashboard Admin

Menampilkan ringkasan terkait akun, pengajuan prestasi, pengumuman, dan status finalisasi SKPI.

### Validasi Prestasi

Administrator memeriksa bukti pengajuan prestasi mahasiswa, menyetujui atau menolak pengajuan, dan dapat melihat status serta riwayat keputusan yang disimpan oleh aplikasi.

### Manajemen Akun

Administrator dapat menambah, mengubah, dan mengelola akun mahasiswa serta dosen. Data mahasiswa meliputi identitas, angkatan/kelas, IPK, mata kuliah yang diambil, dan status aktif. Data dosen mencakup identitas dan mata kuliah beserta angkatan/kelas yang diampu. Fitur sumber juga menyediakan reset kata sandi serta pengaktifan/nonaktifkan akun.

### Pengumuman Akademik

Administrator dapat mengelola pengumuman yang muncul pada portal sesuai fungsi dalam antarmuka. Daftar pengumuman berasal dari data aplikasi.

### Data Master: kategori, mata kuliah, dan poin

Administrator dapat mengelola kategori proyek, mata kuliah, penawaran mata kuliah, kategori prestasi, dan ambang poin MEXS. Kategori yang digunakan formulir proyek mengikuti data master sehingga perubahan pada data master dapat tercermin di formulir.

### Rekapitulasi dan SKPI

Administrator dapat melihat daftar mahasiswa dan ringkasan rekam prestasi, melakukan finalisasi SKPI, mengekspor hasil secara massal, serta mencetak dokumen mahasiswa yang sudah memenuhi syarat finalisasi. Pencetakan tidak ditampilkan sebagai tindakan bebas untuk mahasiswa.

## 5. Aturan proyek dan dokumentasi yang penting

- **Kategori proyek umum:** dapat ditampilkan pada bursa proyek sesuai kategori yang diaktifkan.
- **Proyek Mata Kuliah:** visibilitas dibatasi berdasarkan mahasiswa yang mengambil mata kuliah, dosen pengampu/pembimbing, anggota, pembuat, atau cakupan angkatan/kelas sesuai status proyek.
- **Informatika Untuk Masyarakat:** memakai penetapan mata kuliah terkait dan aturan akses lebih ketat daripada proyek umum.
- **Anggota kelompok:** ada pemeriksaan kapasitas, persetujuan anggota, lingkup kelas/mata kuliah, dan pembatasan anggota yang sudah tergabung kelompok lain.
- **Dokumentasi:** setiap tahap menyimpan status, lampiran, waktu pengajuan/verifikasi, catatan, dan jumlah revisi sesuai data tahap.
- **Progres:** dihitung dari tahapan yang berstatus Disetujui; proyek kelompok menggabungkan progres kelompok-kelompok di dalamnya.
- **Penilaian:** nilai diberikan setelah syarat dokumentasi selesai terpenuhi; predikat huruf dihitung oleh fungsi penilaian.

## 6. Interaksi umum dan aksesibilitas

- Navigasi samping responsif untuk layar desktop maupun perangkat yang lebih kecil.
- Pencarian pada daftar yang mendukung atribut pencarian dan filter kategori.
- Dialog untuk form, konfirmasi, panduan, dan detail.
- Toast untuk informasi berhasil, peringatan, dan kesalahan.
- Pemilih file kustom dengan nama berkas, ukuran, dan tombol hapus pilihan.
- Fokus keyboard yang terlihat, tautan lewati ke konten utama, label ARIA pada komponen terkait, dan tombol Escape untuk menutup dialog.
- Gaya cetak khusus digunakan untuk dokumen yang perlu dicetak dari browser.

## 7. Integrasi Django pada versi konversi

| Bagian | Peran |
|---|---|
| `GET /api/state/` | Mengambil state aplikasi yang disimpan di database. |
| `PUT /api/state/` | Menyimpan perubahan data JSON setelah sesi dengan peran yang dikenali dibuat. |
| `POST /api/session/` | Memeriksa akun demo dari state dan membuat sesi Django. |
| `POST /api/session/logout/` | Mengakhiri sesi Django. |
| `POST /api/documents/` | Menyimpan lampiran ke media server dan metadata ke database. |
| `GET /api/documents/<id>/` | Mengambil isi lampiran untuk pratinjau/unduhan. |
| `DELETE /api/documents/<id>/` | Menghapus lampiran yang tersimpan. |

### Struktur layanan akun berbasis OOP

Login demo menggunakan service backend yang dipilih berdasarkan peran. `BaseAccountService` merupakan class abstrak yang menjadi dasar `StudentAccountService`, `LecturerAccountService`, dan `AdminAccountService`. Ketiganya memiliki kontrak `build_profile()` dan `serialize_login_profile()`, tetapi menghasilkan field yang sesuai dengan data mahasiswa, dosen, atau administrator.

`AccountServiceFactory` memilih service berdasarkan `role`. Alurnya digunakan langsung oleh endpoint `POST /api/session/`, bukan hanya contoh untuk dokumentasi. Factory menormalkan data akun dan mengembalikan profil login tanpa field kata sandi. Class `StateService` menangani validasi dan penyimpanan payload melalui `DjangoStateRepository` serta `PermissionService`; `DocumentService` menangani upload, baca, dan penghapusan berkas.

Pola pewarisan yang nyata: single inheritance pada tiap service akun yang mewarisi `BaseAccountService`; multilevel inheritance pada rantai `ABC → BaseAccountService → service akun`; hierarchical inheritance karena tiga service berbagi induk yang sama. `ApplicationState` dan `StoredDocument` juga mewarisi `TimestampedModel`. Multiple inheritance tidak digunakan oleh service KREASI; ketergantungan repository dan izin diberikan melalui komposisi.

## 8. Batasan versi demo

Tampilan lama menjalankan banyak validasi dan aturan bisnis pada JavaScript. Backend Django kini menangani penyimpanan utama dan sesi demo, tetapi data bisnis masih berbentuk JSON agar konversi tidak mengubah struktur UI. Sebelum digunakan untuk data nyata, aturan otorisasi per objek harus dipindahkan dan dites di server, akun perlu memakai sistem autentikasi Django, serta model proyek/anggota/prestasi/tahapan sebaiknya dibuat relasional.
