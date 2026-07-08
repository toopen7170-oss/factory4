import os, time
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

if platform == 'android':
    from android.permissions import request_permissions, Permission
    # 스마트폰 내부 저장소 및 1호/2호기 자전거 블루투스 연결을 위한 통합 권한 장전
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE, 
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.BLUETOOTH,
        Permission.BLUETOOTH_CONNECT,
        Permission.BLUETOOTH_SCAN,
        Permission.ACCESS_FINE_LOCATION
    ])

class MasterCoreEngine(FloatLayout):
    def __init__(self, **kwargs):
        super(MasterCoreEngine, self).__init__(**kwargs)
        self.secret_tap_count = 0
        self.last_tap_time = 0
        self.app_title = "실내 사이클 메타버스"
        
        # 100% 로컬 구동 원칙: 스마트폰 내부 통제 구역 설정
        self.control_dir = "/sdcard/Download/factory/factory4"
        if not os.path.exists(self.control_dir):
            try:
                os.makedirs(self.control_dir)
            except Exception:
                pass
                
        self.control_path = os.path.join(self.control_dir, "control.txt")
        
        # 상단 영역: UI 충돌 방어 원칙 적용 (고정 레이아웃)
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.title_label = Label(
            text=self.app_title, 
            font_size='30sp', 
            font_name='Roboto', 
            size_hint=(1, 0.2)
        )
        self.main_layout.add_widget(self.title_label)
        
        self.add_widget(self.main_layout)

class Factory4MasterApp(App):
    def build(self):
        # 초미세 폰트 강제 결속 (한글 깨짐 원천 방어)
        font_path = 'assets/font.ttf'
        if os.path.exists(font_path):
            LabelBase.register(name='Roboto', fn_regular=font_path)
            
        # UI 레이아웃 붕괴 방어선 락인 (키보드 및 배경)
        Window.clearcolor = (0.05, 0.05, 0.1, 1)
        Window.softinput_mode = 'below_target'
        
        return MasterCoreEngine()

if __name__ == '__main__':
    Factory4MasterApp().run()
