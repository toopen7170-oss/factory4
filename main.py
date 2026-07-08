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
        
        self.current_lang = 'ko'
        
        # 100% 로컬 구동 원칙: 스마트폰 내부 통제 구역 설정
        self.control_dir = "/sdcard/Download/factory/factory4"
        if not os.path.exists(self.control_dir):
            try:
                os.makedirs(self.control_dir)
            except Exception:
                pass
                
        self.control_path = os.path.join(self.control_dir, "control.txt")
        
        # 상단 영역: UI 충돌 방어 원칙 적용
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.title_label = Label(
            text=self.app_title, 
            font_size='30sp', 
            font_name=self.font_map[self.current_lang], 
            size_hint=(1, 0.2)
        )
        self.main_layout.add_widget(self.title_label)
        
        self.lang_test_btn = Button(
            text="언어 변경 테스트 (Tap)",
            font_name=self.font_map['ko'],
            size_hint=(1, 0.1)
        )
        self.lang_test_btn.bind(on_press=self.change_language_logic)
        self.main_layout.add_widget(self.lang_test_btn)
        
        self.add_widget(self.main_layout)

    def change_language_logic(self, instance):
        lang_keys = list(self.font_map.keys())
        current_idx = lang_keys.index(self.current_lang)
        next_idx = (current_idx + 1) % len(lang_keys)
        self.current_lang = lang_keys[next_idx]
        
        new_font_path = self.font_map[self.current_lang]
        self.title_label.font_name = new_font_path
        self.lang_test_btn.font_name = new_font_path
        
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
        default_font_path = 'font/korean.ttf'
        if os.path.exists(default_font_path):
            LabelBase.register(name='Roboto', fn_regular=default_font_path)
            
        Window.clearcolor = (0.05, 0.05, 0.1, 1)
        Window.softinput_mode = 'below_target'
        
        return MasterCoreEngine()

    def on_start(self):
        # 💡 [버그 픽스] 앱 화면이 렌더링된 이후에 권한을 요청하여 블랙스크린 프리징 방지
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, 
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.BLUETOOTH,
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_SCAN,
                Permission.ACCESS_FINE_LOCATION
            ])

if __name__ == '__main__':
    Factory4MasterApp().run()
