# Haimiya
ai companion project
# Haimiya — floating AI companion

## Isi folder ini

```
haimiya/
├── main.py                        # app utama (chat + kontrol)
├── service/bubble.py               # service overlay (bubble)
├── buildozer.spec                  # konfigurasi build APK
└── .github/workflows/build.yml     # build APK otomatis di GitHub
```

## Cara pakai dari HP (tanpa PC)

1. Bikin akun GitHub kalau belum punya, lalu bikin repo baru (public
   lebih gampang untuk kuota Actions gratis).
2. Upload semua file di folder ini ke repo itu, dengan struktur folder
   yang sama persis (termasuk folder `.github/workflows/` dan
   `service/`). Bisa lewat app GitHub, atau browser di HP (menu
   "Add file" → "Upload files").
3. **Sebelum push**, cek `buildozer.spec`:
   - `package.domain` dan `package.name` — kalau kamu ganti ini,
     ganti juga `APP_PACKAGE` di `main.py` biar cocok
     (`APP_PACKAGE = "<domain>.<name>"`).
4. Setelah file lengkap, GitHub Actions otomatis jalan (lihat tab
   "Actions" di repo). Proses compile pertama biasanya 15–30 menit.
5. Kalau sukses, buka run yang selesai → bagian "Artifacts" → download
   `haimiya-apk` (isinya file `.apk`).
6. Install APK itu di HP (mungkin perlu aktifkan "izinkan install dari
   sumber tidak dikenal").

## Yang perlu dicoba pas pertama install

1. Buka app Haimiya, isi & simpan Groq API key.
2. Coba ngobrol dulu — pastikan koneksi ke Groq jalan.
3. Tekan "Izin Overlay" → aktifkan izin "muncul di atas aplikasi lain".
4. Tekan "Nyalakan Bubble" → harusnya muncul notifikasi permanen +
   bubble ungu kecil yang bisa ditarik ke mana saja dan dibuka lagi
   dengan tap.

## Batasan yang jujur perlu kamu tahu

- **Kode service overlay (`service/bubble.py`) belum pernah dites di
  HP fisik** — ditulis berdasarkan pola pyjnius + WindowManager yang
  umum dipakai, tapi ada kemungkinan perlu penyesuaian kecil. Karena
  kamu cuma pegang HP tanpa PC, debugging lewat `adb logcat` bakal
  susah kalau ada crash tanpa pesan yang jelas — kalau mentok, coba
  cari akses PC/laptop sebentar (bahkan warnet/laptop teman) buat
  sambungkan HP lewat USB debugging dan lihat log error-nya.
- **Notifikasi permanen nggak bisa dihilangkan** selama bubble aktif —
  ini aturan Android buat foreground service, bukan bug.
- **Android 13 ke atas** kadang minta izin notifikasi terpisah
  (`POST_NOTIFICATIONS`) di runtime, di luar izin overlay. Kalau
  notifikasinya nggak muncul walau service jalan, cek pengaturan
  notifikasi app Haimiya.
- **HP dengan MIUI/ColorOS/FuntouchOS/One UI** sering punya battery
  optimizer & "autostart manager" sendiri yang bisa mematikan service
  background. Kalau bubble suka hilang sendiri, whitelist Haimiya di
  pengaturan baterai & autostart HP-mu.
- **Auto-nyala lagi setelah HP restart belum diimplementasikan** di
  kode ini — izin `RECEIVE_BOOT_COMPLETED` sudah disiapkan di
  `buildozer.spec`, tapi butuh komponen tambahan (custom Android
  BroadcastReceiver) buat benar-benar jalan otomatis. Ini langkah
  lanjutan yang bisa dikerjakan setelah versi dasarnya jalan dengan
  baik.
- Untuk urusan API, app ini manggil endpoint Groq langsung pakai
  `requests` (bukan library resmi `groq` yang tadi kamu install) —
  ini sengaja, karena `requests` jauh lebih gampang di-package ke
  Android lewat Buildozer dibanding dependency library resmi Groq.
