[app]
title = factory4
package.name = factory4
package.domain = com.factory.cycling
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,mp3,ttf
source.include_patterns = font/*.ttf
version = 1.0.0

# 💡 [버그 픽스] python3와 hostpython3의 버전을 3.11로 완벽히 일치시켜 충돌 차단
requirements = python3==3.11,hostpython3==3.11,kivy==2.3.0,pillow,pyjnius

android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.build_tools_version = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a
orientation = landscape
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
