# (주의) buildozer.spec 파일 내에서 해당 항목을 찾아 덮어쓰기 하세요.

# 앱 기본 정보
title = MetaRider V1
package.name = metariderv1
package.domain = org.factory4

# 핵심 엔진 및 라이브러리 포함 (블루투스와 안드로이드 API 제어용)
requirements = python3, kivy, android, jnius

# ★ AI 통제선: 안드로이드 필수 권한 요청 (절대 누락 금지)
# 인터넷(다중접속), 외부저장소(폴더접근), 블루투스(센서접속)
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# 안드로이드 최신 API 타겟팅 (Android 11 이상 폴더 접근을 위한 세팅)
android.api = 33
android.minapi = 24
android.accept_sdk_license = True
