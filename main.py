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
    
    # [3단계] 블루투스 스캔 통신병
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
            if name:
                self.on_device_found(name, address)

    # [4단계 신규] GATT 통신병 (데이터 수신 터널)
    class BLEGattCallback(PythonJavaClass):
        __javainterfaces__ = ['android/bluetooth/BluetoothGattCallback']
        __javacontext__ = 'app'

        def __init__(self, app_logic, **kwargs):
            super().__init__(**kwargs)
            self.app_logic = app_logic

        @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
        def onConnectionStateChange(self, gatt, status, newState):
            if newState == 2: # STATE_CONNECTED
                self.app_logic.on_gatt_connected(gatt)
            elif newState == 0: # STATE_DISCONNECTED
                self.app_logic.on_gatt_disconnected()

        @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
        def onServicesDiscovered(self, gatt, status):
            if status == 0: # GATT_SUCCESS
                self.app_logic.on_services_discovered(gatt)

        @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V')
        def onCharacteristicChanged(self, gatt, characteristic):
            value = characteristic.getValue()
            self.app_logic.on_data_received(value)
            
        @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V')
        def onDescriptorWrite(self, gatt, descriptor, status):
            pass

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
    except: pass 
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_handler

# ---------------------------------------------------------
# 3. 메인 앱 화면 및 통제 로직
# ---------------------------------------------------------
class MetaRiderMainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        self.last_video_count = -1
        self.found_devices = {}
        
        # RPM 계산용 이전 데이터 저장소
        self.prev_crank_rev = -1
        self.prev_crank_time = -1
        
        # [상단] 시스템 상태창
        self.status_label = Label(
            text="[System Booting]\nRequesting Permissions...",
            font_size='16sp', halign='center', size_hint_y=0.2
        )
        self.add_widget(self.status_label)

        # [신규] RPM(케이던스) 실시간 계기판
        self.rpm_label = Label(
            text="RPM: 0",
            font_size='50sp', color=(0, 1, 1, 1), bold=True, size_hint_y=0.2
        )
        self.add_widget(self.rpm_label)
        
        # [중단] 블루투스 기기 리스트
        self.scroll_view = ScrollView(size_hint_y=0.4)
        self.device_list_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.device_list_layout.bind(minimum_height=self.device_list_layout.setter('height'))
        self.scroll_view.add_widget(self.device_list_layout)
        self.add_widget(self.scroll_view)
        
        # [하단] 블루투스 스캔 버튼
        self.scan_btn = Button(
            text="블루투스 기기 찾기 (스캔 시작)",
            size_hint_y=0.2, background_color=(0.2, 0.6, 1, 1), disabled=True
        )
        self.scan_btn.bind(on_press=self.toggle_scan)
        self.add_widget(self.scan_btn)

        Clock.schedule_once(self.start_initialization, 1)

    # ------------------ (인프라 및 권한 로직 유지) ------------------
    def start_initialization(self, dt):
        if platform == 'android':
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE,
                Permission.BLUETOOTH_SCAN, Permission.BLUETOOTH_CONNECT, Permission.ACCESS_FINE_LOCATION
            ], self.on_permissions_result)
        else: self.setup_infrastructure()

    def on_permissions_result(self, permissions, grants):
        self.setup_infrastructure()

    def setup_infrastructure(self):
        target_dirs = [FACTORY_ROOT, CORE_DIR, LOG_DIR, MUSIC_DIR, VIDEO_DIR, FONT_DIR]
        try:
            for directory in target_dirs:
                if not os.path.exists(directory): os.makedirs(directory)
            test_file = os.path.join(FACTORY_ROOT, 'permission_test.txt')
            with open(test_file, 'w') as f: f.write('ok')
            os.remove(test_file)
        except Exception as e:
            self.status_label.text = "[Error] 권한 오류. 앱 설정에서 권한을 모두 허용하세요."
            self.status_label.color = (1, 0.2, 0.2, 1)
            return

        self.register_fonts()
        self.scan_resources()
        self.scan_btn.disabled = False

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
            self.rpm_label.font_name = DEFAULT_FONT

        for font_name, file_name in font_mapping.items():
            font_path = os.path.join(FONT_DIR, file_name)
            if os.path.exists(font_path): LabelBase.register(name=font_name, fn_regular=font_path)
            elif os.path.exists(universal_font): LabelBase.register(name=font_name, fn_regular=universal_font)

    def scan_resources(self):
        self.status_label.text = "[시스템 및 인프라 정상]\n아래 버튼을 눌러 센서를 스캔하세요."
        self.status_label.color = (0.2, 1, 0.2, 1)

    # ------------------ (블루투스 스캔 로직 유지) ------------------
    def toggle_scan(self, instance):
        if platform != 'android': return
        if self.scan_btn.text == "블루투스 기기 찾기 (스캔 시작)":
            self.start_ble_scan()
        else:
            self.stop_ble_scan()

    def start_ble_scan(self):
        try:
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
            self.status_label.text = "CYCPLUS 센서를 찾는 중입니다...\n(페달을 돌려 센서를 깨워주세요)"
        except Exception as e:
            self.status_label.text = f"[스캔 오류]\n{str(e)}"

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
            btn = Button(
                text=f"{name}\n({address})", size_hint_y=None, height=120,
                font_name=DEFAULT_FONT, background_color=(0.3, 0.3, 0.3, 1)
            )
            btn.bind(on_press=lambda x: self.connect_device(name, address))
            self.device_list_layout.add_widget(btn)

    # ------------------ (신규: 블루투스 데이터 연결 및 파싱 로직) ------------------
    def connect_device(self, name, address):
        self.stop_ble_scan()
        self.status_label.text = f"[{name}] 연결 시도 중..."
        self.status_label.color = (1, 1, 1, 1)
        
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            device = self.bluetooth_adapter.getRemoteDevice(address)
            self.gatt_callback = BLEGattCallback(self)
            # 안드로이드 컨텍스트를 활용하여 GATT 파이프라인 오픈
            self.gatt = device.connectGatt(PythonActivity.mActivity, False, self.gatt_callback)
        except Exception as e:
            self.status_label.text = f"[연결 오류] {str(e)}"

    @mainthread
    def on_gatt_connected(self, gatt):
        self.status_label.text = "센서와 연결 성공! 데이터 서비스를 탐색합니다..."
        self.status_label.color = (0.2, 1, 0.2, 1)
        # 기기 내부의 서비스(CSC 등) 구조를 스캔하도록 명령
        gatt.discoverServices()

    @mainthread
    def on_gatt_disconnected(self):
        self.status_label.text = "센서 연결이 끊어졌습니다."
        self.status_label.color = (1, 0.2, 0.2, 1)
        self.rpm_label.text = "RPM: 0"

    @mainthread
    def on_services_discovered(self, gatt):
        try:
            UUID = autoclass('java.util.UUID')
            # 1. 자전거 속도/케이던스 표준 서비스 UUID (CSC)
            service_uuid = UUID.fromString("00001816-0000-1000-8000-00805f9b34fb")
            service = gatt.getService(service_uuid)
            
            if service:
                # 2. 케이던스 데이터 측정 특성 UUID
                char_uuid = UUID.fromString("00002a5b-0000-1000-8000-00805f9b34fb")
                characteristic = service.getCharacteristic(char_uuid)
                
                # 3. 실시간 알림 수신 켜기
                gatt.setCharacteristicNotification(characteristic, True)
                
                # 4. 센서의 스위치(CCCD)를 켜서 데이터를 쏘라고 명령
                desc_uuid = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
                descriptor = characteristic.getDescriptor(desc_uuid)
                BluetoothGattDescriptor = autoclass('android.bluetooth.BluetoothGattDescriptor')
                descriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                gatt.writeDescriptor(descriptor)
                
                self.status_label.text = "데이터 수신 채널 오픈 완료! 페달을 굴려주세요."
            else:
                self.status_label.text = "이 기기는 호환되는 자전거 센서(CSC)가 아닙니다."
                self.status_label.color = (1, 0.5, 0, 1)
        except Exception as e:
            self.status_label.text = f"[데이터 연결 오류] {str(e)}"

    @mainthread
    def on_data_received(self, value):
        # 센서가 보낸 바이트 배열(Byte Array) 암호 해독 시작
        try:
            # 안드로이드 Java Byte는 -128~127 범위이므로 0xFF 비트연산으로 양수화
            flags = value[0] & 0xFF
            has_wheel = flags & 0x01
            has_crank = flags & 0x02
            
            offset = 1
            if has_wheel:
                offset += 6 # 속도(바퀴) 데이터가 있으면 건너뜀
                
            # 케이던스(크랭크) 데이터가 포함된 경우
            if has_crank and len(value) >= offset + 4:
                # 16비트 회전수 합계 추출
                crank_rev = (value[offset] & 0xFF) | ((value[offset+1] & 0xFF) << 8)
                # 16비트 마지막 시간 추출 (1024분의 1초 단위)
                crank_time = (value[offset+2] & 0xFF) | ((value[offset+3] & 0xFF) << 8)
                
                if self.prev_crank_rev != -1:
                    # 회전수와 시간의 변화량 계산 (16비트 오버플로우 방지)
                    diff_rev = (crank_rev - self.prev_crank_rev) & 0xFFFF
                    diff_time = (crank_time - self.prev_crank_time) & 0xFFFF
                    
                    if diff_time > 0:
                        # RPM 계산: (회전수 / (시간차 / 1024)) * 60초
                        rpm = (diff_rev / (diff_time / 1024.0)) * 60.0
                        self.rpm_label.text = f"RPM: {int(rpm)}"
                        
                self.prev_crank_rev = crank_rev
                self.prev_crank_time = crank_time
                
        except Exception as e:
            pass # 초기 오류 방지용

class MetaRiderApp(App):
    def build(self):
        return MetaRiderMainLayout()

if __name__ == '__main__':
    MetaRiderApp().run()
