[app]
title = factory4
package.name = factory4
package.domain = com.factory.cycling
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,mp3,ttf
source.include_patterns = font/*.ttf
version = 1.0.0
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pillow,pyjnius,sqlite3
orientation = landscape
fullscreen = 1

# 💡 갤럭시 S26 울트라 환경의 완벽한 하드웨어 접근을 위한 권한 매트릭스 각인
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
