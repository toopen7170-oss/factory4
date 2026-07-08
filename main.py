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
        
        # 💡 [핵심 로직] 다국어 폰트 매핑 (font 폴더 내의 파일들과 연결)
        self.font_map = {
            'ko': 'font/korean.ttf',
            'en': 'font/global.ttf',
            'zh': 'font/chinese.ttf',
            'ja': 'font/japanese.ttf',
            'ar': 'font/arabic.ttf',
            'th': 'font/thai.ttf'
        }
        
        # 기본 언어 설정 (한국어)
        self.current_lang = 'ko'
        
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
        
        # 타이틀 라벨: font_name에 현재 언어의 폰트를 할당
        self.title_label = Label(
            text=self.app_title, 
            font_size='30sp', 
            font_name=self.font_map[self.current_lang], 
            size_hint=(1, 0.2)
        )
        self.main_layout.add_widget(self.title_label)
        
        # 💡 [테스트용] 언어 변경 버튼 추가
        self.lang_test_btn = Button(
            text="언어 변경 테스트 (Tap)",
            font_name=self.font_map['ko'],
            size_hint=(1, 0.1)
        )
        self.lang_test_btn.bind(on_press=self.change_language_logic)
        self.main_layout.add_widget(self.lang_test_btn)
        
        self.add_widget(self.main_layout)

    def change_language_logic(self, instance):
        """언어가 바뀔 때 폰트와 텍스트를 함께 변경해주는 로직"""
        # 다음 언어로 순환 (예시)
        lang_keys = list(self.font_map.keys())
        current_idx = lang_keys.index(self.current_lang)
        next_idx = (current_idx + 1) % len(lang_keys)
        self.current_lang = lang_keys[next_idx]
        
        # 1. 새로운 폰트 적용
        new_font_path = self.font_map[self.current_lang]
        self.title_label.font_name = new_font_path
        self.lang_test_btn.font_name = new_font_path
        
        # 2. 언어별 텍스트 적용 (실제 앱에서는 번역 파일 등에서 가져오시면 됩니다)
        if self.current_lang == 'ko':
            self.title_label.text = "실내 사이클 메타버스"
        elif self.current_lang == 'en':
            self.title_label.text = "Indoor Cycle Metaverse"
        elif self.current_lang == 'zh':
            self.title_label.text = "室内自行车元宇宙"
        elif self.current_lang == 'ja':
            self.title_label.text = "屋内サイクルメタバース"
        else:
            self.title_label.text = f"Language: {self.current_lang}"

class Factory4MasterApp(App):
    def build(self):
        # 💡 앱 전체의 기본 폰트(Roboto)를 korean.ttf로 덮어쓰기 (전역 설정)
        # 폰트를 명시적으로 지정하지 않은 위젯들은 기본적으로 한글 폰트를 따르게 됩니다.
        default_font_path = 'font/korean.ttf'
        if os.path.exists(default_font_path):
            LabelBase.register(name='Roboto', fn_regular=default_font_path)
            
        # UI 레이아웃 붕괴 방어선 락인 (키보드 및 배경)
        Window.clearcolor = (0.05, 0.05, 0.1, 1)
        Window.softinput_mode = 'below_target'
        
        return MasterCoreEngine()

if __name__ == '__main__':
    Factory4MasterApp().run()
