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
# 1. 인프라 경로 설정
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
        
        # [AI 방어 전술 1] 폰트가 없는 초기 상태이므로 무조건 '영어'로 출력하여 Tofu(네모) 방지
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
        if all(grants):
            self.setup_infrastructure()
        else:
            # [AI 방어 전술 2] 권한 거부 시에도 폰트가 없으므로 '영어'로 안내
            error_msg = "[Error] Permission Denied.\n\n"
            error_msg += "Please go to Android Settings -> Apps -> MetaRider V1\n"
            error_msg += "Allow ALL Permissions (Files, Location, Bluetooth)\n"
            error_msg += "Then restart the app."
            self.status_label.text = error_msg
            self.status_label.color = (1, 0.2, 0.2, 1)

    def setup_infrastructure(self):
        target_dirs = [FACTORY_ROOT, CORE_DIR, LOG_DIR, MUSIC_DIR, VIDEO_DIR, FONT_DIR]
        for directory in target_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception as e:
                    self.status_label.text = f"[Error] Cannot create folders.\n{str(e)}"
                    self.status_label.color = (1, 0.2, 0.2, 1)
                    return

        # 폴더가 정상 생성/접근되면 폰트를 불러옴
        self.register_fonts()
        # 폰트 로드 성공 시 한글 출력 시작
        self.scan_resources()

    def register_fonts(self):
        universal_font = os.path.join(FONT_DIR, 'universal.ttf')
        font_mapping = {
            'AppFont': 'app_font.ttf', 'Chinese': 'chinese.ttf',
            'Japanese': 'japanese.ttf', 'Arabic': 'arabic.ttf',
            'Thai': 'thai.ttf', 'Global': 'global.ttf', 'Korean': 'korean.ttf'
        }
        
        primary_font = None
        for fn in ['korean.ttf', 'app_font.ttf', 'global.ttf', 'universal.ttf']:
            chk_path = os.path.join(FONT_DIR, fn)
            if os.path.exists(chk_path):
                primary_font = chk_path
                break
                
        if primary_font:
            LabelBase.register(name=DEFAULT_FONT, fn_regular=primary_font)
            self.status_label.font_name = DEFAULT_FONT

        for font_name, file_name in font_mapping.items():
            font_path = os.path.join(FONT_DIR, file_name)
            if os.path.exists(font_path):
                LabelBase.register(name=font_name, fn_regular=font_path)
            else:
                if os.path.exists(universal_font):
                    LabelBase.register(name=font_name, fn_regular=universal_font)

    def scan_resources(self):
        # 여기까지 도달했다면 폰트가 성공적으로 로드된 것이므로 '한글' 사용 가능!
        log_text = "[인프라 및 리소스 스캔 완료]\n\n"
        
        music_files = glob.glob(os.path.join(MUSIC_DIR, '*.mp3'))
        log_text += f"🎵 국내음악(mp3) 발견: {len(music_files)}개\n"

        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv', '*.mov'):
            video_files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
        
        log_text += f"🎬 주행영상 발견: {len(video_files)}개\n\n"
        log_text += "[System Ready] 자전거 연동 대기 중..."
        
        self.status_label.text = log_text
        self.status_label.color = (0.2, 1, 0.2, 1)

class MetaRiderApp(App):
    def build(self):
        return ResourceScannerLayout()

if __name__ == '__main__':
    MetaRiderApp().run()
