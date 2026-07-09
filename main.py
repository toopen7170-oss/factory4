import os
import math
import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle, Line
from kivy.utils import platform
from kivy.core.audio import SoundLoader

# =========================================================
# 🌍 [글로벌 다국어 폰트 및 UI 텍스트 동적 변환 프로토콜]
# =========================================================
LANGUAGE_FONTS = {
    'ko': 'font/korean.ttf',
    'en': 'Roboto',
    'zh': 'font/chinese.ttf',
    'ja': 'font/japanese.ttf'
}

TRANSLATIONS = {
    'ko': {
        'title': "팩토리4 메타버스 가상 사이클링",
        'login': "로그인 (로드게임)", 'register': "회원가입 (새게임)",
        'mode_1p': "1인 모드 (전체화면)", 'mode_2p': "2인 모드 (화면분할)",
        'speed': "속도", 'distance': "거리", 'points': "보유 포인트",
        'booster': "🚀 부스터 활성화!", 'control_room': "⚙️ 지휘관 통제실",
        'unlock_map': "🔓 맵 해금", 'buy_bike': "🚲 자전거 구매",
        'lang_switch': "🌐 언어 변경 (KO/EN)"
    },
    'en': {
        'title': "FACTORY4 METAVERSE CYCLING",
        'login': "Login (Load Game)", 'register': "Register (New Game)",
        'mode_1p': "1P Mode (Full)", 'mode_2p': "2P Mode (Split)",
        'speed': "SPEED", 'distance': "DIST", 'points': "POINTS",
        'booster': "🚀 BOOSTER ACTIVE!", 'control_room': "⚙️ COMMAND CENTER",
        'unlock_map': "🔓 Unlock Map", 'buy_bike': "🚲 Buy Vehicle",
        'lang_switch': "🌐 Change Language (EN/KO)"
    }
}

CURRENT_LANG_CODE = 'ko'
SAFE_FONT = 'Roboto'

# Android 및 로컬 폰트 강제 직렬 바인딩
for lang, path in LANGUAGE_FONTS.items():
    if path != 'Roboto':
        try:
            LabelBase.register(name=f'custom_{lang}', fn_regular=path)
            if lang == CURRENT_LANG_CODE:
                SAFE_FONT = f'custom_{lang}'
        except Exception:
            pass

# =========================================================
# 💾 [로컬 무결성 데이터베이스 관리 아키텍처]
# =========================================================
class DatabaseManager:
    def __init__(self):
        self.db_path = "factory4_core.db"
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                points INTEGER DEFAULT 0,
                unlocked_maps TEXT DEFAULT '1',
                unlocked_bikes TEXT DEFAULT '0',
                current_bike INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def register_user(self, username, password):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, points) VALUES (?, ?, 0)", (username, password))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def load_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT points, unlocked_maps, unlocked_bikes, current_bike FROM users WHERE username=? AND password=?", (username, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'points': row[0],
                'maps': [int(x) for x in row[1].split(',')],
                'bikes': [int(x) for x in row[2].split(',')],
                'current_bike': row[3]
            }
        return None

    def save_user_data(self, username, points, maps, bikes, current_bike):
        if not username: return
        maps_str = ",".join(map(str, maps))
        bikes_str = ",".join(map(str, bikes))
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET points=?, unlocked_maps=?, unlocked_bikes=?, current_bike=? 
            WHERE username=?
        ''', (points, maps_str, bikes_str, current_bike, username))
        conn.commit()
        conn.close()

# =========================================================
# 📡 [하드웨어 블루투스 GATT 알림 수신 프로토콜]
# =========================================================
if platform == 'android':
    from jnius import autoclass, PythonJavaClass, java_method
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    UUID = autoclass('java.util.UUID')

    class AndroidBLEBridge:
        def __init__(self, update_cb):
            self.update_cb = update_cb
            self.adapter = BluetoothAdapter.getDefaultAdapter()
            self.gatt = None

        def start_connection(self, mac_address):
            if not self.adapter: return
            device = self.adapter.getRemoteDevice(mac_address)
            # GATT 프로토콜 연결 체계 활성화
            self.gatt = device.connectGatt(None, False, BLEGattCallback(self.update_cb))

    class BLEGattCallback(PythonJavaClass):
        __javainterfaces__ = ['android/bluetooth/BluetoothGattCallback']
        __javacontext__ = 'app'
        def __init__(self, update_cb):
            super(BLEGattCallback, self).__init__()
            self.update_cb = update_cb

        @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
        def onConnectionStateChange(self, gatt, status, newState):
            if newState == 2: # Connected
                gatt.discoverServices()

        @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
        def onServicesDiscovered(self, gatt, status):
            # CSC (Cycling Speed and Cadence) 표준 서비스 UUID 매핑
            csc_svc_uuid = UUID.fromString("00001816-0000-1000-8000-00805f9b34fb")
            csc_char_uuid = UUID.fromString("00002a5b-0000-1000-8000-00805f9b34fb")
            service = gatt.getService(csc_svc_uuid)
            if service:
                characteristic = service.getCharacteristic(csc_char_uuid)
                gatt.setCharacteristicNotification(characteristic, True)

        @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V')
        def onCharacteristicChanged(self, gatt, characteristic):
            value = characteristic.getValue()
            # 페달 회전수 raw 데이터 패킷 분석 연산
            if value and len(value) > 1:
                rpm = int(value[1]) 
                Clock.schedule_once(lambda dt: self.update_cb(rpm), 0)
else:
    class AndroidBLEBridge:
        def __init__(self, update_cb): pass
        def start_connection(self, mac_address): pass

# =========================================================
# 🎨 [가상 2.5D/3D 그래픽 및 다중 모드 뷰포트 엔진]
# =========================================================
class 주행뷰포트(FloatLayout):
    def __init__(self, 플레이어_id="1P", **kwargs):
        super(주행뷰포트, self).__init__(**kwargs)
        self.player_id = 플레이어_id
        self.track_pos = 0
        self.altitude = 0.0 # 고도 제어 변수 (근두운용)
        self.bg_color = (0.2, 0.6, 0.2, 1) # 기본 시내 도로
        
        with self.canvas.before:
            self.core_color = Color(*self.bg_color)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            Color(0.1, 0.1, 0.1, 1)
            self.road_line = Line(points=[], width=4)
            self.coin_color = Color(1, 0.8, 0, 0)
            self.coin_visual = Ellipse_Mock = Line(circle=(0, 0, 0)) # 동전
            
        self.bind(size=self.정렬, pos=self.정렬)
        
    def 정렬(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
        self.렌더링(0)

    def 맵테마변경(self, 맵번호):
        테마색상 = {
            1: (0.2, 0.6, 0.2, 1), # 시내
            2: (0.1, 0.4, 0.8, 1), # 해변
            3: (0.3, 0.2, 0.2, 1), # 동굴
            4: (0.1, 0.5, 0.3, 1), # 산길
            5: (0.5, 0.3, 0.1, 1), # 절벽
            6: (0.8, 0.7, 0.4, 1), # 사막
            7: (0.0, 0.2, 0.5, 1), # 바다속
            8: (0.5, 0.7, 0.9, 1), # 하늘속
            9: (0.1, 0.0, 0.2, 1)  # 우주속
        }
        self.bg_color = 테마색상.get(맵번호, (0.2, 0.6, 0.2, 1))
        self.core_color.rgba = self.bg_color

    def 렌더링(self, 속도):
        self.track_pos = (self.track_pos + 속도 * 5) % self.width
        # 3차원 지평선 투영 연산식 가동
        원점_x = self.pos[0] + self.width / 2
        원점_y = self.pos[1] + self.height / 2 + (self.altitude * 2)
        
        self.road_line.points = [
            self.pos[0], self.pos[1], 
            원점_x, 원점_y, 
            self.pos[0] + self.width, self.pos[1]
        ]

# =========================================================
# ⚙️ [가상 통제실 관리자 인터페이스 및 메인 레이아웃]
# =========================================================
class MasterEngineUI(FloatLayout):
    def __init__(self, **kwargs):
        super(MasterEngineUI, self).__init__(**kwargs)
        self.db = DatabaseManager()
        self.current_user = None
        self.points = 0
        self.unlocked_maps = [1]
        self.unlocked_bikes = [0]
        self.current_bike = 0 # 0:기본, 1:스노우보드, 2:할리, 3:근두운
        
        self.is_2p_mode = False
        self.bike_speeds = {0: 1.0, 1: 1.2, 2: 1.5, 3: 2.0}
        self.map_costs = {1:0, 2:500, 3:1000, 4:2000, 5:4000, 6:8000, 7:8000, 8:16000, 9:30000}
        self.bike_costs = {1:5000, 2:10000, 3:30000}
        
        self.p1_speed = 0.0
        self.p2_speed = 0.0
        self.active_map = 1
        self.booster_timer = 0
        self.coin_timer = 0
        
        self.ble_bridge = AndroidBLEBridge(self.블루투스_RPM_수신)
        
        # 주크박스 리스트 파일 탐색 파이프라인
        self.music_list = []
        self.sound_handle = None
        self.음악폴더스캔()

        # UI 언어 초기화
        self.strings = TRANSLATIONS[CURRENT_LANG_CODE]
        
        # 아키텍처 레이아웃 구성
        self.화면빌드_로그인()

    def 음악폴더스캔(self):
        경로 = "/sdcard/Download/음악리스트폴더/"
        if os.path.exists(경로):
            self.music_list = [os.path.join(경로, f) for f in os.listdir(경로) if f.endswith('.mp3')]

    def 음악재생(self, 파일경로):
        if self.sound_handle: self.sound_handle.stop()
        self.sound_handle = SoundLoader.load(파일경로)
        if self.sound_handle: self.sound_handle.play()

    def 블루투스_RPM_수신(self, rpm):
        # RPM 기반 실제 주행 가속 속도 연산 제어 매트릭스
        배율 = self.bike_speeds.get(self.current_bike, 1.0)
        if self.booster_timer > 0: 배율 *= 2.0
        self.p1_speed = (rpm * 0.2) * 배율

    def 화면빌드_로그인(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(text=self.strings['title'], font_name=SAFE_FONT, font_size='32sp', bold=True)
        self.id_input = TextInput(hint_text="ID", text="factory_boss", size_hint_y=0.15, multiline=False)
        self.pw_input = TextInput(hint_text="PASSWORD", text="1234", password=True, size_hint_y=0.15, multiline=False)
        
        btn_login = Button(text=self.strings['login'], font_name=SAFE_FONT, size_hint_y=0.15, background_color=(0.1, 0.6, 0.2, 1))
        btn_reg = Button(text=self.strings['register'], font_name=SAFE_FONT, size_hint_y=0.15, background_color=(0.2, 0.4, 0.8, 1))
        
        btn_login.bind(on_press=self.프로토콜_로그인)
        btn_reg.bind(on_press=self.프로토콜_회원가입)
        
        layout.add_widget(title)
        layout.add_widget(self.id_input)
        layout.add_widget(self.pw_input)
        layout.add_widget(btn_login)
        layout.add_widget(btn_reg)
        self.add_widget(layout)

    def 프로토콜_회원가입(self, instance):
        if self.db.register_user(self.id_input.text, self.pw_input.text):
            self.id_input.text = "회원가입 성공! 로그인 해주십시오."
        else:
            self.id_input.text = "이미 존재하는 계정입니다."

    def 프로토콜_로그인(self, instance):
        data = self.db.load_user(self.id_input.text, self.pw_input.text)
        if data:
            self.current_user = self.id_input.text
            self.points = data['points']
            self.unlocked_maps = data['maps']
            self.unlocked_bikes = data['bikes']
            self.current_bike = data['current_bike']
            self.화면빌드_모드선택()
        else:
            self.id_input.text = "계정 정보가 일치하지 않습니다."

    def 화면빌드_모드선택(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=100, spacing=30)
        
        btn_1p = Button(text=self.strings['mode_1p'], font_name=SAFE_FONT, font_size='24sp', background_color=(0.1, 0.5, 0.8, 1))
        btn_2p = Button(text=self.strings['mode_2p'], font_name=SAFE_FONT, font_size='24sp', background_color=(0.5, 0.3, 0.8, 1))
        
        btn_1p.bind(on_press=lambda x: self.게임엔진가동(False))
        btn_2p.bind(on_press=lambda x: self.게임엔진가동(True))
        
        layout.add_widget(btn_1p)
        layout.add_widget(btn_2p)
        self.add_widget(layout)

    def 게임엔진가동(self, 모드분기):
        self.is_2p_mode = 모드분기
        self.clear_widgets()
        
        # [레이어 1] 주행 스크린 파이프라인 분기
        self.game_layout = BoxLayout(orientation='horizontal' if 모드분기 else 'vertical')
        self.view_1p = 주행뷰포트(플레이어_id="1P")
        self.game_layout.add_widget(self.view_1p)
        
        if self.is_2p_mode:
            self.view_2p = 주행뷰포트(플레이어_id="2P")
            self.game_layout.add_widget(self.view_2p)
            
        self.add_widget(self.game_layout)
        
        # [레이어 2] 대시보드 오버레이 UI
        self.hud = FloatLayout()
        self.lbl_stats = Label(
            text=f"{self.strings['speed']}: 0.0 km/h | {self.strings['points']}: {self.points}",
            font_name=SAFE_FONT, font_size='18sp', pos_hint={'center_x': 0.5, 'center_y': 0.9}
        )
        self.hud.add_widget(self.lbl_stats)
        
        # 고도 제어 인터페이스 (근두운 기체 전용 수동 업/다운 제어 패널)
        self.ctrl_panel = BoxLayout(orientation='horizontal', size_hint=(0.3, 0.12), pos_hint={'center_x': 0.5, 'center_y': 0.15})
        btn_up = Button(text="▲ UP", font_size='18sp', background_color=(0,0,0,0.5))
        btn_down = Button(text="▼ DOWN", font_size='18sp', background_color=(0,0,0,0.5))
        btn_up.bind(on_press=self.고도상승)
        btn_down.bind(on_press=self.고도하강)
        self.ctrl_panel.add_widget(btn_up)
        self.ctrl_panel.add_widget(btn_down)
        self.hud.add_widget(self.ctrl_panel)
        
        # 비밀 지휘관 화면 진입점 버튼 (우측 상단 락인)
        btn_secret = Button(text=self.strings['control_room'], font_name=SAFE_FONT, size_hint=(0.15, 0.08), pos_hint={'x': 0.85, 'y': 0.92})
        btn_secret.bind(on_press=self.화면빌드_지휘관통제실)
        self.hud.add_widget(btn_secret)
        
        self.add_widget(self.hud)
        
        # 시뮬레이션 및 데이터 오토 세이브 타이머 스케줄러 등록
        Clock.schedule_interval(self.메인엔진동기화루프, 0.1)

    def 고도상승(self, instance):
        if self.current_bike == 3: # 오직 근두운 장착 시에만 한글 제어 가동
            self.view_1p.altitude = min(100.0, self.view_1p.altitude + 5.0)

    def 고도하강(self, instance):
        if self.current_bike == 3:
            self.view_1p.altitude = max(0.0, self.view_1p.altitude - 5.0)

    def 메인엔진동기화루프(self, dt):
        # 페달 정지 상태 검증 (자전거를 멈추면 맵과 연산 정지 스펙 구현)
        if self.p1_speed == 0 and platform == 'android':
            return
            
        # 가상 주행 시뮬레이션 모드 데이터 공급 (물리 센서 미연결 대비)
        if self.p1_speed == 0:
            self.p1_speed = 15.0 + 5.0 * math.sin(Clock.get_time() * 0.5)

        # 10초 주기 동전 및 10분 주기 부스터 동기화 타이머 연산
        self.coin_timer += dt
        self.booster_timer += dt
        
        if self.coin_timer >= 10.0:
            획득포인트 = 2 if self.is_2p_mode else 1
            self.points += 획득포인트
            self.coin_timer = 0
            # 백그라운드 실시간 강제 저장 프로토콜 작동
            self.db.save_user_data(self.current_user, self.points, self.unlocked_maps, self.unlocked_bikes, self.current_bike)

        self.view_1p.맵테마변경(self.active_map)
        self.view_1p.렌더링(self.p1_speed)
        
        if self.is_2p_mode:
            self.view_2p.맵테마변경(self.active_map)
            self.view_2p.렌더링(self.p1_speed)
            
        self.lbl_stats.text = f"{self.strings['speed']}: {self.p1_speed:.1f} km/h | {self.strings['points']}: {self.points}"

    def 화면빌드_지휘관통제실(self, instance):
        Clock.unschedule(self.메인엔진동기화루프)
        self.clear_widgets()
        
        scroll = ScrollView(size_hint=(1, 1))
        container = GridLayout(cols=1, spacing=20, size_hint_y=None, padding=30)
        container.bind(minimum_height=container.setter('height'))
        
        # 1. 언어 변환 센터 스위치
        btn_lang = Button(text=self.strings['lang_switch'], font_name=SAFE_FONT, size_hint_y=None, height=60, background_color=(0.1,0.5,0.6,1))
        btn_lang.bind(on_press=self.인터페이스_언어교체)
        container.add_widget(btn_lang)
        
        # 2. 9단계 무대(맵) 콘텐츠 해금 매트릭스 센터
        container.add_widget(Label(text="🏞️ CONTENT MAP EXPANSION MATRIX", font_size='18sp', bold=True, size_hint_y=None, height=40))
        for m_id, cost in self.map_costs.items():
            상태 = "ACTIVE" if m_id in self.unlocked_maps else f"LOCKED ({cost} P)"
            btn = Button(text=f"STAGE {m_id} MAP : {상태}", font_name=SAFE_FONT, size_hint_y=None, height=50)
            btn.bind(on_press=lambda x, idx=m_id: self.인터페이스_맵해금(idx))
            container.add_widget(btn)
            
        # 3. 3단계 가상 기체 기획 상점 인터페이스
        container.add_widget(Label(text="🚲 VEHICLE SPEED UPGRADE ENGINE", font_size='18sp', bold=True, size_hint_y=None, height=40))
        기체이름 = {1: "스노우보드 기체 (+1 가속, 50cm 부유)", 2: "할리 오토바이 (+2 가속, 터미네이터 사양)", 3: "근두운 자전거 (+3 가속, 고도자율제어)"}
        for b_id, cost in self.bike_costs.items():
            상태 = "OWNED" if b_id in self.unlocked_bikes else f"BUY ({cost} P)"
            btn = Button(text=f"{기체이름[b_id]} : {상태}", font_name=SAFE_FONT, size_hint_y=None, height=50)
            btn.bind(on_press=lambda x, idx=b_id: self.인터페이스_기체구매(idx))
            container.add_widget(btn)

        # 4. 스마트 주크박스 음악 파일 오디오 스트리밍 리스트 리로드
        container.add_widget(Label(text="🎵 SMART AUDIO JUKEBOX LIST", font_size='18sp', bold=True, size_hint_y=None, height=40))
        for music in self.music_list:
            btn_m = Button(text=os.path.basename(music), size_hint_y=None, height=40, background_color=(0.3,0.3,0.3,1))
            btn_m.bind(on_press=lambda x, path=music: self.음악재생(path))
            container.add_widget(btn_m)

        # 복귀 스위치
        btn_close = Button(text="💾 SAVE & EXIT", size_hint_y=None, height=60, background_color=(0.8, 0.2, 0.2, 1))
        btn_close.bind(on_press=lambda x: self.게임엔진가동(self.is_2p_mode))
        container.add_widget(btn_close)
        
        scroll.add_widget(container)
        self.add_widget(scroll)

    def 인터페이스_언어교체(self, instance):
        global CURRENT_LANG_CODE, SAFE_FONT
        CURRENT_LANG_CODE = 'en' if CURRENT_LANG_CODE == 'ko' else 'ko'
        self.strings = TRANSLATIONS[CURRENT_LANG_CODE]
        SAFE_FONT = f'custom_{CURRENT_LANG_CODE}' if f'custom_{CURRENT_LANG_CODE}' in LabelBase._fonts else 'Roboto'
        self.화면빌드_지휘관통제실(None)

    def 인터페이스_맵해금(self, 맵번호):
        if 맵번호 in self.unlocked_maps:
            self.active_map = 맵번호
            return
        비용 = self.map_costs[맵번호]
        if self.points >= 비용:
            self.points -= 비용
            self.unlocked_maps.append(맵번호)
            self.active_map = 맵번호
            self.db.save_user_data(self.current_user, self.points, self.unlocked_maps, self.unlocked_bikes, self.current_bike)
            self.화면빌드_지휘관통제실(None)

    def 인터페이스_기체구매(self, 기체번호):
        if 기체번호 in self.unlocked_bikes:
            self.current_bike = 기체번호
            self.db.save_user_data(self.current_user, self.points, self.unlocked_maps, self.unlocked_bikes, self.current_bike)
            return
        비용 = self.bike_costs[기체번호]
        if self.points >= 비용:
            self.points -= 비용
            self.unlocked_bikes.append(기체번호)
            self.current_bike = 기체번호
            self.db.save_user_data(self.current_user, self.points, self.unlocked_maps, self.unlocked_bikes, self.current_bike)
            self.화면빌드_지휘관통제실(None)

class Factory4MasterApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.05, 1)
        return MasterEngineUI()

if __name__ == '__main__':
    Factory4MasterApp().run()
