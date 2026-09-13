cat > /mnt/user-data/outputs/haimiya/buildozer.spec << 'EOF'
[app]
title = Haimiya
package.name = haimiya
package.domain = org.haimiya
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

requirements = python3,kivy,requests,pyjnius

orientation = portrait
fullscreen = 0

# Izin yang dibutuhkan:
# - INTERNET: buat manggil Groq API
# - SYSTEM_ALERT_WINDOW: buat bubble overlay
# - FOREGROUND_SERVICE: biar service bubble bisa tetap jalan
# - RECEIVE_BOOT_COMPLETED: disiapkan buat fitur auto-start
#   setelah HP restart (langkah lanjutan, belum diimplementasi
#   di kode ini)
android.permissions = INTERNET,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED

# Service background buat bubble (lihat service/bubble.py)
services = bubble:service/bubble.py

android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

# Wajib True biar proses build otomatis (CI) nggak macet nungguin
# konfirmasi lisensi Android SDK secara manual.
android.accept_sdk_license = True

[buildozer]
log_level = 2
EOF
echo done