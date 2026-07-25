import os
import sys
import traceback
import glob
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.core.text import LabelBase, DEFAULT_FONT

# 안드로이드 전용 모듈 로드
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, PythonJavaClass, java_method
    
    # ---------------------------------------------------------
    # [블루투스 통신병] 파이썬 친화적인 클래식 Interface 모드 적용
    # ---------------------------------------------------------
    class BLEScanCallback(PythonJavaClass):
        # 안드로이드의 LeScanCallback '인터페이스'를 직접 호출 (오류 방지)
        __javainterfaces__ = ['android/bluetooth/BluetoothAdapter$LeScanCallback']
        __javacontext__ = 'app'

        def __init__(self, on_device_found, **kwargs):
            super().__init__(**kwargs)
            self.on_device_found = on_device_found

        @java_method('(Landroid/bluetooth/BluetoothDevice;I[B)V')
        def onLeScan(self, device, rssi, scanRecord):
            name = device.getName()
            address = device.getAddress()
            # 이름이 존재하는 블루투스 기기만 파이썬으로 전달
            if name:
                self.on_device_found(name, address)

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

# ---------------------------------------------------------
# 3. 메인 앱 화면 
# ---------------------------------------------------------
class MetaRiderMainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        self.last_video_count = -1
        self.found_devices = {}
        
        # [상단] 시스템 상태창
        self.status_label = Label(
            text="[System Booting]\nRequesting Permissions...",
            font_size='16sp',
            halign='center',
            size_hint_y=0.3
        )
        self.add_widget(self.status_label)
        
        # [중단] 블루투스 기기 리스트 (스크롤)
        self.scroll_view = ScrollView(size_hint_y=0.5)
        self.device_list_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.device_list_layout.bind(minimum_height=self.device_list_layout.setter('height'))
        self.scroll_view.add_widget(self.device_list_layout)
        self.add_widget(self.scroll_view)
        
        # [하단] 블루투스 스캔 버튼
        self.scan_btn = Button(
            text="블루투스 기기 찾기 (스캔 시작)",
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 1, 1),
            disabled=True
        )
        self.scan_btn.bind(on_press=self.toggle_scan)
        self.add_widget(self.scan_btn)

        Clock.schedule_once(self.start_initialization, 1)

    def start_initialization(self, dt):
        if platform == 'android':
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE,
                Permission.BLUETOOTH_SCAN, Permission.BLUETOOTH_CONNECT, Permission.ACCESS_FINE_LOCATION
            ], self.on_permissions_result)
        else:
            self.setup_infrastructure()

    def on_permissions_result(self, permissions, grants):
        self.setup_infrastructure()

    def setup_infrastructure(self):
        target_dirs = [FACTORY_ROOT, CORE_DIR, LOG_DIR, MUSIC_DIR, VIDEO_DIR, FONT_DIR]
        try:
            for directory in target_dirs:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            test_file = os.path.join(FACTORY_ROOT, 'permission_test.txt')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
        except Exception as e:
            self.status_label.text = "[Error] Storage Permission Denied.\n권한을 다시 확인해주세요."
            self.status_label.color = (1, 0.2, 0.2, 1)
            return

        self.register_fonts()
        self.scan_resources()
        self.scan_btn.disabled = False
        Clock.schedule_interval(self.auto_scan_video, 5)

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
            self.scan_btn.font_name = DEFAULT_FONT

        for font_name, file_name in font_mapping.items():
            font_path = os.path.join(FONT_DIR, file_name)
            if os.path.exists(font_path):
                LabelBase.register(name=font_name, fn_regular=font_path)
            elif os.path.exists(universal_font):
                LabelBase.register(name=font_name, fn_regular=universal_font)

    def scan_resources(self):
        log_text = "[인프라 준비 완료]\n\n"
        music_files = glob.glob(os.path.join(MUSIC_DIR, '*.mp3'))
        log_text += f"- 음악: {len(music_files)}개 대기 중\n"
        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv', '*.mov'):
            video_files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
        self.last_video_count = len(video_files)
        log_text += f"- 영상: {self.last_video_count}개 대기 중\n\n"
        log_text += "아래 버튼을 눌러 자전거를 스캔하세요."
        
        self.status_label.text = log_text
        self.status_label.color = (0.2, 1, 0.2, 1)

    def auto_scan_video(self, dt):
        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv', '*.mov'):
            video_files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
        current_count = len(video_files)
        if current_count != self.last_video_count:
            self.scan_resources()

    # ---------------------------------------------------------
    # [블루투스] 인터페이스 통신 로직
    # ---------------------------------------------------------
    def toggle_scan(self, instance):
        if platform != 'android':
            self.status_label.text = "PC 환경에서는 블루투스 스캔이 불가능합니다."
            return

        if self.scan_btn.text == "블루투스 기기 찾기 (스캔 시작)":
            self.start_ble_scan()
        else:
            self.stop_ble_scan()

    def start_ble_scan(self):
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            self.bluetooth_adapter = BluetoothAdapter.getDefaultAdapter()
            
            if not self.bluetooth_adapter or not self.bluetooth_adapter.isEnabled():
                self.status_label.text = "[경고] 스마트폰의 블루투스를 켜주세요."
                self.status_label.color = (1, 0.8, 0.2, 1)
                return

            self.found_devices.clear()
            self.device_list_layout.clear_widgets()
            
            # 파이썬 친화적 콜백 객체 생성 후 스캔 시작
            self.scan_callback = BLEScanCallback(self.on_device_discovered)
            self.bluetooth_adapter.startLeScan(self.scan_callback)
            
            self.scan_btn.text = "스캔 중지"
            self.scan_btn.background_color = (1, 0.2, 0.2, 1)
            self.status_label.text = "주변 센서를 찾는 중입니다...\n(자전거 페달을 돌려 센서를 깨워주세요)"
            self.status_label.color = (0.2, 1, 0.2, 1)
            
        except Exception as e:
            self.status_label.text = f"[스캔 오류 발생]\n{str(e)}"
            self.status_label.color = (1, 0.2, 0.2, 1)

    def stop_ble_scan(self):
        try:
            if hasattr(self, 'bluetooth_adapter') and hasattr(self, 'scan_callback'):
                self.bluetooth_adapter.stopLeScan(self.scan_callback)
            self.scan_btn.text = "블루투스 기기 찾기 (스캔 시작)"
            self.scan_btn.background_color = (0.2, 0.6, 1, 1)
            self.status_label.text = "스캔 중지됨. 리스트에서 기기를 선택하세요."
        except Exception as e:
            pass

    @mainthread
    def on_device_discovered(self, name, address):
        # 중복 기기 추가 방지
        if address not in self.found_devices:
            self.found_devices[address] = name
            
            # 리스트에 기기 버튼 생성
            btn = Button(
                text=f"{name}\n({address})",
                size_hint_y=None,
                height=120,
                font_name=DEFAULT_FONT,
                background_color=(0.3, 0.3, 0.3, 1)
            )
            btn.bind(on_press=lambda x: self.connect_device(name, address))
            self.device_list_layout.add_widget(btn)

    def connect_device(self, name, address):
        self.stop_ble_scan()
        self.status_label.text = f"선택 완료: [{name}]\n(MAC: {address})\n\n연결 및 데이터 수신 대기 중..."
        self.status_label.color = (1, 1, 1, 1)

class MetaRiderApp(App):
    def build(self):
        return MetaRiderMainLayout()

if __name__ == '__main__':
    MetaRiderApp().run()
