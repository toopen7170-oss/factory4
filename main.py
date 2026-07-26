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
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.core.text import LabelBase

# ---------------------------------------------------------
# 1. 경로 설정 (정확한 기기 내장 메모리 경로)
# ---------------------------------------------------------
if platform == 'android':
    FACTORY_ROOT = '/sdcard/Download/factory'
else:
    FACTORY_ROOT = os.path.join(os.getcwd(), 'factory')

CORE_DIR = os.path.join(FACTORY_ROOT, 'factory1_core')
LOG_DIR = os.path.join(FACTORY_ROOT, 'crash_logs_오류로그')
MUSIC_DIR = os.path.join(CORE_DIR, 'music', '국내음악')
VIDEO_DIR = os.path.join(CORE_DIR, 'video')
FONT_DIR = os.path.join(CORE_DIR, 'font')

# ---------------------------------------------------------
# 2. 블랙박스 (오류 로그 파일 자동 저장)
# ---------------------------------------------------------
def global_exception_handler(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, 'crash_log.txt')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(error_msg + "\n" + "="*50 + "\n")
    except: 
        pass
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_handler

# ---------------------------------------------------------
# 3. 폰트 등록 시스템 (다국어 및 범용 폰트 매핑)
# ---------------------------------------------------------
def register_external_fonts():
    try:
        os.makedirs(FONT_DIR, exist_ok=True)
    except: pass
    
    universal_font = os.path.join(FONT_DIR, 'universal.ttf')
    has_universal = os.path.exists(universal_font)

    # 요청하신 다국어 폰트 매핑
    font_mapping = {
        'AppFont': 'app_font.ttf', 
        'Chinese': 'chinese.ttf',
        'Japanese': 'japanese.ttf', 
        'Arabic': 'arabic.ttf',
        'Thai': 'thai.ttf', 
        'Global': 'global.ttf', 
        'Korean': 'korean.ttf',
        'Universal': 'universal.ttf'
    }

    for font_name, file_name in font_mapping.items():
        font_path = os.path.join(FONT_DIR, file_name)
        if os.path.exists(font_path):
            LabelBase.register(name=font_name, fn_regular=font_path)
        elif has_universal:
            # 해당 국가 폰트가 없으면 무조건 universal.ttf 적용
            LabelBase.register(name=font_name, fn_regular=universal_font)

try: register_external_fonts()
except: pass

def get_safe_font():
    if os.path.exists(os.path.join(FONT_DIR, 'korean.ttf')): return 'Korean'
    if os.path.exists(os.path.join(FONT_DIR, 'universal.ttf')): return 'Universal'
    return 'Roboto'

# ---------------------------------------------------------
# 4. 안드로이드 블루투스 및 미디어 리스너 (JNI)
# ---------------------------------------------------------
if platform == 'android':
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        
        # 블루투스 스캔 리스너
        class BLEScanCallback(PythonJavaClass):
            __javainterfaces__ = ['android/bluetooth/BluetoothAdapter$LeScanCallback']
            __javacontext__ = 'app'
            def __init__(self, on_device_found, **kwargs):
                super().__init__(**kwargs)
                self.on_device_found = on_device_found
            @java_method('(Landroid/bluetooth/BluetoothDevice;I[B)V')
            def onLeScan(self, device, rssi, scanRecord):
                name = device.getName()
                address = device.getAddress()
                if name: self.on_device_found(name, address)

        # 블루투스 데이터 리스너
        class BLEGattCallback(PythonJavaClass):
            __javainterfaces__ = ['android/bluetooth/BluetoothGattCallback']
            __javacontext__ = 'app'
            def __init__(self, app_logic, **kwargs):
                super().__init__(**kwargs)
                self.app_logic = app_logic
            @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
            def onConnectionStateChange(self, gatt, status, newState):
                if newState == 2: self.app_logic.on_gatt_connected(gatt)
                elif newState == 0: self.app_logic.on_gatt_disconnected()
            @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
            def onServicesDiscovered(self, gatt, status):
                if status == 0: self.app_logic.on_services_discovered(gatt)
            @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V')
            def onCharacteristicChanged(self, gatt, characteristic):
                value = characteristic.getValue()
                self.app_logic.on_data_received(value)
            @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V')
            def onDescriptorWrite(self, gatt, descriptor, status):
                pass
                
        # 연속 재생을 위한 미디어 종료 리스너
        class MusicCompletionListener(PythonJavaClass):
            __javainterfaces__ = ['android/media/MediaPlayer$OnCompletionListener']
            __javacontext__ = 'app'
            def __init__(self, callback, **kwargs):
                super().__init__(**kwargs)
                self.callback = callback
            @java_method('(Landroid/media/MediaPlayer;)V')
            def onCompletion(self, mp):
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.callback(), 0)
    except Exception:
        pass

# ---------------------------------------------------------
# 5. 메인 앱 화면 및 통제 로직
# ---------------------------------------------------------
class MetaRiderMainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        self.found_devices = {}
        
        # 파일 목록 및 선택 상태 관리
        self.music_files = []
        self.video_files = []
        self.selected_music_paths = set() 
        
        self.prev_crank_rev = -1
        self.prev_crank_time = -1
        
        # 오디오 플레이어
        self.audio_player = None
        self.is_music_playing = False
        self.play_queue = []
        self.current_play_index = 0
        
        safe_font = get_safe_font()
        
        # 1. 상태 라벨
        self.status_label = Label(
            text="[시스템 부팅 중] 환경을 설정하고 있습니다...",
            font_name=safe_font, font_size='16sp', halign='center', valign='middle', size_hint_y=0.15
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.add_widget(self.status_label)

        # 2. 미디어 리스트(팝업) 버튼 레이아웃
        self.media_layout = GridLayout(cols=2, size_hint_y=0.1, spacing=10)
        
        # 이모티콘 깨짐 방지를 위해 일반 텍스트 사용
        self.music_btn = Button(text="[음악] 목록 열기", font_name=safe_font, background_color=(0.2, 0.8, 0.2, 1))
        self.music_btn.bind(on_press=self.open_music_popup)
        self.media_layout.add_widget(self.music_btn)
        
        self.video_btn = Button(text="[영상] 목록 열기", font_name=safe_font, background_color=(0.8, 0.2, 0.2, 1))
        self.video_btn.bind(on_press=self.open_video_popup)
        self.media_layout.add_widget(self.video_btn)
        
        self.add_widget(self.media_layout)

        # 3. RPM
        self.rpm_label = Label(
            text="RPM: 0", font_name=safe_font, font_size='60sp', color=(0, 1, 1, 1), bold=True, size_hint_y=0.3
        )
        self.add_widget(self.rpm_label)
        
        # 4. 블루투스 기기 리스트
        self.scroll_view = ScrollView(size_hint_y=0.3)
        self.device_list_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.device_list_layout.bind(minimum_height=self.device_list_layout.setter('height'))
        self.scroll_view.add_widget(self.device_list_layout)
        self.add_widget(self.scroll_view)
        
        # 5. 블루투스 스캔 버튼
        self.scan_btn = Button(
            text="블루투스 기기 찾기", font_name=safe_font, size_hint_y=0.15, background_color=(0.2, 0.6, 1, 1),
            halign='center', valign='middle'
        )
        self.scan_btn.bind(size=self.scan_btn.setter('text_size'))
        self.scan_btn.bind(on_press=self.toggle_scan)
        self.add_widget(self.scan_btn)

        Clock.schedule_once(self.start_initialization, 1)

    # ------------------ (초기 인프라 & 자동 스캔) ------------------
    def start_initialization(self, dt):
        target_dirs = [FACTORY_ROOT, CORE_DIR, LOG_DIR, MUSIC_DIR, VIDEO_DIR, FONT_DIR]
        try:
            for directory in target_dirs: os.makedirs(directory, exist_ok=True)
            self.status_label.text = "[시스템 작동 중] 블루투스 스캔 및 미디어 재생 준비 완료."
            self.status_label.color = (0.2, 1, 0.2, 1)
        except:
            self.status_label.text = "[주의] 파일 생성 실패. 저장소 권한을 확인해 주세요."
            self.status_label.color = (1, 0.5, 0.2, 1)

        # 3초마다 미디어(음악/영상) 폴더를 자동 스캔하여 리스트 갱신
        Clock.schedule_interval(self.scan_media_files, 3.0) 
        self.scan_media_files(0)

    def scan_media_files(self, dt=0):
        try:
            if os.path.exists(MUSIC_DIR):
                new_music = glob.glob(os.path.join(MUSIC_DIR, '*.mp3'))
                for m in new_music:
                    if m not in self.music_files: self.selected_music_paths.add(m)
                self.music_files = new_music
            
            if os.path.exists(VIDEO_DIR):
                v_exts = ('*.mp4', '*.avi', '*.mkv', '*.mov')
                self.video_files = []
                for ext in v_exts: self.video_files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
            
            if not self.is_music_playing:
                self.music_btn.text = f"[음악] 목록 열기 ({len(self.music_files)}곡)"
            self.video_btn.text = f"[영상] 목록 열기 ({len(self.video_files)}개)"
        except Exception: pass

    # ------------------ (음악 목록 팝업 및 재생 제어) ------------------
    def open_music_popup(self, instance):
        safe_font = get_safe_font()
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # 팝업 상단 제어 버튼 (글씨 잘림 방지를 위해 폰트 크기 축소 및 텍스트 간소화)
        top_bar = BoxLayout(size_hint_y=0.15, spacing=5)
        btn_sel_all = Button(text="전체선택", font_name=safe_font, font_size='14sp', background_color=(0.4, 0.4, 0.4, 1))
        btn_desel_all = Button(text="선택해제", font_name=safe_font, font_size='14sp', background_color=(0.4, 0.4, 0.4, 1))
        btn_play = Button(text="선택 재생", font_name=safe_font, font_size='14sp', background_color=(0.2, 0.8, 0.2, 1))
        btn_stop = Button(text="정지", font_name=safe_font, font_size='14sp', background_color=(1, 0.5, 0, 1))
        
        top_bar.add_widget(btn_sel_all)
        top_bar.add_widget(btn_desel_all)
        top_bar.add_widget(btn_play)
        top_bar.add_widget(btn_stop)
        content.add_widget(top_bar)
        
        # 곡 리스트 뷰
        scroll = ScrollView(size_hint_y=0.85)
        list_layout = GridLayout(cols=1, size_hint_y=None, spacing=2)
        list_layout.bind(minimum_height=list_layout.setter('height'))
        
        self.checkbox_refs = {} 
        
        for m_path in self.music_files:
            # 글씨 겹침 방지를 위해 리스트 높이를 70으로 확장
            row = BoxLayout(size_hint_y=None, height=70, padding=5)
            cb = CheckBox(size_hint_x=0.15, active=(m_path in self.selected_music_paths))
            
            # 글씨 겹침 방지를 위해 shorten(말줄임표) 속성 추가
            lbl = Label(
                text=os.path.basename(m_path), 
                font_name=safe_font, 
                size_hint_x=0.85, 
                halign='left', 
                valign='middle',
                shorten=True, 
                shorten_from='right'
            )
            lbl.bind(size=lbl.setter('text_size'))
            
            row.add_widget(cb)
            row.add_widget(lbl)
            list_layout.add_widget(row)
            self.checkbox_refs[m_path] = cb
            
        scroll.add_widget(list_layout)
        content.add_widget(scroll)
        
        popup = Popup(title="음악 플레이리스트 (체크된 곡만 연속 재생됩니다)", title_font=safe_font, content=content, size_hint=(0.95, 0.9))
        
        # 버튼 기능 연결
        btn_sel_all.bind(on_press=lambda x: self.toggle_all_music(True))
        btn_desel_all.bind(on_press=lambda x: self.toggle_all_music(False))
        btn_play.bind(on_press=lambda x: [self.update_selected_music(), self.start_playlist(), popup.dismiss()])
        btn_stop.bind(on_press=lambda x: [self.stop_music(), popup.dismiss()])
        
        popup.open()

    def toggle_all_music(self, state):
        for cb in self.checkbox_refs.values(): cb.active = state

    def update_selected_music(self):
        self.selected_music_paths.clear()
        for m_path, cb in self.checkbox_refs.items():
            if cb.active: self.selected_music_paths.add(m_path)

    def start_playlist(self):
        if not self.selected_music_paths: return
        self.play_queue = [m for m in self.music_files if m in self.selected_music_paths]
        self.current_play_index = 0
        self.play_next_song()

    def play_next_song(self):
        if platform != 'android': return
        if self.current_play_index >= len(self.play_queue):
            self.stop_music() 
            return
            
        next_song = self.play_queue[self.current_play_index]
        self.current_play_index += 1
        
        try:
            from jnius import autoclass
            MediaPlayer = autoclass('android.media.MediaPlayer')
            
            if self.audio_player:
                self.audio_player.stop()
                self.audio_player.release()
                
            self.audio_player = MediaPlayer()
            self.audio_player.setDataSource(next_song)
            
            if not hasattr(self, 'completion_listener'):
                self.completion_listener = MusicCompletionListener(self.play_next_song)
            self.audio_player.setOnCompletionListener(self.completion_listener)
            
            self.audio_player.prepare()
            self.audio_player.start()
            
            self.is_music_playing = True
            song_name = os.path.basename(next_song)
            # 이모티콘 제거 후 재생 상태 표시
            self.music_btn.text = f"재생중: {song_name[:10]}..."
            self.music_btn.background_color = (1, 0.5, 0, 1)
        except Exception as e:
            self.status_label.text = f"[음악 오류] {str(e)}"
            self.play_next_song() 

    def stop_music(self):
        if self.audio_player:
            try:
                self.audio_player.stop()
                self.audio_player.release()
            except: pass
        self.audio_player = None
        self.is_music_playing = False
        self.music_btn.text = f"[음악] 목록 열기 ({len(self.music_files)}곡)"
        self.music_btn.background_color = (0.2, 0.8, 0.2, 1)

    # ------------------ (동영상 목록 팝업 및 재생 제어) ------------------
    def open_video_popup(self, instance):
        safe_font = get_safe_font()
        content = BoxLayout(orientation='vertical', padding=10)
        
        scroll = ScrollView(size_hint_y=1.0)
        list_layout = GridLayout(cols=1, size_hint_y=None, spacing=10)
        list_layout.bind(minimum_height=list_layout.setter('height'))
        
        # 스캔된 비디오 버튼 나열 (이모티콘 제거 및 말줄임표 적용)
        for v_path in self.video_files:
            btn = Button(
                text=f"{os.path.basename(v_path)}", 
                font_name=safe_font, 
                size_hint_y=None, 
                height=80,
                halign='left', 
                valign='middle', 
                padding=(20, 0),
                shorten=True, 
                shorten_from='right'
            )
            btn.bind(size=btn.setter('text_size'))
            btn.bind(on_press=lambda x, path=v_path: [self.play_specific_video(path)])
            list_layout.add_widget(btn)
            
        scroll.add_widget(list_layout)
        content.add_widget(scroll)
        
        popup = Popup(title="영상 선택 (터치 시 외부 앱으로 팝업 재생)", title_font=safe_font, content=content, size_hint=(0.95, 0.9))
        popup.open()

    def play_specific_video(self, video_path):
        if platform == 'android':
            try:
                from jnius import autoclass
                StrictMode = autoclass('android.os.StrictMode')
                VmPolicyBuilder = autoclass('android.os.StrictMode$VmPolicy$Builder')
                StrictMode.setVmPolicy(VmPolicyBuilder().build())

                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                File = autoclass('java.io.File')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                intent = Intent(Intent.ACTION_VIEW)
                file = File(video_path)
                uri = Uri.fromFile(file)
                intent.setDataAndType(uri, "video/*")
                PythonActivity.mActivity.startActivity(intent)
            except Exception as e:
                self.status_label.text = f"[영상 실행 오류] {str(e)}"

    # ------------------ (블루투스 센서 제어) ------------------
    def toggle_scan(self, instance):
        if platform != 'android': return
        if "시작" in self.scan_btn.text: self.start_ble_scan()
        else: self.stop_ble_scan()

    def start_ble_scan(self):
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            self.bluetooth_adapter = BluetoothAdapter.getDefaultAdapter()
            if not self.bluetooth_adapter or not self.bluetooth_adapter.isEnabled():
                self.status_label.text = "[경고] 스마트폰 블루투스를 켜주세요."
                self.status_label.color = (1, 0.8, 0.2, 1)
                return
            self.found_devices.clear()
            self.device_list_layout.clear_widgets()
            self.scan_callback = BLEScanCallback(self.on_device_discovered)
            self.bluetooth_adapter.startLeScan(self.scan_callback)
            self.scan_btn.text = "스캔 중지"
            self.scan_btn.background_color = (1, 0.2, 0.2, 1)
            self.status_label.text = "센서를 찾는 중입니다...\n(페달을 돌려 센서를 깨워주세요)"
        except Exception as e:
            self.status_label.text = f"[스캔 오류] {str(e)}"

    def stop_ble_scan(self):
        try:
            if hasattr(self, 'bluetooth_adapter') and hasattr(self, 'scan_callback'):
                self.bluetooth_adapter.stopLeScan(self.scan_callback)
            self.scan_btn.text = "블루투스 기기 찾기 (스캔 시작)"
            self.scan_btn.background_color = (0.2, 0.6, 1, 1)
        except Exception: pass

    @mainthread
    def on_device_discovered(self, name, address):
        if address not in self.found_devices:
            self.found_devices[address] = name
            safe_font = get_safe_font()
            btn = Button(
                text=f"{name}\n({address})", font_name=safe_font, size_hint_y=None, height=120,
                background_color=(0.3, 0.3, 0.3, 1)
            )
            btn.bind(on_press=lambda x: self.connect_device(name, address))
            self.device_list_layout.add_widget(btn)

    def connect_device(self, name, address):
        self.stop_ble_scan()
        self.status_label.text = f"[{name}] 연결 시도 중..."
        self.status_label.color = (1, 1, 1, 1)
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            device = self.bluetooth_adapter.getRemoteDevice(address)
            self.gatt_callback = BLEGattCallback(self)
            self.gatt = device.connectGatt(PythonActivity.mActivity, False, self.gatt_callback)
        except Exception as e:
            self.status_label.text = f"[연결 오류] {str(e)}"

    @mainthread
    def on_gatt_connected(self, gatt):
        self.status_label.text = "센서와 연결 성공! 데이터를 탐색합니다."
        self.status_label.color = (0.2, 1, 0.2, 1)
        gatt.discoverServices()

    @mainthread
    def on_gatt_disconnected(self):
        self.status_label.text = "센서 연결이 끊어졌습니다."
        self.status_label.color = (1, 0.2, 0.2, 1)
        self.rpm_label.text = "RPM: 0"

    @mainthread
    def on_services_discovered(self, gatt):
        try:
            from jnius import autoclass
            UUID = autoclass('java.util.UUID')
            service_uuid = UUID.fromString("00001816-0000-1000-8000-00805f9b34fb")
            service = gatt.getService(service_uuid)
            
            if service:
                char_uuid = UUID.fromString("00002a5b-0000-1000-8000-00805f9b34fb")
                characteristic = service.getCharacteristic(char_uuid)
                gatt.setCharacteristicNotification(characteristic, True)
                
                desc_uuid = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
                descriptor = characteristic.getDescriptor(desc_uuid)
                BluetoothGattDescriptor = autoclass('android.bluetooth.BluetoothGattDescriptor')
                descriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                gatt.writeDescriptor(descriptor)
                self.status_label.text = "데이터 수신 채널 오픈! 페달을 굴려주세요."
        except Exception as e:
            self.status_label.text = f"[데이터 연결 오류] {str(e)}"

    @mainthread
    def on_data_received(self, value):
        try:
            flags = value[0] & 0xFF
            has_crank = flags & 0x02
            offset = 1 + (6 if (flags & 0x01) else 0)
                
            if has_crank and len(value) >= offset + 4:
                crank_rev = (value[offset] & 0xFF) | ((value[offset+1] & 0xFF) << 8)
                crank_time = (value[offset+2] & 0xFF) | ((value[offset+3] & 0xFF) << 8)
                
                if self.prev_crank_rev != -1:
                    diff_rev = (crank_rev - self.prev_crank_rev) & 0xFFFF
                    diff_time = (crank_time - self.prev_crank_time) & 0xFFFF
                    
                    if diff_time > 0:
                        rpm = (diff_rev / (diff_time / 1024.0)) * 60.0
                        self.rpm_label.text = f"RPM: {int(rpm)}"
                        
                self.prev_crank_rev = crank_rev
                self.prev_crank_time = crank_time
        except: pass

class MetaRiderApp(App):
    def build(self):
        return MetaRiderMainLayout()

if __name__ == '__main__':
    MetaRiderApp().run()
