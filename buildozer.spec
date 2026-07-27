[app]

# (str) Title of your application
title = MetaRider

# (str) Package name
package.name = metariderv1

# (str) Package domain (needed for android packaging)
package.domain = org.kivy

# (str) Source code where the main.py live (누락되었던 핵심 코드 추가)
source.dir = .

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas,ttf,mp3,mp4,avi,mkv,mov,bin,txt

# (list) List of inclusion patterns
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let it empty to exclude nothing)
#source.exclude_exts = spec

# (list) List of exclusion patterns
#source.exclude_patterns = license,images/mu/

# (str) Application versioning
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,pyjnius,android,ffpyplayer

# (list) Custom source folders for python modules
#source.lib_dirs = ../(lib)

# (str) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# (list) Features
#android.features = android.hardware.usb.host

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android SDK version to use
#android.sdk = 20

# (str) Android NDK version to use
#android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app supports, it can be higher than minapi on android.
#android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (list) The android architectures to build for,, supported are: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (API >= 23)
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug (with command output))
log_level = 2

# (str) Path to build artifact, storage, logging
#bin_dir = ./bin

# (int) Display warning about running as root
warn_root = 1
