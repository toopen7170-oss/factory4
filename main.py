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

# 💡 [엔진 최적화] 안드로이드 시스템 내부에서 외국어 글꼴이 깨지는 현상을 방지하기 위한 전역 네임스페이스 명시적 바인딩
font_files = {
    'ko_font': 'font/korean.ttf',
    'en_font': 'font/global.ttf',
    'zh_font': 'font/chinese.ttf',
    'ja_font': 'font/japanese.ttf',
    'ar_font': 'font/arabic.ttf',
    'th_font': 'font/thai.ttf'
}

for font_name, font_path in font_files.items():
    if os.path.exists(font_path):
        LabelBase.register(name=font_name, fn_regular=font_path)

if platform == 'android':
    from android.permissions import request_permissions, Permission
    # 기기 내부 미디어 주크박스 스캔 및 블루투스 케이던스 센서 수신을 위한 하드웨어 권한 획득
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
        
        # 각 언어 코드별 전역 폰트 식별자 매핑
        self.font_map = {
            'ko': 'ko_font' if os.path.exists('font/korean.ttf') else 'Roboto',
            'en': 'en_font' if os.path.exists('font/global.ttf') else 'Roboto',
            'zh': 'zh_font' if os.path.exists('font/chinese.ttf') else 'Roboto',
            'ja': 'ja_font' if os.path.exists('font/japanese.ttf') else 'Roboto',
            'ar': 'ar_font' if os.path.exists('font/arabic.ttf') else 'Roboto',
            'th': 'th_font' if os.path.exists('font/thai.ttf') else 'Roboto'
        }
        
        self.current_lang = 'ko'
        
        # 100% 로컬 프라이버시 보호 장벽 조성을 위한 영구 데이터 저장소 디렉터리 검증
        self.control_dir = "/sdcard/Download/factory/factory4"
        if not os.path.exists(self.control_dir):
            try:
                os.makedirs(self.control_dir)
            except Exception:
                pass
                
        self.control_path = os.path.join(self.control_dir, "control.txt")
        
        # UI 레이아웃 충돌 방어 원칙 수립 (데이터 표시창 고정 분리 벽)
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 💡 [프리미엄 UI 개편] 아이보리 바탕 위에 완벽하게 가독성을 보장하는 진하고 선명한 검은색 굵은 글씨 레이어 적용
        self.title_label = Label(
            text=self.app_title, 
            font_size='34sp', 
            font_name=self.font_map[self.current_lang], 
            size_hint=(1, 0.2),
            color=(0, 0, 0, 1),
            bold=True
        )
        self.main_layout.add_widget(self.title_label)
        
        # 💡 [프리미엄 UI 개편] 기본 어두운 텍스처를 걷어내고 소프트 베이지-아이보리 톤의 버튼 배경과 고대비 굵은 글씨 컴포넌트 이식
        self.lang_test_btn = Button(
            text="언어 변경 테스트 (Tap)",
            font_name=self.font_map['ko'],
            size_hint=(1, 0.1),
            color=(0, 0, 0, 1),
            bold=True,
            background_normal='',
            background_color=(0.88, 0.88, 0.83, 1)
        )
        self.lang_test_btn.bind(on_press=self.change_language_logic)
        self.main_layout.add_widget(self.lang_test_btn)
        
        self.add_widget(self.main_layout)

    def change_language_logic(self, instance):
        """실시간 무빌드 다국어 리로드 및 폰트 강제 매핑 동기화 시스템"""
        lang_keys = list(self.font_map.keys())
        current_idx = lang_keys.index(self.current_lang)
        next_idx = (current_idx + 1) % len(lang_keys)
        self.current_lang = lang_keys[next_idx]
        
        new_font = self.font_map[self.current_lang]
        self.title_label.font_name = new_font
        self.lang_test_btn.font_name = new_font
        
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
            
        # 💡 [프리미엄 UI 개편] 눈의 피로감을 차단하고 시인성을 최고 등급으로 끌어올리는 고품격 소프트 아이보리(Ivory) 전면 스크린 도색
        Window.clearcolor = (0.98, 0.98, 0.94, 1)
        Window.softinput_mode = 'below_target'
        
        return MasterCoreEngine()

if __name__ == '__main__':
    Factory4MasterApp().run()
