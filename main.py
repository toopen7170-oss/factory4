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

# 안드로이드 전용 모듈 로드
if platform == 'android':
    from android.permissions import request_permissions, Permission

# ---------------------------------------------------------
# 1. 인프라 경로 설정 (공장장님 지정 절대 경로 완벽 반영)
# ---------------------------------------------------------
if platform == 'android':
    FACTORY_ROOT = '/sdcard/Download/factory'
else:
    FACTORY_ROOT = os.path.join(os.getcwd(), 'factory_test')

CORE_DIR = os.path.join(FACTORY_ROOT, 'factory1_core')
LOG_DIR = os.path.join(FACTORY_ROOT, 'crash_logs_오류로그')
MUSIC_DIR = os.path.join(CORE_DIR, 'music', '국내음악')
VIDEO_DIR = os.path.join(CORE_DIR, 'video')
FONT_DIR = os.path.join(CORE_DIR, 'font')

# ---------------------------------------------------------
# 2. 블랙박스 (오류 로그) 시스템
# ---------------------------------------------------------
def global_exception_handler(exctype, value, tb):
    if not os.path.exists(LOG_DIR):
        try: os.makedirs(LOG_DIR)
        except: pass
        
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    log_file = os.path.join(LOG_DIR, 'crash_log.txt')
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(error_msg + "\n" + "="*50 + "\n")
    except:
        pass 
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_handler

class ResourceScannerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.last_video_count = -1  # 자동 스캔 감지용 변수
        
        # [초기 화면]
        self.status_label = Label(
            text="[System Booting]\nRequesting Permissions...",
            font_size='18sp',
            halign='center'
        )
        self.add_widget(self.status_label)
        Clock.schedule_once(self.start_initialization, 1)

    def start_initialization(self, dt):
        if platform == 'android':
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
        # [AI 방어 전술 수정] 안드로이드 11 이상 권한 버그 강제 우회
        # grants 결과를 믿지 않고, 폴더 생성 및 쓰기 테스트를 직접 실행함.
        self.setup_infrastructure()

    def setup_infrastructure(self):
        target_dirs = [FACTORY_ROOT, CORE_DIR, LOG_DIR, MUSIC_DIR, VIDEO_DIR, FONT_DIR]
        try:
            # 1. 폴더 생성 시도
            for directory in target_dirs:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    
            # 2. 쓰기 권한 실제 확인용 더미 파일 생성 테스트
            test_file = os.path.join(FACTORY_ROOT, 'permission_test.txt')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            
        except Exception as e:
            # 권한이 진짜 없을 때만 영어+한글 혼용으로 최후의 에러 안내
            error_msg = "[Error] Storage Permission Denied.\n\n"
            error_msg += "안드로이드 설정에서 권한이 완전히 허용되지 않았습니다.\n\n"
            error_msg += "1. 앱 설정 -> 권한 -> '위치', '근처 기기(블루투스)' 허용\n"
            error_msg += "2. 특별한 접근 -> '모든 파일에 대한 접근' -> MetaRider V1 (허용)\n\n"
            error_msg += f"Detail: {str(e)}"
            self.status_label.text = error_msg
            self.status_label.color = (1, 0.2, 0.2, 1)
            return

        # 권한 테스트 통과 시 폰트 및 미디어 로드
        self.register_fonts()
        self.scan_resources()
        
        # [신규 기능] 5초마다 백그라운드에서 동영상 폴더 자동 스캔 실행
        Clock.schedule_interval(self.auto_scan_video, 5)

    def register_fonts(self):
        universal_font = os.path.join(FONT_DIR, 'universal.ttf')
        
        # 국가별 폰트 매핑
        font_mapping = {
            'AppFont': 'app_font.ttf', 'Chinese': 'chinese.ttf',
            'Japanese': 'japanese.ttf', 'Arabic': 'arabic.ttf',
            'Thai': 'thai.ttf', 'Global': 'global.ttf', 'Korean': 'korean.ttf'
        }
        
        # 1. 앱 기본 한글 폰트 적용
        primary_font = None
        for fn in ['korean.ttf', 'app_font.ttf', 'global.ttf', 'universal.ttf']:
            chk_path = os.path.join(FONT_DIR, fn)
            if os.path.exists(chk_path):
                primary_font = chk_path
                break
                
        if primary_font:
            LabelBase.register(name=DEFAULT_FONT, fn_regular=primary_font)
            self.status_label.font_name = DEFAULT_FONT

        # 2. 국가별 폰트 각각 적용 (없으면 universal.ttf로 강제 대체)
        for font_name, file_name in font_mapping.items():
            font_path = os.path.join(FONT_DIR, file_name)
            if os.path.exists(font_path):
                LabelBase.register(name=font_name, fn_regular=font_path)
            else:
                if os.path.exists(universal_font):
                    LabelBase.register(name=font_name, fn_regular=universal_font)

    def scan_resources(self):
        log_text = "[인프라 및 리소스 스캔 완료]\n\n"
        
        # mp3 음악 스캔
        music_files = glob.glob(os.path.join(MUSIC_DIR, '*.mp3'))
        log_text += f"🎵 국내음악(mp3) 발견: {len(music_files)}개\n"

        # 주행 영상 스캔
        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv', '*.mov'):
            video_files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
        
        self.last_video_count = len(video_files)
        log_text += f"🎬 주행영상 발견: {self.last_video_count}개\n\n"
        
        log_text += "[System Ready] 자전거 연동 대기 중...\n"
        log_text += "(신규 동영상 실시간 자동 스캔 작동 중 ♻️)"
        
        self.status_label.text = log_text
        self.status_label.color = (0.2, 1, 0.2, 1)

    def auto_scan_video(self, dt):
        # 5초 주기로 비디오 폴더 확인 후 갯수 변동 시 화면 즉시 리프레시
        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv', '*.mov'):
            video_files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
        
        current_count = len(video_files)
        # 새로운 영상이 들어오거나 지워지면 스캔 재가동
        if current_count != self.last_video_count:
            self.scan_resources()

class MetaRiderApp(App):
    def build(self):
        return ResourceScannerLayout()

if __name__ == '__main__':
    MetaRiderApp().run()
