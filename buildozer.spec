[app]
# 앱 기본 정보
title = MetaRider V1
package.name = metariderv1
package.domain = org.factory4

# 소스 코드 및 포함할 리소스 확장자 설정
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,mp3,mp4,avi,mkv,mov
version = 1.0

# 핵심 엔진 및 라이브러리 포함 (블루투스와 안드로이드 API 제어용)
requirements = python3, kivy, android, jnius

# ★ AI 통제선: 안드로이드 필수 권한 요청 (MANAGE_EXTERNAL_STORAGE 추가 완료)
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE, BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# 안드로이드 최신 API 타겟팅
android.api = 33
android.minapi = 24
android.accept_sdk_license = True

# 아키텍처 설정 (최신 안드로이드 스마트폰 호환성)
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
# 빌드 로그 출력 레벨
log_level = 2
warn_on_root = 1
