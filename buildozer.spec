[app]
title = factory4
package.name = factory4
package.domain = com.factory.cycling
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,mp3,ttf
source.include_patterns = font/*.ttf
version = 1.0.0

# 💡 [핵심 버그 픽스] Python 3.14 강제 다운로드를 막고 3.11 버전으로 영구 락인
requirements = python3==3.11,kivy==2.3.0,pillow,pyjnius

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
