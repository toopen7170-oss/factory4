import os
import sys
import traceback
import glob
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase, DEFAULT_FONT

# 안드로이드 전용 모듈 로드 (권한 요청용)
if platform == 'android':
    from android.permissions import request_permissions, Permission

# ---------------------------------------------------------
# 1. 인프라 경로 설정 (공장장님 지시 사항 100% 반영)
# ---------------------------------------------------------
if platform == 'android':
    # 안드로이드 최상위 공장 폴더
    FACTORY_ROOT = '/sdcard/Download/factory'
else:
    # PC 테스트용 더미 경로
    FACTORY_ROOT = os.path.join(os.getcwd(), 'factory_test')

# 1-1. 코어(Core) 폴더 및 오류 로그 폴더 분리
CORE_DIR = os.path.join(FACTORY_ROOT, 'factory1_core')
LOG_DIR = os.path.join(FACTORY_ROOT, 'crash_logs_오류로그')  # Core 바깥으로 독립

# 1-2. 미디어 및 폰트 폴더 세부 경로
MUSIC_DIR = os.path.join(CORE_DIR, 'music', '국내음악')
VIDEO_DIR = os.path.join(CORE_DIR, 'video')
FONT_DIR = os.path.join(CORE_DIR, 'font')

# ---------------------------------------------------------
# 2. [AI 방어 로직] 치명적 오류 발생 시 로그 파일로 자동 저장
# ---------------------------------------------------------
def global_exception_handler(exctype, value, tb):
    # 에러 발생 시 지정된 오류 로그 폴더로 텍스트 출력
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except:
            pass
            
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    log_file = os.path.join(LOG_DIR, 'crash_log.txt')
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(error_msg + "\n" + "="*50 + "\n")
    except:
        pass 
    sys.__excepthook__(exctype, value, tb)

# 파이썬 기본 에러 핸들러를 가로채서 위 함수로 연결 (앱이 튕겨도 기록 남김)
sys.excepthook = global_exception_handler

class ResourceScannerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.status_label = Label(
            text="[System Booting...]\n경로 스캔 및 리소스 로드 중...",
            font_size='18sp',
            halign='center'
        )
        self.add_widget(self.status_label)
        # 1초 뒤 권한 요청 및 초기화 시작
        Clock.schedule_once(self.start_initialization, 1)

    def start_initialization(self, dt):
        if platform == 'android':
            self.status_label.text = "안드로이드 권한 확인 중..."
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT,
                Permission.ACCESS_FINE_LOCATION
            ], self.on_permissions_result)
        else:
            self.setup_infrastructure()

    def on_permissions_result(self, permissions, grants):
        if all(grants):
            self.setup_infrastructure()
        else:
            self.status_label.text = "[Error] 권한이 거부되었습니다.\n앱 권한 설정에서 수동으로 허용해주세요."

    def setup_infrastructure(self):
        # 1단계: 지정된 절대 경로에 폴더 생성 (없을 경우)
        target_dirs = [FACTORY_ROOT, CORE_DIR, LOG_DIR, MUSIC_DIR, VIDEO_DIR, FONT_DIR]
        for directory in target_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)

        # 2단계: 다국어 폰트 매핑 및 대체(Fallback) 로직 실행
        self.register_fonts()

        # 3단계: 미디어 파일 자동 스캔 (mp3, 비디오)
        self.scan_resources()

    def register_fonts(self):
        universal_font = os.path.join(FONT_DIR, 'universal.ttf')
        
        # 공장장님이 지정한 국가별 폰트 리스트
        font_mapping = {
            'AppFont': 'app_font.ttf',
            'Chinese': 'chinese.ttf',
            'Japanese': 'japanese.ttf',
            'Arabic': 'arabic.ttf',
            'Thai': 'thai.ttf',
            'Global': 'global.ttf',
            'Korean': 'korean.ttf'
        }
        
        # [우선순위 1] 기본 UI 폰트 세팅 (korean -> app_font -> global -> universal 순)
        primary_font = None
        for fn in ['korean.ttf', 'app_font.ttf', 'global.ttf', 'universal.ttf']:
            chk_path = os.path.join(FONT_DIR, fn)
            if os.path.exists(chk_path):
                primary_font = chk_path
                break
                
        if primary_font:
            LabelBase.register(name=DEFAULT_FONT, fn_regular=primary_font)
            self.status_label.font_name = DEFAULT_FONT

        # [우선순위 2] 국가별 폰트 개별 등록 및 Fallback(땜빵) 처리
        for font_name, file_name in font_mapping.items():
            font_path = os.path.join(FONT_DIR, file_name)
            
            if os.path.exists(font_path):
                # 파일이 있으면 해당 폰트 적용
                LabelBase.register(name=font_name, fn_regular=font_path)
            else:
                # 파일이 없으면 universal.ttf로 강제 덮어쓰기 (Tofu 깨짐 방지)
                if os.path.exists(universal_font):
                    LabelBase.register(name=font_name, fn_regular=universal_font)

    def scan_resources(self):
        log_text = "[Resource Scan Completed]\n\n"
        
        # 음악 파일 스캔 (.mp3)
        music_files = glob.glob(os.path.join(MUSIC_DIR, '*.mp3'))
        log_text += f"🎵 국내음악(mp3) 발견: {len(music_files)}개\n"

        # 주행 영상 파일 스캔 (다양한 확장자 지원, 새 영상 자동 스캔)
        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv', '*.mov'):
            video_files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
        
        log_text += f"🎬 주행영상 발견: {len(video_files)}개\n"
        if video_files:
            log_text += "(신규 맵 로드맵 자동 연동 대기 중)\n"

        log_text += "\n[System Ready] 자전거 연동 대기 중..."
        
        self.status_label.text = log_text
        self.status_label.color = (0.2, 1, 0.2, 1)

class MetaRiderApp(App):
    def build(self):
        return ResourceScannerLayout()

if __name__ == '__main__':
    MetaRiderApp().run()
