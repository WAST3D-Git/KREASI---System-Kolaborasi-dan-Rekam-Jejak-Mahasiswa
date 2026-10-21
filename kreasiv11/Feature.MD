# Feature.MD — Panduan Fitur dan Alur Penggunaan KREASI

Dokumen ini menjelaskan fitur dan alur penggunaan situs **KREASI (Sistem Kolaborasi dan Rekam Jejak Prestasi Mahasiswa)** dengan bahasa sederhana. Penjelasan disusun berdasarkan kode frontend `portal/static/portal/index.html` dan backend Django pada folder `portal/` di proyek ini.

> **Catatan ruang lingkup:** panduan ini menerangkan fitur yang ditemukan pada kode sumber. Ketersediaan data dan sebagian tindakan bergantung pada akun, peran, data master, status proyek, dan hak akses. Dokumentasi ini bukan pernyataan bahwa semua alur telah diuji pada server produksi.

## Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Peran Pengguna](#2-peran-pengguna)
3. [Cara Membuka dan Masuk ke Sistem](#3-cara-membuka-dan-masuk-ke-sistem)
4. [Fitur Umum](#4-fitur-umum)
5. [Fitur Mahasiswa](#5-fitur-mahasiswa)
6. [Fitur Dosen](#6-fitur-dosen)
7. [Fitur Administrator](#7-fitur-administrator)
8. [Alur Lengkap Proyek](#8-alur-lengkap-proyek)
9. [Alur Prestasi, Poin MEXS, dan SKPI](#9-alur-prestasi-poin-mexs-dan-skpi)
10. [Unggah dan Pengelolaan Dokumen](#10-unggah-dan-pengelolaan-dokumen)
11. [Ringkasan Aturan dan Validasi Penting](#11-ringkasan-aturan-dan-validasi-penting)
12. [Menjalankan Sistem untuk Pertama Kali](#12-menjalankan-sistem-untuk-pertama-kali)
13. [Catatan Teknis dan Batasan Implementasi](#13-catatan-teknis-dan-batasan-implementasi)

---

## 1. Gambaran Umum

KREASI menggabungkan tiga kebutuhan utama:

- **Rekam jejak mahasiswa:** mencatat prestasi, kompetensi, portofolio, poin MEXS, dan informasi yang dipakai pada pratinjau SKPI.
- **Kolaborasi proyek:** membantu mahasiswa menemukan atau mengusulkan proyek, mendaftar ke proyek yang dibuka, membentuk kelompok, dan mengirim dokumentasi pekerjaan.
- **Pemantauan akademik:** membantu dosen mengelola proyek, memeriksa dokumentasi, memberi bimbingan dan nilai, serta membantu administrator mengelola akun, memvalidasi prestasi, mengatur data master, dan memfinalisasi SKPI.

Situs mempertahankan antarmuka HTML, CSS, dan JavaScript yang sudah ada. Django menangani login berbasis sesi, penyimpanan state aplikasi, pemeriksaan akses pada backend, dan penyimpanan berkas di server.

### Menu berdasarkan peran

| Peran | Menu utama | Kegunaan utama |
|---|---|---|
| Pengunjung | Beranda, Layanan, Kontak, Hubungi Admin, Sign In/Get Started | Mengenal sistem dan membuka halaman login. |
| Mahasiswa | Dashboard, Profil & Talenta, Rekam Jejak Prestasi, SKPI, Bursa Proyek, Proyek Saya | Mengelola profil, mengajukan prestasi, bergabung/mengusulkan proyek, dan memantau dokumen. |
| Dosen | Dashboard Dosen, Profil Dosen, Talent Pool, Manajemen Proyek | Menemukan talenta, meninjau usulan, membimbing proyek, memverifikasi dokumentasi, dan menilai proyek mata kuliah. |
| Administrator | Dashboard Admin, Validasi Prestasi, Manajemen Akun, Pengumuman Akademik, Kategori & Poin, Rekapitulasi & SKPI | Mengelola akun, master data, validasi prestasi, informasi akademik, dan finalisasi SKPI. |

## 2. Peran Pengguna

### 2.1 Mahasiswa

Mahasiswa menggunakan KREASI untuk:

- melihat ringkasan proyek, prestasi, poin MEXS, dan undangan;
- memperbarui bagian profil yang memang boleh diedit;
- mencatat keahlian dan karya/portofolio;
- mengajukan prestasi beserta bukti;
- mencari proyek, mendaftarkan diri, atau membuat usulan proyek;
- mengelola dokumentasi dan usulan anggota pada proyek yang diikuti;
- melihat pratinjau SKPI dan status finalisasinya.

### 2.2 Dosen

Dosen menggunakan KREASI untuk:

- melihat ringkasan aktivitas dan pemberitahuan;
- melihat profil serta melaporkan data yang keliru kepada administrator;
- mencari mahasiswa melalui Talent Pool berdasarkan data profil, keahlian, IPK, MEXS, dan portofolio;
- mengundang mahasiswa untuk berkolaborasi;
- meninjau usulan proyek mahasiswa;
- mengelola proyek yang menjadi tanggung jawabnya;
- membuat tahapan dokumentasi, memberi catatan bimbingan, memverifikasi berkas, dan meminta revisi;
- menetapkan nilai pada proyek mata kuliah setelah persyaratan penyelesaian dokumentasi terpenuhi.

### 2.3 Administrator

Administrator bertanggung jawab terhadap data dan tata kelola sistem. Fitur utamanya:

- membuat, mengubah, mengaktifkan/nonaktifkan, menghapus akun mahasiswa/dosen, dan mengatur ulang kata sandi;
- memasukkan data akademik yang digunakan untuk membatasi pilihan kelas, angkatan, dan mata kuliah;
- memvalidasi pengajuan prestasi beserta bukti;
- menerbitkan, mengubah, dan menghapus pengumuman akademik;
- mengelola kategori proyek, mata kuliah, kategori prestasi, bobot poin MEXS, dan ambang MEXS;
- melihat rekapitulasi poin dan memfinalisasi, membatalkan finalisasi, serta mencetak SKPI.

Akun administrator awal dibuat melalui perintah Django, bukan melalui formulir tambah akun di antarmuka. Formulir **Tambah Akun** pada antarmuka Admin menyediakan pilihan Mahasiswa dan Dosen.

## 3. Cara Membuka dan Masuk ke Sistem

### 3.1 Membuka halaman utama

1. Jalankan aplikasi Django (lihat [Menjalankan Sistem untuk Pertama Kali](#12-menjalankan-sistem-untuk-pertama-kali)).
2. Buka `http://127.0.0.1:8000/` di browser.
3. Halaman utama menampilkan pengenalan KREASI dan navigasi Beranda, Layanan, serta Kontak.
4. Tekan **Sign In** atau **Get Started** untuk menuju halaman login.
5. Tombol **Hubungi Admin** membuka informasi agar pengunjung mengetahui jalur menghubungi administrator.

Angka statistik pemasaran pada halaman utama (`500+` mahasiswa, `100+` prestasi, dan `50+` proyek) ditulis langsung pada frontend. Angka tersebut **bukan** penghitung data langsung dari basis data.

### 3.2 Login

1. Pilih peran yang sesuai: **Mahasiswa**, **Dosen**, atau **Admin**.
2. Masukkan username dan kata sandi.
3. Tekan tombol masuk.
4. Backend Django memeriksa username, kata sandi, status akun, dan kecocokan peran. Jika berhasil, sistem membuat sesi login dan membuka portal sesuai peran.
5. Jika akun tidak cocok, sistem menampilkan pesan umum **“Akun tidak terdaftar di sistem”**.

Username biasanya berupa NIM untuk mahasiswa dan NIP untuk dosen, sesuai data yang dibuat administrator. Login tidak membuat akun secara otomatis; akun harus dibuat dan diaktifkan terlebih dahulu.

### 3.3 Keluar dari sistem

Gunakan tombol **Logout** pada bagian bawah navigasi portal. Sistem mengirim permintaan logout ke Django untuk mengakhiri sesi server, kemudian kembali ke halaman utama.

## 4. Fitur Umum

### 4.1 Dashboard

Setiap peran mempunyai dashboard yang berbeda. Dashboard menampilkan ringkasan yang relevan untuk peran tersebut, misalnya jumlah akun dan tugas administrasi untuk Admin, poin serta status proyek bagi Mahasiswa, dan ringkasan pekerjaan bagi Dosen.

### 4.2 Navigasi portal

Menu utama berada pada panel samping. Pada layar kecil, tombol navigasi dapat membuka atau menutup panel tersebut. Pilih nama menu untuk berpindah halaman.

### 4.3 Pencarian data

Bagian daftar yang menyediakan kolom pencarian menggunakan kata kunci untuk menyaring baris atau kartu yang tampil. Contohnya daftar akun, Talent Pool, proyek, prestasi, atau data SKPI. Kolom pencarian hanya menyaring data yang tersedia pada halaman tersebut; kolom ini tidak membuat data baru.

### 4.4 Modal, pesan, dan konfirmasi

- **Modal** digunakan untuk formulir atau detail, misalnya detail prestasi, detail proyek, pengaturan akun, atau verifikasi dokumen.
- **Pesan notifikasi singkat** (toast) memberi tahu apakah tindakan berhasil, ditolak, atau membutuhkan perbaikan.
- **Dialog konfirmasi** digunakan untuk tindakan penting seperti menghapus proyek, kelompok, atau data.

Bacalah pesan validasi yang muncul. Pesan tersebut menjelaskan bagian yang perlu diperbaiki, misalnya kolom wajib kosong, pilihan anggota tidak sesuai, atau kapasitas kelompok sudah penuh.

### 4.5 Notifikasi

Ikon/notifikasi pada portal memberi ringkasan aktivitas terbaru. Daftar notifikasi dapat dibuka dan item tertentu dapat diarahkan ke halaman yang berkaitan. Isi notifikasi bergantung pada aktivitas, peran penerima, dan data yang tersedia.

### 4.6 Panduan

Tombol **Panduan** pada navigasi membuka penjelasan penggunaan dalam antarmuka. Dokumen `Feature.MD` ini menjadi panduan tambahan yang menjelaskan fitur dan alur lebih menyeluruh.

---

## 5. Fitur Mahasiswa

### 5.1 Dashboard Mahasiswa

Dashboard menampilkan ringkasan seperti:

- total poin MEXS;
- jumlah proyek aktif/yang dapat dipantau;
- jumlah prestasi yang disetujui;
- jumlah prestasi yang menunggu validasi;
- jumlah undangan kolaborasi yang menunggu respons;
- progres dokumentasi proyek yang diikuti.

**Cara menggunakan:** buka menu Dashboard. Pilih kartu proyek atau tautan **Lihat semua** untuk membuka detail/daftar proyek terkait. Buka bagian Undangan Kolaborasi untuk membaca dan merespons undangan.

### 5.2 Profil & Talenta

Halaman ini memuat identitas akademik, biodata singkat, keahlian, dan portofolio.

**Data resmi yang tidak dapat diubah mahasiswa melalui formulir profil:**

- nama lengkap dan NIM;
- program studi dan data akademik resmi;
- fakultas, angkatan, semester, dan IPK;
- surel akademik yang ditetapkan sistem.

Perubahan data resmi perlu dilakukan administrator. Pada formulir profil, mahasiswa dapat mengubah data kontak/biodata yang disediakan seperti telepon dan deskripsi “Tentang Saya”.

#### Menambah atau menghapus keahlian

1. Buka **Profil & Talenta**.
2. Masukkan satu keahlian pada kolom **Tambahkan keahlian baru**.
3. Tekan **Tambah**.
4. Untuk menghapus, tekan ikon silang di sebelah keahlian terkait.

Validasi yang terlihat pada frontend membatasi keahlian maksimal 60 karakter, maksimal 20 keahlian, serta mencegah keahlian duplikat tanpa membedakan huruf besar/kecil. Perubahan keahlian juga memperbarui data pada Talent Pool.

#### Menambah portofolio

1. Pada bagian **Portofolio**, tekan **Tambah**.
2. Isi informasi karya yang diminta, seperti judul, kategori, deskripsi, tautan (jika ada), dan berkas pendukung (jika diperlukan).
3. Simpan portofolio.
4. Untuk melihat kembali berkas yang memang sudah tersimpan, gunakan **Lihat Berkas** atau **Unduh**. Gunakan tombol hapus bila karya ingin dihilangkan dari portofolio.

Portofolio yang terhubung ke data talenta dapat dilihat oleh Dosen melalui Talent Pool sesuai data dan akses sistem.

### 5.3 Rekam Jejak Prestasi

Halaman ini dipakai untuk mengajukan dan melacak prestasi mahasiswa.

#### Mengajukan prestasi baru

1. Buka **Rekam Jejak Prestasi**.
2. Isi judul prestasi/kegiatan, kategori, penyelenggara, dan tanggal kegiatan.
3. Unggah dokumen bukti asli.
4. Isi catatan tambahan bila diperlukan.
5. Tekan **Kirim Pengajuan**.
6. Periksa pengajuan yang muncul pada tabel **Riwayat Pengajuan Prestasi**.

Kategori dan bobot poin berasal dari data master yang dikelola Admin. Formulir menghitung poin berdasarkan kategori yang dipilih; mahasiswa tidak menentukan bobot poin secara bebas.

#### Memantau hasil validasi

Status pengajuan dapat berupa **Menunggu Validasi**, **Disetujui**, atau **Ditolak**. Buka **Detail** untuk melihat data, bukti yang tercatat, catatan validator, dan informasi validasi bila telah diputuskan.

Pengajuan berstatus **Menunggu Validasi** dapat dibatalkan oleh mahasiswa melalui detail pengajuan. Keputusan validasi dilakukan oleh Admin.

**Penting:** ketika SKPI mahasiswa sudah difinalisasi oleh Admin, formulir pengajuan prestasi baru dikunci sampai status finalisasi dibatalkan oleh Admin.

### 5.4 Bursa Proyek

Bursa Proyek membantu mahasiswa melihat proyek yang dapat diakses, membaca detail proyek, dan mengajukan diri pada proyek umum yang membuka pendaftaran.

Fitur yang tersedia pada daftar/detail proyek mencakup:

- filter jenis proyek: **Semua**, **Proyek Mata Kuliah**, **Informatika untuk Masyarakat**, dan **Proyek Umum**;
- informasi judul, kategori, periode, deskripsi, persyaratan anggota, dan lampiran jika ada;
- daftar kelompok/anggota pada proyek berkelompok;
- informasi pendaftaran tertutup atau kapasitas penuh;
- formulir pendaftaran anggota untuk proyek yang menerima pendaftar.

Tidak semua proyek terlihat oleh semua mahasiswa. Proyek Mata Kuliah dibatasi berdasarkan mata kuliah, angkatan, kelas, pembuat, atau keanggotaan. Proyek Informatika untuk Masyarakat juga mempunyai aturan keterkaitan khusus. Proyek umum mengikuti kategori yang dipublikasikan dan status/kuota pendaftarannya.

#### Mendaftar ke proyek umum

1. Buka **Bursa Proyek** dan cari proyek yang sesuai.
2. Buka detail dan baca persyaratan anggota.
3. Pilih **Daftar ke Proyek Ini** jika pendaftaran masih dibuka dan Anda memenuhi syarat.
4. Isi keahlian yang relevan, posisi yang dilamar, serta motivasi/kontribusi.
5. Tekan **Kirim Pendaftaran**.
6. Pantau hasilnya melalui status pendaftaran, notifikasi, atau daftar proyek yang terkait.

Sistem pada frontend mencegah mahasiswa mendaftar lebih dari sekali ke proyek yang sama. Penerimaan pelamar dilakukan Dosen yang bertanggung jawab atas proyek. Pada proyek berkelompok, Dosen menempatkan pelamar yang diterima ke kelompok yang masih memiliki kapasitas.

### 5.5 Mengusulkan Proyek/Kegiatan Baru

Mahasiswa dapat mengusulkan proyek dengan formulir pembuatan proyek. Kategori yang dapat dipilih dipengaruhi data master dan aturan mata kuliah/peran.

Alur umum:

1. Buka area pembuatan proyek dari portal mahasiswa.
2. Isi nama, kategori, periode, deskripsi, persyaratan anggota, dan informasi lain sesuai kategori.
3. Jika kategori **Proyek Mata Kuliah**, pilih mata kuliah yang diambil, dosen pengampu, satu angkatan, dan satu atau beberapa kelas yang sesuai cakupan dosen.
4. Tentukan apakah proyek dikerjakan individu atau berkelompok bila opsi tersebut tersedia.
5. Jika berkelompok, tentukan jumlah kelompok dan kapasitas anggota per kelompok, lalu pilih anggota yang memenuhi syarat menggunakan filter pencarian, angkatan, dan kelas.
6. Periksa kembali kapasitas kelompok serta data yang diisi, lalu kirim usulan.
7. Usulan yang menunggu keputusan dapat dibuka kembali untuk diedit atau dibatalkan oleh pembuatnya selama belum diproses dosen.

Usulan mahasiswa memiliki status menunggu persetujuan. Dosen yang berwenang dapat menerima/mengaktifkan atau menolak usulan. Setelah disetujui, proyek akan mengikuti aturan visibilitas dan pengelolaan yang sesuai kategorinya.

### 5.6 Proyek Saya

Halaman **Proyek Saya** menampilkan proyek/usulan yang berkaitan dengan mahasiswa. Pada ruang kerja proyek, mahasiswa dapat melakukan tindakan sesuai status dan keanggotaan, antara lain:

- membaca informasi proyek serta status usulan/keanggotaan;
- melihat progres dan status setiap tahapan dokumentasi;
- mengunggah atau mengirim ulang berkas tahapan yang diminta Dosen;
- membaca catatan verifikasi dan catatan bimbingan;
- mengusulkan anggota tambahan pada kelompok jika aturan proyek mengizinkan;
- memilih atau berpindah ke kelompok yang memang terkait dengannya jika opsi itu tersedia;
- melihat status nilai pada proyek mata kuliah setelah penilaian diaktifkan.

Tindakan yang tersedia bergantung pada kategori proyek, apakah mahasiswa sudah menjadi anggota, apakah keanggotaan telah disetujui, apakah kapasitas kelompok terpenuhi, dan apakah proyek sedang dibuka untuk perubahan.

### 5.7 SKPI Mahasiswa

Halaman SKPI menampilkan **pratinjau** Surat Keterangan Pendamping Ijazah berdasarkan data mahasiswa dan prestasi yang sudah disetujui.

Yang ditampilkan antara lain identitas akademik, IPK, daftar prestasi tervalidasi, total poin MEXS, dan predikat MEXS. Kode saat ini memilih maksimal 10 prestasi tervalidasi dengan poin tertinggi untuk dimasukkan ke pratinjau.

Pratinjau ini bukan finalisasi resmi. Finalisasi dan pencetakan SKPI resmi dilakukan oleh Administrator. Mahasiswa dapat melihat apakah SKPI masih menunggu finalisasi atau sudah difinalisasi, termasuk catatan finalisasi jika tersedia.

### 5.8 Undangan Kolaborasi

Saat mendapat undangan, mahasiswa dapat:

1. membuka **Undangan Kolaborasi** dari Dashboard;
2. membaca pengirim, peran yang ditawarkan, tanggal, proyek, dan pesan;
3. memilih **Terima** atau **Tolak**.

Jika proyek memiliki kuota total dan kuotanya sudah penuh, sistem menolak penerimaan undangan sampai kapasitas dapat ditangani. Pada proyek individu/nonkelompok, menerima undangan menambahkan mahasiswa sebagai anggota. Proyek berkelompok tetap mengikuti pengaturan kelompok proyek; menerima undangan tidak dengan sendirinya menggantikan semua aturan pengelompokan.

---

## 6. Fitur Dosen

### 6.1 Dashboard Dosen

Dashboard menjadi ringkasan untuk membuka pekerjaan yang perlu ditangani, termasuk usulan proyek yang menunggu tinjauan dan aktivitas/notifikasi terbaru. Gunakan pintasan atau menu **Manajemen Proyek** untuk melanjutkan pekerjaan.

### 6.2 Profil Dosen

Halaman ini menampilkan data dosen, misalnya nama, NIP/NIDN bila tersedia, program studi, jabatan, surel, bidang keahlian, mata kuliah yang diampu beserta cakupan angkatan/kelas, riwayat pendidikan, dan publikasi ilmiah.

Data tersebut ditampilkan untuk diperiksa; jika ada kesalahan, pilih **Laporkan Kesalahan Data**, pilih bagian yang salah, jelaskan perbaikannya, lalu kirim laporan. Perubahan data resmi dilakukan Admin, bukan langsung melalui halaman profil dosen.

### 6.3 Talent Pool

Talent Pool adalah katalog untuk membantu Dosen menemukan mahasiswa yang sesuai untuk proyek atau kegiatan.

Kartu talenta dapat memperlihatkan:

- nama, NIM, program studi, angkatan, dan kelas;
- IPK dan poin MEXS;
- keahlian;
- jumlah/kumpulan portofolio;
- detail profil, karya, dan keterlibatan proyek.

**Cara mencari mahasiswa:** gunakan pencarian, pilih **Lihat Profil** untuk membuka detail, kemudian pilih **Undang** bila ingin mengirim undangan kolaborasi untuk proyek tertentu. Data keahlian yang ditambahkan mahasiswa pada Profil & Talenta disinkronkan ke katalog ini oleh alur frontend.

### 6.4 Manajemen Proyek

Area ini merupakan tempat Dosen melihat proyek, meninjau usulan, membuka dokumentasi, mengelola kelompok, dan melakukan evaluasi.

#### Meninjau usulan proyek

1. Buka **Manajemen Proyek** dan temukan usulan berstatus menunggu keputusan.
2. Buka detail usulan untuk memeriksa judul, kategori, pembuat, deskripsi, periode, persyaratan, serta lampiran.
3. Terima/aktifkan usulan dengan opsi tinjauan, atau tolak jika tidak sesuai.
4. Usulan Proyek Mata Kuliah diarahkan kepada dosen pengampu/pembimbing yang ditentukan; usulan proyek umum tanpa pemilik dapat ditinjau oleh dosen sesuai logika sistem.

#### Membuat proyek

Dosen dapat membuat proyek melalui formulir yang sama, dengan isian dan aturan yang menyesuaikan kategori. Untuk **Proyek Mata Kuliah**, Dosen menentukan mata kuliah, satu angkatan, beberapa kelas, dan apakah tugas individu atau berkelompok. Untuk **Informatika untuk Masyarakat**, kategori tersedia bagi dosen yang tercatat mengampu mata kuliah terkait; dosen pembuat menjadi pembimbing pada alur ini.

Pada proyek umum, Dosen mengatur jumlah anggota yang dibutuhkan. Dosen juga dapat membuka atau menutup pendaftaran proyek umum yang dikelolanya. Pendaftaran tidak dapat dibuka lagi jika kuota sudah penuh tanpa terlebih dahulu menangani kapasitas proyek.

#### Memproses pendaftar

Untuk proyek yang memiliki formulir pendaftaran:

1. lihat daftar pelamar;
2. buka profil pelamar untuk memeriksa keahlian, motivasi, serta portofolio;
3. terima atau tolak pelamar;
4. jika diterima, sistem memasukkan mahasiswa sebagai anggota atau menempatkannya pada kelompok yang masih memiliki tempat, sesuai jenis proyek.

Dosen tidak dapat memproses pelamar pada proyek yang tidak menjadi tanggung jawabnya. Sistem juga memeriksa kapasitas sebelum menerima anggota baru.

#### Mengelola anggota dan kelompok

Pada proyek yang mendukung pengelolaan kelompok, Dosen dapat:

- menambah kelompok;
- menambah/mengeluarkan anggota;
- memeriksa usulan anggota dari mahasiswa;
- menyetujui atau menolak usulan anggota;
- melihat identitas, peran, dan status persetujuan anggota.

Pilihan anggota dapat dibatasi oleh mata kuliah, angkatan, kelas, keaktifan akun, dan aturan khusus proyek. Anggota yang diusulkan mahasiswa dapat berstatus menunggu persetujuan.

### 6.5 Dokumentasi Proyek dan Bimbingan

Dokumentasi proyek ada di dalam **Manajemen Proyek**, bukan sebagai daftar tahap otomatis terpisah.

#### Membuat tahapan dokumentasi

1. Buka proyek yang menjadi tanggung jawab Dosen.
2. Buka bagian **Verifikasi Tahapan Dokumentasi**.
3. Tekan **Tambah Tahap**.
4. Masukkan nama tahap dan deskripsi/instruksi yang diperlukan.
5. Simpan tahap.

**Tahapan tidak otomatis terdiri dari tujuh item wajib.** Dosen menentukan dan menambahkan tahapan sesuai kebutuhan proyek. Jika tahap ditambahkan pada proyek berkelompok secara umum, sistem dapat menambahkannya ke semua kelompok; Dosen juga dapat mengatur tahap untuk kelompok tertentu ketika membuka ruang kelompok.

#### Memeriksa dokumen mahasiswa

Tahap dapat menunjukkan status seperti **Belum Dimulai**, **Menunggu Verifikasi**, **Disetujui**, atau **Revisi**. Ketika mahasiswa mengirim berkas:

1. Dosen membuka tahap yang menunggu verifikasi.
2. Dosen membaca/meninjau berkas asli jika sudah tersimpan.
3. Dosen memilih keputusan persetujuan atau meminta revisi.
4. Dosen dapat memberikan catatan agar mahasiswa memahami bagian yang harus diperbaiki.
5. Mahasiswa memperbarui/mengirim ulang dokumen, kemudian menunggu verifikasi berikutnya.

Riwayat tahap menyimpan informasi pengiriman dan catatan verifikasi sesuai data yang tersedia.

#### Catatan bimbingan

Dosen dapat menambahkan catatan bimbingan/log aktivitas pada proyek atau kelompok. Catatan ini membantu mencatat arahan, progres, dan aktivitas yang dibahas.

### 6.6 Menandai Proyek Selesai dan Memberi Nilai

Untuk proyek mata kuliah, penilaian mengikuti pengaturan mode nilai yang tersedia: kelompok saja, individu saja, atau kelompok dan individu.

Alur nilai:

1. Dosen memeriksa dan menyetujui seluruh tahapan dokumentasi pada target proyek/kelompok.
2. Dosen memilih **Tandai Seluruh Tahapan Selesai**.
3. Setelah penanda penyelesaian aktif, formulir penilaian dapat digunakan.
4. Masukkan nilai antara 0 hingga 100 dan simpan.
5. Sistem menampilkan nilai angka dan huruf sesuai rentang nilai yang diterapkan dalam kode.

Untuk kelompok tanpa anggota yang disetujui, sistem tidak mengizinkan pemberian nilai kelompok. Jika dokumentasi belum lengkap, penilaian tetap terkunci.

### 6.7 Penghapusan Proyek

Tombol penghapusan tersedia hanya jika Dosen memang memiliki hak menghapus proyek tersebut. Penghapusan meminta konfirmasi dan dapat menghapus data proyek beserta kelompok, pelamar, dan dokumentasi yang terkait pada state aplikasi. Periksa proyek yang dipilih sebelum menyetujui tindakan karena tindakan ini tidak ditujukan sebagai pembatalan sementara.

---

## 7. Fitur Administrator

### 7.1 Dashboard Admin

Dashboard Admin menampilkan ringkasan akun mahasiswa, akun dosen, prestasi yang menunggu validasi, pengumuman akademik, dan tautan cepat menuju validasi prestasi, manajemen akun, serta SKPI. Bagian aktivitas terbaru membantu membuka notifikasi terkait.

### 7.2 Manajemen Akun

Pada **Manajemen Akun**, Admin dapat memfilter daftar berdasarkan peran dan melakukan tindakan untuk akun mahasiswa/dosen.

#### Membuat akun

1. Pilih **Tambah Akun**.
2. Pilih peran Mahasiswa atau Dosen.
3. Isi nama, username/nomor induk, kata sandi awal, program studi, surel, dan field tambahan yang tersedia.
4. Untuk Mahasiswa, lengkapi data yang mendukung penyaringan proyek seperti NIM, angkatan, kelas, dan mata kuliah yang diambil.
5. Untuk Dosen, lengkapi NIP/NIDN bila diminta, mata kuliah yang diampu, serta cakupan angkatan dan kelas.
6. Simpan akun.

Data akun menjadi dasar pemilihan anggota proyek. Karena itu, NIM/NIP, angkatan, kelas, dan mata kuliah harus benar. Akun baru sebaiknya diperiksa kembali sebelum digunakan.

#### Mengelola akun yang sudah ada

Pada setiap akun, Admin dapat menggunakan tindakan yang tersedia untuk:

- mengubah data akun;
- mengatur ulang kata sandi;
- mengaktifkan atau menonaktifkan akun;
- menghapus akun non-administrator sesuai pilihan yang ditampilkan.

Akun nonaktif tidak seharusnya digunakan untuk login. Akun mahasiswa/dosen yang tidak aktif juga tidak muncul sebagai kandidat aktif pada sejumlah formulir proyek.

### 7.3 Validasi Prestasi

Halaman **Validasi Prestasi** membagi data menjadi pengajuan yang menunggu keputusan dan riwayat pengajuan yang sudah diproses.

1. Pilih prestasi pada bagian **Menunggu Validasi**.
2. Periksa nama mahasiswa, judul prestasi, kategori, penyelenggara, tanggal kegiatan, poin, dokumen bukti, dan catatan mahasiswa bila ada.
3. Buka bukti asli untuk pratinjau/unduhan jika file tersimpan.
4. Pilih **Setujui** atau **Tolak**.
5. Isi catatan validator bila diperlukan, lalu simpan keputusan.

Keputusan dicatat beserta nama validator dan tanggal. Prestasi yang disetujui dihitung ke total poin MEXS. Prestasi yang ditolak tetap menjadi bagian riwayat sehingga keputusan dapat ditelusuri.

### 7.4 Pengumuman Akademik

Di menu **Pengumuman Akademik**, Admin dapat menambah, mengubah, dan menghapus pengumuman. Periksa judul, isi, serta informasi yang diminta pada formulir sebelum menyimpan. Pengumuman yang tersedia menjadi bagian informasi/aktivitas yang ditampilkan oleh sistem sesuai implementasi frontend.

### 7.5 Data Master: Kategori, Mata Kuliah, dan Poin MEXS

Menu **Kategori & Poin** mempunyai beberapa tab.

#### Kategori Proyek

Admin dapat menambah, mengubah, atau menghapus kategori yang dapat dipakai pada formulir proyek dan filter Bursa Proyek. Kategori khusus yang terhubung dengan aturan sistem—**Proyek Mata Kuliah** dan **Informatika untuk Masyarakat**—dilindungi dari perubahan nama atau penghapusan melalui form master karena perubahan tersebut dapat mengganggu aturan khusus proyek.

#### Mata Kuliah

Admin dapat menambah, mengubah, dan menghapus nama mata kuliah. Data ini menjadi pilihan bagi akun mahasiswa, akun dosen, dan formulir proyek mata kuliah. Perubahan data master sebaiknya diikuti pemeriksaan ulang data mata kuliah pada akun terkait.

#### Kategori Prestasi & Poin

Admin mengelola nama kategori prestasi dan bobot poin MEXS. Mahasiswa memilih kategori yang telah disediakan saat mengajukan prestasi, sedangkan poin mengikuti bobot kategori yang dipilih. Bobot yang diubah akan memengaruhi perhitungan prestasi sesuai cara data poin disimpan/ditampilkan oleh aplikasi.

#### Ambang Poin MEXS

Admin menetapkan nilai ambang poin MEXS. Halaman rekapitulasi menggunakan angka ini untuk menilai apakah jumlah poin mahasiswa sudah mencapai ambang. Nilai default pada state awal adalah 1000 poin, dan Admin dapat mengubahnya melalui tab ambang batas.

### 7.6 Rekapitulasi & SKPI

Halaman ini menampilkan daftar mahasiswa, program studi, IPK, total poin MEXS, progres menuju ambang, dan status finalisasi SKPI.

Untuk mahasiswa yang belum difinalisasi:

1. pilih **Finalisasi SKPI**;
2. periksa informasi/isi yang ditampilkan pada dialog finalisasi;
3. simpan finalisasi.

Untuk SKPI yang sudah final, Admin dapat membuka **Detail**, **Cetak SKPI**, atau **Batalkan Finalisasi**. Setelah finalisasi dibatalkan, status kembali belum final dan mahasiswa dapat mengajukan prestasi lagi mengikuti aturan aplikasi.

Pencetakan SKPI resmi hanya tersedia untuk Admin dan hanya setelah status finalisasi tercatat. Pratinjau mahasiswa tidak menggantikan finalisasi resmi ini.

---

## 8. Alur Lengkap Proyek

Bagian ini menjelaskan perbedaan alur berdasarkan kategori, agar pengaturan kuota dan kelompok lebih mudah dipahami.

### 8.1 Kategori proyek

Kategori default yang didefinisikan dalam kode meliputi:

- Proyek Mata Kuliah
- Informatika untuk Masyarakat
- Kompetisi
- Magang
- Wirausaha
- Organisasi & Kepemimpinan
- Minat & Bakat
- Internasionalisasi & Summit
- Rekognisi
- Penelitian & Hibah

Daftar aktual berasal dari data master, sehingga Admin dapat menambah/mengelola kategori umum. Dua kategori khusus yang memiliki aturan tersendiri adalah **Proyek Mata Kuliah** dan **Informatika untuk Masyarakat**.

| Jenis | Sifat utama | Pengaturan/akses khusus |
|---|---|---|
| Proyek Mata Kuliah | Proyek terkait mata kuliah dan cakupan kelas. Tidak menggunakan kuota pendaftaran umum seperti proyek marketplace. | Harus memakai mata kuliah yang sesuai. Memakai satu angkatan dan satu atau beberapa kelas yang sesuai cakupan dosen. Dapat berkelompok atau individu. Akses mahasiswa dibatasi oleh mata kuliah, angkatan/kelas, pembuat atau keanggotaan. |
| Informatika untuk Masyarakat | Kegiatan khusus mata kuliah terkait; tidak dipublikasikan sebagai proyek umum dengan kuota anggota tetap. | Mahasiswa harus tercatat mengambil mata kuliah terkait; dosen harus tercatat mengampunya untuk membuat kategori tersebut. Jumlah anggota total tidak diwajibkan seperti proyek umum; kapasitas per kelompok tetap berlaku jika berkelompok. |
| Proyek Umum | Proyek pada kategori lain, misalnya Kompetisi, Magang, Wirausaha, dan kategori umum lainnya. | Jumlah anggota yang dibutuhkan menjadi kuota total pendaftar. Pendaftaran dapat dibuka/ditutup oleh Dosen yang mengelola proyek. |

Ketersediaan kategori dalam formulir dipengaruhi peran dan data akun. Sebagai contoh, kategori Informatika untuk Masyarakat tidak ditawarkan jika mata kuliah tersebut tidak tercatat pada akun mahasiswa/dosen terkait.

### 8.2 Kapasitas proyek berkelompok

Pada proyek berkelompok terdapat dua nilai berbeda:

- **Jumlah anggota yang dibutuhkan:** kuota total proyek umum.
- **Anggota per kelompok:** batas maksimal anggota pada satu kelompok.

Untuk proyek umum, jumlah kapasitas seluruh kelompok harus cukup untuk kuota total yang ditetapkan. Sistem memeriksa bahwa satu mahasiswa tidak terpilih pada lebih dari satu kelompok dalam formulir yang sama dan jumlah anggota setiap kelompok tidak melebihi kapasitas.

**Contoh:** sebuah proyek umum membutuhkan 4 anggota, berkelompok, dengan kapasitas 3 orang per kelompok. Satu kelompok hanya dapat menampung 3 orang sehingga kapasitasnya kurang dari kuota total 4. Sistem meminta penambahan kelompok atau penyesuaian jumlah anggota per kelompok sebelum proyek disimpan.

Jika jumlah kelompok adalah 2 dan setiap kelompok maksimal 3 orang, kapasitas totalnya 6 orang. Kuota total 4 orang menjadi mungkin, tetapi setiap kelompok tetap tidak boleh berisi lebih dari 3 orang.

Untuk Proyek Mata Kuliah dan Informatika untuk Masyarakat, kuota total pendaftaran umum tidak digunakan dengan cara yang sama. Pada dua kategori ini, aturan utama jumlah anggota adalah kapasitas kelompok dan cakupan mahasiswa.

### 8.3 Aturan anggota

- Kandidat harus berasal dari akun mahasiswa aktif yang dikelola Admin.
- Filter angkatan, kelas, dan pencarian membantu menemukan anggota.
- Pada Proyek Mata Kuliah, anggota harus sesuai mata kuliah serta angkatan/kelas yang dipilih.
- Pada Informatika untuk Masyarakat, kandidat harus memenuhi syarat mata kuliah terkait.
- Pada proyek umum, kandidat tetap harus lolos aturan proyek dan kuota.
- Usulan penambahan anggota dapat menunggu persetujuan Dosen.
- Seorang mahasiswa tidak boleh mengirim pendaftaran lebih dari sekali ke proyek yang sama.

### 8.4 Siklus status proyek

Siklus status bergantung pada kategori dan pembuatnya. Secara umum alurnya:

1. **Pembuatan/usulan:** pembuat mengisi data proyek dan mengirimnya.
2. **Ditinjau:** usulan mahasiswa menunggu persetujuan Dosen yang relevan.
3. **Aktif/dibuka:** proyek dapat dijalankan dan, untuk proyek umum, pendaftaran dapat dibuka.
4. **Pengelolaan anggota:** Dosen memproses pelamar dan mengelola kelompok sesuai kapasitas.
5. **Dokumentasi:** Dosen membuat tahapan; mahasiswa mengunggah berkas dan menerima umpan balik.
6. **Penyelesaian:** Dosen menyetujui seluruh dokumentasi dan menandai proyek/kelompok selesai.
7. **Penilaian:** untuk proyek mata kuliah, nilai diberikan setelah persyaratan dokumentasi selesai dan mode penilaian sesuai.

Tidak setiap proyek melewati seluruh langkah dengan cara identik. Contohnya, proyek umum mungkin memakai pendaftaran anggota, sedangkan proyek mata kuliah mempunyai batas kelas dan mata kuliah.

---

## 9. Alur Prestasi, Poin MEXS, dan SKPI

1. Admin menyiapkan kategori prestasi dan bobot poin melalui **Kategori & Poin**.
2. Mahasiswa mengajukan prestasi dengan data kegiatan dan dokumen bukti.
3. Status pengajuan menjadi **Menunggu Validasi**.
4. Admin meninjau bukti, kemudian menyetujui atau menolak pengajuan dengan catatan.
5. Prestasi yang disetujui masuk perhitungan poin MEXS; data poin juga terlihat pada halaman talenta dan ringkasan terkait.
6. Halaman SKPI mahasiswa menyusun pratinjau dari prestasi tervalidasi, dengan batas maksimal 10 prestasi berpoin tertinggi.
7. Admin melihat rekap poin terhadap ambang MEXS, memfinalisasi SKPI, dan dapat mencetak dokumen.
8. Saat SKPI berstatus final, mahasiswa tidak dapat mengirim prestasi baru melalui formulir. Admin perlu membatalkan finalisasi untuk membuka kembali pengajuan.

### Perbedaan status

- **Menunggu Validasi:** belum dihitung sebagai prestasi yang telah disetujui.
- **Disetujui:** dapat berkontribusi pada poin MEXS dan daftar pratinjau SKPI.
- **Ditolak:** tercatat pada riwayat, tetapi tidak menjadi prestasi disetujui.
- **SKPI Final:** finalisasi administratif telah dilakukan dan pencetakan resmi dapat dilakukan Admin.

Ambang MEXS adalah indikator capaian poin. Status **SKPI Final** adalah status finalisasi dokumen oleh Admin; keduanya bukan hal yang sama.

---

## 10. Unggah dan Pengelolaan Dokumen

Dokumen bisa dipakai pada portofolio, bukti prestasi, lampiran proyek, dan tahapan dokumentasi proyek. File yang diunggah melalui backend disimpan di server dan memiliki metadata seperti nama file, jenis konten, ukuran, pemilik, dan konteks unggahan.

### Cara mengakses dokumen

- **Lihat/Buka Dokumen:** membuka pratinjau berkas jika pengguna memiliki izin.
- **Unduh:** tersedia pada komponen antarmuka yang menyediakan tindakan tersebut.
- **Hapus:** tersedia pada fitur tertentu untuk menghapus file terkait, apabila hak akses mengizinkan.

Akses dosen/admin dan akses mahasiswa diperiksa berdasarkan sesi dan hubungan terhadap berkas/proyek. Hak untuk melihat berkas tidak selalu berarti hak untuk menghapusnya.

### Format dan ukuran

Backend menerima beberapa format dokumen umum—termasuk PDF, gambar, dokumen Office, spreadsheet, presentasi, CSV, TXT, dan ZIP—dengan batas umum **10 MB per berkas**. Beberapa formulir frontend menerapkan batas atau format yang lebih ketat; misalnya formulir bukti prestasi dan lampiran proyek dapat menampilkan batas 5 MB dan tipe tertentu. Ikuti instruksi yang terlihat pada formulir yang sedang digunakan.

Jika data lama hanya memiliki nama/ukuran file tetapi tidak memiliki file fisik tersimpan, tombol pratinjau tidak dapat memulihkan konten yang tidak ada. Unggah ulang file asli untuk menyimpan berkas fisik yang dapat dibuka.

---

## 11. Ringkasan Aturan dan Validasi Penting

| Kondisi | Perilaku yang diterapkan pada antarmuka/kode |
|---|---|
| Username/kata sandi/peran tidak cocok | Login ditolak dengan pesan umum “Akun tidak terdaftar di sistem”. |
| Data identitas resmi mahasiswa perlu diubah | Mahasiswa menghubungi Admin; field identitas pada halaman profil tidak dapat diedit sendiri. |
| SKPI sudah difinalisasi | Formulir pengajuan prestasi baru dikunci sampai finalisasi dibatalkan Admin. |
| Prestasi tidak memiliki kategori master yang sah | Pengajuan tidak dapat diproses. |
| Mahasiswa melamar proyek yang sama lebih dari sekali | Pengajuan kedua ditolak oleh pemeriksaan frontend. |
| Kuota total proyek umum penuh | Pendaftaran/anggota baru tidak dapat diterima sampai kapasitas tersedia. |
| Kapasitas kelompok penuh | Penambahan anggota ditolak atau membutuhkan kelompok/kapasitas tambahan. |
| Mahasiswa di luar cakupan mata kuliah, angkatan, atau kelas | Mahasiswa tidak dapat dipilih sebagai anggota Proyek Mata Kuliah yang tidak sesuai. |
| Anggota diusulkan ke kelompok lain atau belum disetujui | Pengajuan anggota dibatasi oleh aturan keanggotaan kelompok. |
| Dokumen terlalu besar atau format tidak didukung | Backend menolak unggahan dan menampilkan pesan kesalahan. |
| Dosen belum menyetujui seluruh tahap dokumentasi | Proyek/kelompok belum dapat ditandai selesai dan penilaian tetap terkunci. |
| Nilai di luar rentang 0–100 | Penyimpanan nilai ditolak pada pemeriksaan frontend. |
| Pengguna mencoba membuka proyek/dokumen yang tidak berhak diakses | Pemeriksaan peran/relasi diterapkan di frontend dan/atau backend sesuai endpoint. |

Pesan yang muncul di layar sebaiknya dijadikan acuan untuk memperbaiki input. Untuk perubahan data resmi atau kondisi yang tidak dapat diselesaikan dari halaman pengguna, hubungi Admin Program Studi.

---

## 12. Menjalankan Sistem untuk Pertama Kali

Panduan lengkap ada di `README.md`. Ringkasan lokal untuk Windows:

1. Ekstrak arsip proyek.
2. Buka PowerShell pada folder `kreasi_django`.
3. Buat dan aktifkan virtual environment, lalu pasang dependensi.
4. Jalankan migrasi database.
5. Buat akun administrator awal.
6. Jalankan server.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py create_kreasi_admin --username admin --name "Administrator Program Studi"
python manage.py runserver
```

Perintah `create_kreasi_admin` meminta kata sandi melalui prompt terminal. Setelah server berjalan, kunjungi `http://127.0.0.1:8000/`, pilih peran **Admin**, lalu masuk menggunakan akun yang dibuat.

### Persiapan data awal yang disarankan

1. Login sebagai Admin.
2. Buat akun mahasiswa dan dosen.
3. Periksa data NIM/NIP, angkatan, kelas, mata kuliah yang diambil, mata kuliah yang diampu, dan cakupan kelas dosen.
4. Periksa kategori proyek dan daftar mata kuliah pada Data Master.
5. Tambahkan kategori prestasi beserta bobot poin sebelum mahasiswa mulai mengajukan prestasi.
6. Sesudah itu, lakukan uji coba alur login, pengajuan prestasi, tinjauan Dosen/Admin, pembuatan proyek, dokumentasi, dan SKPI.

State awal memang tidak berisi akun, proyek, atau prestasi demo. Kategori proyek, daftar mata kuliah, kelas awal, dan ambang MEXS memiliki nilai awal yang ditetapkan pada pembentuk state, tetapi daftar kategori prestasi dimulai kosong sehingga perlu disiapkan oleh Admin.

---

## 13. Catatan Teknis dan Batasan Implementasi

Bagian ini membantu membedakan fitur yang terlihat oleh pengguna dari cara data disimpan di backend.

1. **Autentikasi:** sesi login dikelola Django. Akun disimpan sebagai `PortalUser`; kata sandi diproses menggunakan mekanisme hash Django.
2. **Data fitur:** proyek, prestasi, portofolio, notifikasi, undangan, data master, dan finalisasi SKPI pada implementasi ini disimpan dalam satu agregat JSON (`AppState.data`). Jenis data tersebut belum masing-masing menjadi tabel database terpisah.
3. **File fisik:** dokumen disimpan menggunakan `UploadedDocument` dan storage `MEDIA_ROOT`; mencadangkan database saja belum tentu mencadangkan isi berkas.
4. **Penyaringan akses:** endpoint state memfilter data menurut peran dan identitas; endpoint dokumen memeriksa sesi serta akses terhadap dokumen.
5. **Administrator awal:** akun administrator awal dibuat lewat management command. Antarmuka tambah akun berfokus pada mahasiswa dan dosen.
6. **Angka pada landing page:** nilai 500+, 100+, dan 50+ ditulis tetap pada HTML dan bukan statistik database.
7. **Tahapan dokumentasi:** sistem tidak otomatis memasang tujuh tahapan dokumentasi yang wajib. Dosen menambahkan tahapan yang diperlukan untuk tiap proyek/kelompok.
8. **Batas upload:** backend menolak file di atas 10 MB; formulir tertentu dapat mempunyai batas frontend yang lebih rendah.
9. **Kesiapan produksi:** sebelum digunakan sungguhan, jalankan `python manage.py check`, migrasi, serta pengujian fungsional semua peran pada lingkungan yang memiliki dependensi proyek. Konfigurasi secret key, debug, host, HTTPS, backup database, dan backup media harus disesuaikan untuk hosting.

### Endpoint backend utama

Tabel berikut untuk operator/pengembang yang ingin mengetahui jalur komunikasi frontend dengan Django.

| Metode | URL | Kegunaan |
|---|---|---|
| `GET` | `/` | Menyajikan frontend KREASI. |
| `GET` | `/api/session/` | Memeriksa sesi login yang masih aktif. |
| `POST` | `/api/auth/login/` | Memverifikasi kredensial dan memulai sesi. |
| `POST` | `/api/auth/logout/` | Mengakhiri sesi login. |
| `GET` | `/api/state/` | Mengambil data aplikasi sesuai hak akses. |
| `POST` | `/api/state/` | Memvalidasi dan menyimpan state aplikasi. |
| `POST` | `/api/documents/upload/` | Mengunggah berkas dan metadata. |
| `GET` | `/api/documents/<uuid>/` | Membaca/pratinjau dokumen jika diizinkan. |
| `POST` | `/api/documents/<uuid>/delete/` | Menghapus dokumen jika diizinkan. |
| `GET` | `/django-admin/` | Membuka Django Admin sesuai permission framework. |

---

**Acuan kode utama:**

- Frontend dan alur UI: `portal/static/portal/index.html`
- Login, sesi, state, serta dokumen: `portal/views.py`
- Model akun dan dokumen: `portal/models.py`
- Aturan penyimpanan dan pembatasan state berdasarkan role: `portal/repository.py`
- Layanan akun per peran: `portal/services.py`
- Pemetaan URL: `kreasi_project/urls.py`
- Pembuatan administrator awal: `portal/management/commands/create_kreasi_admin.py`
