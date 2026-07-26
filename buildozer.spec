[app]

# (str) Title of your application
title = MetaRider

# (str) Package name
package.name = metariderv1

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (exts)
source.include_exts = py,png,jpg,kv,atlas,mp4,avi,mkv,wav,mp3

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements 
# 💡 [수정됨] 에러를 유발하고 앱을 무겁게 만드는 ffmpeg, ffpyplayer를 제거했습니다. 
# Kivy는 안드로이드 네이티브 플레이어를 통해 mp3, mp4를 정상적으로 재생합니다.
requirements = python3,kivy,android,jnius

# (str) Supported orientations
orientation = portrait

#
# Android specific
#
fullscreen = 1
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.skip_update = False
android.accept_sdk_license = True
android.archs = arm64-v8a
android.allow_backup = True

# ==========================================
# 💡 [안정화 유지 설정]
# ==========================================
# 1. ccache(컴파일러) 에러를 막기 위해 안정화된 NDK 25b는 계속 유지합니다.
android.ndk = 25b

# 2. IndexError(엔진 버그) 방지를 위해 공식 안정화 버전(master)을 사용합니다.
p4a.branch = master
# ==========================================

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
