import os
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import platform

# 💡 [글꼴 다국어 임베딩] 전용 디렉터리 내 자산을 가상 네임스페이스에 동적 등록
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
        
        # 💡 [고대비 컴포넌트 데이터 테이블] 폰트와 매치되는 완벽한 타겟 다국어 사전 정의
        self.lang_pack = {
            'ko': {'title': "실내 사이클 메타버스", 'btn': "언어 변경 테스트 (Tap)", 'font': 'ko_font'},
            'en': {'title': "Indoor Cycle Metaverse", 'btn': "Language Change Test (Tap)", 'font': 'en_font'},
            'zh': {'title': "室内自行车元宇宙", 'btn': "语言切换测试 (Tap)", 'font': 'zh_font'},
            'ja': {'title': "屋内サイクルメタバース", 'btn': "言語変更テスト (Tap)", 'font': 'ja_font'},
            'ar': {'title': "دورة ميتافيرس الداخلية", 'btn': "اختبار تغيير اللغة (Tap)", 'font': 'ar_font'},
            'th': {'title': "อินดอร์ ไซเคิล เมตาเวิร์ส", 'btn': "ทดสอบเปลี่ยนภาษา (Tap)", 'font': 'th_font'}
        }
        
        self.lang_keys = list(self.lang_pack.keys())
        self.current_lang = 'ko'
        
        # 100% 로컬 데이터 저장소 경로 안정화 가이드라인
        self.control_dir = "/sdcard/Download/factory/factory4"
        if not os.path.exists(self.control_dir):
            try:
                os.makedirs(self.control_dir)
            except Exception:
                pass
                
        self.control_path = os.path.join(self.control_dir, "control.txt")
        
        # UI 배치 매직 미러 그리드 백본 구조화
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 초기 언어 데이터 파싱 및 안전 가속 폰트 적용
        init_data = self.lang_pack[self.current_lang]
        safe_font = init_data['font'] if os.path.exists(font_files[init_data['font']]) else 'Roboto'
        
        # [프리미엄 핏 레이블] 아이보리 캔버스용 선명도 극대화 폰트 레이어
        self.title_label = Label(
            text=init_data['title'], 
            font_size='34sp', 
            font_name=safe_font, 
            size_hint=(1, 0.2),
            color=(0, 0, 0, 1),
            bold=True
        )
        self.main_layout.add_widget(self.title_label)
        
        # [프리미엄 핏 인터랙션 컴포넌트] 고화질 소프트 베이지 버튼 아키텍처
        self.lang_test_btn = Button(
            text=init_data['btn'],
            font_name=safe_font,
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
        """실시간 메모리 데이터 캐시 로드 및 동적 리얼타임 다국어 폰트 제어 인젝터"""
        current_idx = self.lang_keys.index(self.current_lang)
        next_idx = (current_idx + 1) % len(self.lang_keys)
        self.current_lang = self.lang_keys[next_idx]
        
        target_data = self.lang_pack[self.current_lang]
        
        # 폰트 자산 실시간 유효성 스캔 검증기 활성화
        font_key = target_data['font']
        final_font = font_key if os.path.exists(font_files[font_key]) else 'Roboto'
        
        # [원자적 업데이트 아키텍처] 텍스트와 전용 매칭 폰트를 완벽한 동시성에 의거해 즉각 교체 (네모 칸 깨짐 차단)
        self.title_label.text = target_data['title']
        self.title_label.font_name = final_font
        
        self.lang_test_btn.text = target_data['btn']
        self.lang_test_btn.font_name = final_font

class Factory4MasterApp(App):
    def build(self):
        default_font_path = 'font/korean.ttf'
        if os.path.exists(default_font_path):
            LabelBase.register(name='Roboto', fn_regular=default_font_path)
            
        # 눈의 피로를 최소화하며 명암비를 올리는 프리미엄 무광 소프트 아이보리 스크린 세팅
        Window.clearcolor = (0.98, 0.98, 0.94, 1)
        Window.softinput_mode = 'below_target'
        
        return MasterCoreEngine()

if __name__ == '__main__':
    Factory4MasterApp().run()
