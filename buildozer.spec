[app]
# (str) Title of your application
title = factory4

# (str) Package name
package.name = factory4

# (str) Package domain (needed for android packaging)
package.domain = com.factory.cycling

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,txt,mp3,ttf

# (list) List of inclusions using pattern matching
source.include_patterns = font/*.ttf

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# 💡 핵심 수정: 404 에러 방지를 위해 파이썬 패치 버전을 3.11.9로 정확하게 명시
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pillow,pyjnius

# (str) Supported orientations
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# -----------------------------------------------------------------------------
# Android configuration
# -----------------------------------------------------------------------------

# (list) Permissions
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use
android.ndk_api = 21

# (list) Architecture to build for
android.archs = arm64-v8a

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2
warn_on_root = 1
