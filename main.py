import os
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import platform

# 안드로이드 권한 요청 (앱 실행 시)
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE, 
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.BLUETOOTH_CONNECT,
        Permission.BLUETOOTH_SCAN,
        Permission.ACCESS_FINE_LOCATION
    ])

class MasterCoreEngine(FloatLayout):
    def __init__(self, **kwargs):
        super(MasterCoreEngine, self).__init__(**kwargs)
        self.secret_tap_count = 0
        self.last_tap_time = 0
        
        # 기본 제어 매트릭스 변수 초기화
        self.app_title = "실내 사이클 메타버스"
        self.coin_interval = 10
        self.booster_condition = 10
        self.npc_count = 50
        
        # 스마트폰 내부 통제실 물리 경로 세팅
        self.control_dir = "/sdcard/Download/factory/factory2"
        self.control_path = os.path.join(self.control_dir, "control.txt")
        
        # 1. 메인 구동 화면 레이아웃
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.title_label = Label(text=self.app_title, font_size='30sp', size_hint=(1, 0.2))
        self.status_label = Label(text="자전거 1, 2호기 무선 연결 대기 중...\n페달을 밟으면 연동이 시작됩니다.", font_size='18sp')
        
        self.main_layout.add_widget(self.title_label)
        self.main_layout.add_widget(self.status_label)
        self.add_widget(self.main_layout)
        
        # 2. 비밀 지휘관 화면 레이아웃 (최초 숨김)
        self.secret_panel = BoxLayout(orientation='vertical', padding=30, spacing=15, size_hint=(0.8, 0.9), pos_hint={'x': 0.1, 'y': 0.05})
        self.setup_secret_ui()
        
        # 3. 우측 상단 투명 터치 센서 트랙커 바인딩
        self.secret_trigger = Button(size_hint=(0.15, 0.15), pos_hint={'x': 0.85, 'y': 0.85}, background_color=(0,0,0,0))
        self.secret_trigger.bind(on_press=self.process_secret_tap)
        self.add_widget(self.secret_trigger)
        
        # 로컬 파일 자동 감시 서브루틴 가동 (2초 주기)
        Clock.schedule_interval(self.auto_file_watcher, 2.0)

    def setup_secret_ui(self):
        self.secret_panel.add_widget(Label(text="🟢 스마트폰 단독 지휘 통제실 (v1.0)", font_size='24sp', color=(0, 1, 0, 1)))
        
        self.secret_panel.add_widget(Label(text="앱 이름 변경", font_size='16sp'))
        self.input_title = TextInput(text=self.app_title, multiline=False, size_hint=(1, 0.4))
        self.secret_panel.add_widget(self.input_title)
        
        self.secret_panel.add_widget(Label(text="동전 생성 간격 (초)", font_size='16sp'))
        self.slider_coin = Slider(min=1, max=60, value=self.coin_interval)
        self.secret_panel.add_widget(self.slider_coin)
        
        self.secret_panel.add_widget(Label(text="고스트 NPC 인원수 (명)", font_size='16sp'))
        self.slider_npc = Slider(min=0, max=100, value=self.npc_count)
        self.secret_panel.add_widget(self.slider_npc)
        
        btn_save = Button(text="설정 저장 및 즉시 적용", size_hint=(1, 0.6), background_color=(0, 0.5, 1, 1))
        btn_save.bind(on_press=self.save_config_from_ui)
        self.secret_panel.add_widget(btn_save)

    def process_secret_tap(self, instance):
        current_time = time.time()
        if current_time - self.last_tap_time > 1.5:
            self.secret_tap_count = 0
            
        self.secret_tap_count += 1
        self.last_tap_time = current_time
        
        if self.secret_tap_count >= 5:
            self.secret_tap_count = 0
            self.open_loading_animation()

    def open_loading_animation(self):
        self.loading_label = Label(text="🏹         ❤️", font_size='40sp', pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.loading_label)
        
        Clock.schedule_once(lambda dt: setattr(self.loading_label, 'text', "🏹🎯❤️"), 0.5)
        Clock.schedule_once(lambda dt: setattr(self.loading_label, 'text', "🟢 동기화 완료!"), 1.0)
        Clock.schedule_once(self.reveal_secret_panel, 1.5)

    def reveal_secret_panel(self, dt):
        self.remove_widget(self.loading_label)
        if self.secret_panel not in self.children:
            self.add_widget(self.secret_panel)

    def save_config_from_ui(self, instance):
        self.app_title = self.input_title.text
        self.coin_interval = int(self.slider_coin.value)
        self.npc_count = int(self.slider_npc.value)
        
        try:
            if not os.path.exists(self.control_dir):
                os.makedirs(self.control_dir)
            with open(self.control_path, "w", encoding="utf-8") as f:
                f.write(f"앱 간판 = {self.app_title}\n")
                f.write(f"동전 등장 간격 = {self.coin_interval}\n")
                f.write(f"고스트 NPC 주행 인원 = {self.npc_count}\n")
        except Exception as e:
            self.status_label.text = f"저장 실패: 권한을 확인하세요.\n{e}"
            return
            
        self.title_label.text = self.app_title
        self.status_label.text = f"규칙 변경 전착 완료\n동전 주기: {self.coin_interval}초 | 경쟁자: {self.npc_count}명"
        self.remove_widget(self.secret_panel)

    def auto_file_watcher(self, dt):
        if os.path.exists(self.control_path):
            try:
                with open(self.control_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        if "=" in line:
                            key, val = line.split("=")
                            key = key.strip()
                            val = val.strip()
                            if key == "앱 간판":
                                self.app_title = val
                                self.title_label.text = val
                            elif key == "동전 등장 간격":
                                self.coin_interval = int(val)
                            elif key == "고스트 NPC 주행 인원":
                                self.npc_count = int(val)
            except Exception as e:
                pass

class Factory4MasterApp(App):
    def build(self):
        font_path = 'font/NanumGothic.ttf'
        if os.path.exists(font_path):
            LabelBase.register(name='Roboto', fn_regular=font_path)
            
        Window.clearcolor = (0.05, 0.05, 0.1, 1)
        return MasterCoreEngine()

if __name__ == '__main__':
    Factory4MasterApp().run()
