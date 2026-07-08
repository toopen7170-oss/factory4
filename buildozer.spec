[app]
title = factory4
package.name = factory4
package.domain = com.factory.cycling
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,mp3,ttf
source.include_patterns = font/*.ttf
version = 1.0.0
requirements = python3,kivy==2.3.0,pillow,pyjnius
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.ndk_api = 21
android.archs = arm64-v8a
orientation = landscape
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
