import os
import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle, Line
from kivy.utils import platform

# =========================================================
# 🌍 [글로벌 다국어 폰트 매핑 프로토콜]
# =========================================================
# 💡 공장장님 지침: 새로운 국가 추가 시, '국가코드': '폰트파일명' 을 아래에 추가만 하십시오.
LANGUAGE_FONTS = {
    'ko': 'korean.ttf',      # 한국어
    'en': 'global.ttf',      # 영어 (글로벌 기본)
    'zh': 'chinese.ttf',     # 중국어
    'ja': 'japanese.ttf',    # 일본어
    'ar': 'arabic.ttf',      # 아랍어
    'th': 'thai.ttf',        # 태국어
    'default': 'app_font.ttf' # 공통 예비용
}

# 🎛️ 현재 앱 구동 언어 설정 (이곳의 코드를 바꾸면 전체 폰트가 변경됩니다)
CURRENT_LANG_CODE = 'ko'

# 폰트 자동 등록 엔진 (font 폴더 내부 탐색)
FONT_DIR = 'font'
REGISTERED_FONTS = {}

if os.path.exists(FONT_DIR):
    for lang_code, filename in LANGUAGE_FONTS.items():
        font_path = os.path.join(FONT_DIR, filename)
        if os.path.exists(font_path):
            font_name = f'custom_{lang_code}'
            LabelBase.register(name=font_name, fn_regular=font_path)
            REGISTERED_FONTS[lang_code] = font_name
        else:
            print(f"[경고] {filename} 파일을 {FONT_DIR}/ 경로에서 찾을 수 없습니다.")

# 설정된 언어의 폰트를 SAFE_FONT로 지정 (없을 경우 Kivy 기본 폰트인 Roboto 사용)
SAFE_FONT = REGISTERED_FONTS.get(CURRENT_LANG_CODE, 'Roboto')

# ---------------------------------------------------------
# 📡 [블루투스 코어 & 시뮬레이터 연동 인터페이스]
# ---------------------------------------------------------
if platform == 'android':
    from jnius import autoclass, PythonJavaClass, java_method
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    ScanSettings = autoclass('android.bluetooth.le.ScanSettings')
    Looper = autoclass('android.os.Looper')
    
    class BLEScanCallback(PythonJavaClass):
        __javainterfaces__ = ['android/bluetooth/le/ScanCallback']
        __javacontext__ = 'app'
        def __init__(self, target_name, success_cb):
            super(BLEScanCallback, self).__init__()
            self.target_name = target_name
            self.success_cb = success_cb
            self.found = False

        @java_method('(ILandroid/bluetooth/le/ScanResult;)V')
        def onScanResult(self, callbackType, result):
            if self.found or not result: return
            device = result.getDevice()
            if not device: return
            try:
                device_name = device.getName()
                mac_address = device.getAddress()
                if device_name and self.target_name in device_name:
                    self.found = True
                    Clock.schedule_once(lambda dt: self.success_cb(device_name, mac_address), 0)
            except Exception as e: print(e)

        @java_method('(Ljava/util/List;)V')
        def onBatchScanResults(self, results): pass
        @java_method('(I)V')
        def onScanFailed(self, errorCode): pass

class BLEManager:
    def __init__(self):
        self.scanner = None
        self.scan_callback = None
        self._init_adapter()

    def _init_adapter(self):
        if platform == 'android':
            try:
                adapter = BluetoothAdapter.getDefaultAdapter()
                if adapter and adapter.isEnabled():
                    self.scanner = adapter.getBluetoothLeScanner()
            except Exception as e:
                print(f"어댑터 초기화 에러: {e}")

    def scan_for_device(self, target_name, callback_success, callback_fail):
        if platform != 'android':
            callback_fail("가상 시뮬레이션 모드\n(APK 설치 후 작동)")
            return

        try:
            if not self.scanner: 
                self._init_adapter()
            if not self.scanner:
                callback_fail("블루투스 권한 없음\n(APK 빌드 필수)")
                return

            self.stop_scan()
            try:
                if Looper.myLooper() is None: Looper.prepare()
            except Exception: pass

            self.scan_callback = BLEScanCallback(target_name, callback_success)
            settings_builder = autoclass('android.bluetooth.le.ScanSettings$Builder')()
            settings_builder.setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            
            self.scanner.startScan(None, settings_builder.build(), self.scan_callback)
            Clock.schedule_once(lambda dt: self.stop_scan(), 10)
        except Exception as e:
            error_str = str(e)[:25]
            callback_fail(f"시뮬레이터 우회됨\n{error_str}...")

    def stop_scan(self):
        if platform == 'android' and self.scanner and self.scan_callback:
            try:
                self.scanner.stopScan(self.scan_callback)
                self.scan_callback = None
            except Exception: pass

# ---------------------------------------------------------
# 🎛️ [마스터 코어 엔진] 아이보리 & 블랙 선명화 에디션
# ---------------------------------------------------------
class MasterCoreEngine(FloatLayout):
    def __init__(self, **kwargs):
        super(MasterCoreEngine, self).__init__(**kwargs)
        self.safe_font = SAFE_FONT
        self.ble_manager = BLEManager()
        
        # 가상 데이터 변수
        self.sim_time = 0
        self.current_speed = 0.0
        self.current_rpm = 0
        self.total_distance = 0.0
        
        # =========================================================
        # [레이어 1] 메인 대시보드 (아이보리 테마)
        # =========================================================
        self.main_layer = BoxLayout(orientation='vertical', padding=15, spacing=12)
        
        # 1. 상단 정보 바
        top_bar = BoxLayout(size_hint_y=0.08)
        self.nav_title = Label(
            text="FACTORY MASTER METAVERSE v4.0", 
            font_size='12sp', color=(0.2, 0.2, 0.2, 1), bold=True, halign='left'
        )
        self.secret_trigger = Label(
            text="⚙️ [통제실 진입방향]", font_name=self.safe_font,
            font_size='12sp', color=(0.1, 0.5, 0.9, 0.6), halign='right'
        )
        top_bar.add_widget(self.nav_title)
        top_bar.add_widget(self.secret_trigger)
        self.main_layer.add_widget(top_bar)
        
        # 2. HUD 속도계 구역 (짤림 방지 및 선명한 블랙 폰트)
        self.hud_area = FloatLayout(size_hint_y=0.46)
        with self.hud_area.canvas.before:
            Color(0.90, 0.89, 0.85, 1) # 약간 짙은 아이보리로 HUD 구역 분할
            self.hud_bg = Rectangle(size=self.hud_area.size, pos=self.hud_area.pos)
        self.hud_area.bind(size=self._update_hud_canvas, pos=self._update_hud_canvas)
        
        self.speed_label = Label(text="0.0", font_size='60sp', bold=True, color=(0, 0, 0, 1), pos_hint={'center_x': 0.5, 'center_y': 0.58})
        self.speed_unit = Label(text="KM/H", font_size='15sp', bold=True, color=(0.3, 0.3, 0.3, 1), pos_hint={'center_x': 0.5, 'center_y': 0.33})
        self.rpm_label = Label(text="RPM: 0", font_name=self.safe_font, font_size='20sp', bold=True, color=(0.1, 0.4, 0.8, 1), pos_hint={'center_x': 0.5, 'center_y': 0.15})
        
        self.hud_area.add_widget(self.speed_label)
        self.hud_area.add_widget(self.speed_unit)
        self.hud_area.add_widget(self.rpm_label)
        self.main_layer.add_widget(self.hud_area)
        
        # 3. 하단 데이터 매트릭스 (텍스트 크기 안정화)
        data_grid = GridLayout(cols=2, spacing=12, size_hint_y=0.28)
        
        db1 = BoxLayout(orientation='vertical', padding=5)
        db1_lbl = Label(text="DISTANCE", font_size='13sp', bold=True, color=(0.4, 0.4, 0.4, 1))
        self.dist_val = Label(text="0.00 km", font_size='24sp', bold=True, color=(0, 0, 0, 1))
        db1.add_widget(db1_lbl)
        db1.add_widget(self.dist_val)
        
        db2 = BoxLayout(orientation='vertical', padding=5)
        db2_lbl = Label(text="ACTIVE DEVICES", font_name=self.safe_font, font_size='13sp', bold=True, color=(0.4, 0.4, 0.4, 1))
        self.device_val = Label(text="0 / 2", font_size='24sp', bold=True, color=(0.8, 0.1, 0.1, 1))
        db2.add_widget(db2_lbl)
        db2.add_widget(self.device_val)
        
        data_grid.add_widget(db1)
        data_grid.add_widget(db2)
        self.main_layer.add_widget(data_grid)
        
        # 4. 하단 제어 패널 스위치
        self.btn_sim = Button(
            text="⚡ 가상 주행 모드 시뮬레이터 가동 중", font_name=self.safe_font,
            font_size='16sp', size_hint_y=0.18, bold=True,
            background_normal='', background_color=(0.2, 0.2, 0.25, 1), color=(1, 1, 1, 1)
        )
        self.main_layer.add_widget(self.btn_sim)
        self.add_widget(self.main_layer)

        # =========================================================
        # [레이어 2] 비밀 지휘관 통제실 (선명도 강화 배경)
        # =========================================================
        self.commander_layer = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.commander_layer.opacity = 0       
        self.commander_layer.disabled = True   
        
        with self.commander_layer.canvas.before:
            Color(0.93, 0.92, 0.88, 0.99)
            self.bg_rect = Rectangle(size=Window.size, pos=self.commander_layer.pos)
        self.commander_layer.bind(size=self._update_bg, pos=self._update_bg)

        title = Label(text="🟢 자전거 센서 동기화 센터", font_name=self.safe_font, font_size='24sp', bold=True, color=(0, 0, 0, 1), size_hint_y=0.15)
        self.commander_layer.add_widget(title)

        # [ 1호기 통제 UI ]
        box1 = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.32)
        self.status_1 = Label(
            text="[ 1호기 (Cycplus C3) ]\n상태: 🔴 연결 끊김", font_name=self.safe_font, 
            font_size='15sp', bold=True, color=(0.1, 0.1, 0.1, 1), halign='center', valign='middle'
        )
        self.status_1.bind(size=self._update_text_size)
        self.btn_scan_1 = Button(
            text="🔍 1호기 장치 탐색", font_name=self.safe_font, font_size='16sp', bold=True,
            background_normal='', background_color=(0.1, 0.5, 0.8, 1), color=(1, 1, 1, 1)
        )
        self.btn_scan_1.bind(on_press=lambda x: self.start_device_scan(1, "Cycplus C3"))
        box1.add_widget(self.status_1)
        box1.add_widget(self.btn_scan_1)
        self.commander_layer.add_widget(box1)

        # [ 2호기 통제 UI ]
        box2 = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.32)
        self.status_2 = Label(
            text="[ 2호기 (Cycplus C3) ]\n상태: 🔴 연결 끊김", font_name=self.safe_font, 
            font_size='15sp', bold=True, color=(0.1, 0.1, 0.1, 1), halign='center', valign='middle'
        )
        self.status_2.bind(size=self._update_text_size)
        
        btn_box2 = BoxLayout(orientation='horizontal', spacing=10)
        self.btn_scan_2 = Button(
            text="🔍 2호기 탐색", font_name=self.safe_font, font_size='15sp', bold=True,
            background_normal='', background_color=(0.1, 0.5, 0.8, 1), color=(1, 1, 1, 1)
        )
        self.btn_scan_2.bind(on_press=lambda x: self.start_device_scan(2, "Cycplus C3"))
        
        btn_disconnect = Button(
            text="❌ 연결 해제", font_name=self.safe_font, font_size='15sp', bold=True,
            background_normal='', background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1)
        )
        btn_disconnect.bind(on_press=self.disconnect_devices)
        btn_box2.add_widget(self.btn_scan_2)
        btn_box2.add_widget(btn_disconnect)
        box2.add_widget(self.status_2)
        box2.add_widget(btn_box2)
        self.commander_layer.add_widget(box2)

        # [ 복귀 버튼 ]
        btn_save = Button(
            text="💾 설정 저장 후 대시보드 복귀", font_name=self.safe_font, font_size='18sp', bold=True,
            size_hint_y=0.2, background_normal='', background_color=(0.2, 0.65, 0.2, 1), color=(1, 1, 1, 1)
        )
        btn_save.bind(on_press=self.close_commander_room)
        self.commander_layer.add_widget(btn_save)

        self.add_widget(self.commander_layer)
        
        self.touch_count = 0
        self.touch_timer = None
        Clock.schedule_interval(self.update_simulation_data, 0.1)

    def _update_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def _update_text_size(self, instance, value):
        instance.text_size = (instance.width, None)

    def _update_hud_canvas(self, instance, value):
        self.hud_bg.size = instance.size
        self.hud_bg.pos = instance.pos
        instance.canvas.after.clear()
        with instance.canvas.after:
            Color(0, 0, 0, 0.15)
            cx = instance.pos[0] + instance.size[0] / 2
            cy = instance.pos[1] + instance.size[1] / 2
            Line(circle=(cx, cy, min(instance.size)/2.4, -120, 120), width=2.5)

    def update_simulation_data(self, dt):
        self.sim_time += dt
        self.current_speed = 25.0 + 12.0 * math.sin(self.sim_time * 0.5) + 1.5 * math.cos(self.sim_time * 2)
        if self.current_speed < 0: self.current_speed = 0.0
        
        self.current_rpm = int(self.current_speed * 2.8 + 10 * math.sin(self.sim_time * 1.2))
        if self.current_rpm < 0: self.current_rpm = 0
        
        self.total_distance += (self.current_speed / 3600.0) * dt
        
        self.speed_label.text = f"{self.current_speed:.1f}"
        self.rpm_label.text = f"RPM: {self.current_rpm}"
        self.dist_val.text = f"{self.total_distance:.2f} km"

    def on_touch_down(self, touch):
        if touch.x > self.width * 0.70 and touch.y > self.height * 0.85:
            self.touch_count += 1
            if self.touch_timer: self.touch_timer.cancel()
            self.touch_timer = Clock.schedule_once(self.reset_touches, 2.0)
            
            if self.touch_count >= 5:
                self.open_commander_room()
                self.touch_count = 0
                return True 
        return super(MasterCoreEngine, self).on_touch_down(touch)

    def reset_touches(self, dt):
        self.touch_count = 0

    def open_commander_room(self):
        self.main_layer.disabled = True
        self.commander_layer.opacity = 1
        self.commander_layer.disabled = False

    def start_device_scan(self, device_id, target_name):
        if device_id == 1:
            self.btn_scan_1.text = "🔄 탐색 중..."
            self.btn_scan_1.disabled = True
            self.status_1.text = "[ 1호기 ]\n상태: 🟡 탐색 진행 중"
            self.ble_manager.scan_for_device(target_name, 
                lambda name, mac: self.on_scan_success(1, name, mac), 
                lambda err: self.on_scan_fail(1, err))
        elif device_id == 2:
            self.btn_scan_2.text = "🔄 탐색 중..."
            self.btn_scan_2.disabled = True
            self.status_2.text = "[ 2호기 ]\n상태: 🟡 탐색 진행 중"
            self.ble_manager.scan_for_device(target_name, 
                lambda name, mac: self.on_scan_success(2, name, mac), 
                lambda err: self.on_scan_fail(2, err))

    def on_scan_success(self, device_id, device_name, mac_address):
        self.ble_manager.stop_scan()
        if device_id == 1:
            self.status_1.text = f"[ 1호기 ({device_name}) ]\n상태: 🟢 연결됨\nMAC: {mac_address}"
            self.btn_scan_1.text = "🔍 다시 탐색"
            self.btn_scan_1.disabled = False
        elif device_id == 2:
            self.status_2.text = f"[ 2호기 ({device_name}) ]\n상태: 🟢 연결됨\nMAC: {mac_address}"
            self.btn_scan_2.text = "🔍 다시 탐색"
            self.btn_scan_2.disabled = False
        self.device_val.text = "1 / 2"
        self.device_val.color = (0.1, 0.6, 0.1, 1)

    def on_scan_fail(self, device_id, error_msg):
        if device_id == 1:
            self.status_1.text = f"[ 1호기 ] 스캔 제한됨\n({error_msg})"
            self.btn_scan_1.text = "🔍 재탐색"
            self.btn_scan_1.disabled = False
        elif device_id == 2:
            self.status_2.text = f"[ 2호기 ] 스캔 제한됨\n({error_msg})"
            self.btn_scan_2.text = "🔍 재탐색"
            self.btn_scan_2.disabled = False

    def close_commander_room(self, instance):
        self.ble_manager.stop_scan()
        self.commander_layer.opacity = 0
        self.commander_layer.disabled = True
        self.main_layer.disabled = False

    def disconnect_devices(self, instance):
        self.ble_manager.stop_scan()
        self.status_1.text = "[ 1호기 (Cycplus C3) ]\n상태: 🔴 연결 끊김"
        self.status_2.text = "[ 2호기 (Cycplus C3) ]\n상태: 🔴 연결 끊김"
        self.btn_scan_1.text = "🔍 1호기 장치 탐색"
        self.btn_scan_2.text = "🔍 2호기 탐색"
        self.device_val.text = "0 / 2"
        self.device_val.color = (0.8, 0.1, 0.1, 1)


class Factory4MasterApp(App):
    def build(self):
        Window.clearcolor = (0.95, 0.94, 0.90, 1) 
        return MasterCoreEngine()

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.BLUETOOTH, Permission.BLUETOOTH_ADMIN,
                    Permission.BLUETOOTH_CONNECT, Permission.BLUETOOTH_SCAN,
                    Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION
                ])
            except Exception as e: print(e)

if __name__ == '__main__':
    Factory4MasterApp().run()
