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
requirements = python3,kivy,android,jnius,ffmpeg,ffpyplayer

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
# 💡 [핵심 수정 사항] C컴파일러 오류(ccache) 해결을 위한 설정
# ==========================================
# 1. C/C++ 컴파일이 가장 안정적으로 지원되는 NDK 25b 버전으로 강제 고정합니다.
android.ndk = 25b

# 2. ffmpeg 및 ffpyplayer의 최신 빌드 레시피가 포함된 p4a 개발(develop) 브랜치를 사용합니다.
p4a.branch = develop
# ==========================================

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
