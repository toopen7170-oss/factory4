import os
import sys
import traceback
import glob
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.core.text import LabelBase

# ---------------------------------------------------------
# 1. 경로 설정
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
# 2. 블랙박스 (오류 로그 자동 저장)
# ---------------------------------------------------------
def global_exception_handler(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, 'crash_log.txt')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(error_msg + "\n" + "="*50 + "\n")
    except: pass
    sys.__excepthook__(exctype, value, tb)
sys.excepthook = global_exception_handler

# ---------------------------------------------------------
# 3. 폰트 시스템
# ---------------------------------------------------------
def is_valid_font(path):
    try: return os.path.exists(path) and os.path.getsize(path) > 1024
    except: return False

def register_external_fonts():
    try: os.makedirs(FONT_DIR, exist_ok=True)
    except: pass
    universal_font = os.path.join(FONT_DIR, 'universal.ttf')
    has_universal = is_valid_font(universal_font)
    font_mapping = {
        'AppFont': 'app_font.ttf', 'Chinese': 'chinese.ttf', 'Japanese': 'japanese.ttf', 
        'Arabic': 'arabic.ttf', 'Thai': 'thai.ttf', 'Global': 'global.ttf', 
        'Korean': 'korean.ttf', 'Universal': 'universal.ttf'
    }
    for font_name, file_name in font_mapping.items():
        font_path = os.path.join(FONT_DIR, file_name)
        if is_valid_font(font_path): LabelBase.register(name=font_name, fn_regular=font_path)
        elif has_universal: LabelBase.register(name=font_name, fn_regular=universal_font)

def get_safe_font():
    if is_valid_font(os.path.join(FONT_DIR, 'korean.ttf')): return 'Korean'
    if is_valid_font(os.path.join(FONT_DIR, 'universal.ttf')): return 'Universal'
    return 'Roboto'

# ---------------------------------------------------------
# 4. 앱 전역 데이터 관리자 (음악/비디오 상태 공유)
# ---------------------------------------------------------
class MediaManager:
    video_files = []
    music_files = []
    selected_music_paths = set()
    audio_player = None
    play_queue = []
    current_play_index = 0
    is_music_playing = False

# 안드로이드 음악 종료 리스너 (JNI)
if platform == 'android':
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        class MusicCompletionListener(PythonJavaClass):
            __javainterfaces__ = ['android/media/MediaPlayer$OnCompletionListener']
            __javacontext__ = 'app'
            def __init__(self, callback, **kwargs):
                super().__init__(**kwargs)
                self.callback = callback
            @java_method('(Landroid/media/MediaPlayer;)V')
            def onCompletion(self, mp):
                Clock.schedule_once(lambda dt: self.callback(), 0)
    except: pass

# ---------------------------------------------------------
# 5. 각 화면(Screen) 클래스 설계
# ---------------------------------------------------------

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.safe_font = get_safe_font()
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)
        
        title = Label(text="MetaRider 메인 시스템", font_name=self.safe_font, font_size='35sp', size_hint_y=0.2)
        layout.add_widget(title)

        # 음악 재생 버튼 (복구됨)
        self.music_btn = Button(text="[배경 음악] 리스트 열기", font_name=self.safe_font, background_color=(0.2, 0.8, 0.2, 1), size_hint_y=0.15)
        self.music_btn.bind(on_press=self.open_music_popup)
        layout.add_widget(self.music_btn)

        btn_1p = Button(text="1인 모드 (주행/경주/타임어택)", font_name=self.safe_font, background_color=(0.2, 0.6, 1, 1))
        btn_1p.bind(on_press=self.go_single_player)
        layout.add_widget(btn_1p)

        btn_2p = Button(text="2인 모드 (화면 분할 듀얼 주행)", font_name=self.safe_font, background_color=(1, 0.5, 0.2, 1))
        btn_2p.bind(on_press=self.go_multi_player)
        layout.add_widget(btn_2p)
        
        self.status_label = Label(text="미디어 스캔 중...", font_name=self.safe_font, size_hint_y=0.1)
        layout.add_widget(self.status_label)
        self.add_widget(layout)
        
        Clock.schedule_interval(self.scan_media, 30.0)
        Clock.schedule_once(self.scan_media, 1)

    def scan_media(self, dt):
        try:
            if os.path.exists(VIDEO_DIR):
                MediaManager.video_files = glob.glob(os.path.join(VIDEO_DIR, '*.mp4')) + glob.glob(os.path.join(VIDEO_DIR, '*.avi')) + glob.glob(os.path.join(VIDEO_DIR, '*.mkv'))
            if os.path.exists(MUSIC_DIR):
                new_music = glob.glob(os.path.join(MUSIC_DIR, '*.mp3'))
                for m in new_music:
                    if m not in MediaManager.music_files: MediaManager.selected_music_paths.add(m)
                MediaManager.music_files = new_music
                
            if not MediaManager.is_music_playing:
                self.music_btn.text = f"[배경 음악] 리스트 열기 ({len(MediaManager.music_files)}곡)"
            self.status_label.text = f"비디오 {len(MediaManager.video_files)}개 | 음악 {len(MediaManager.music_files)}곡 로드 완료"
        except: pass

    # --- 음악 관련 로직 부활 ---
    def open_music_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        top_bar = BoxLayout(size_hint_y=0.15, spacing=5)
        btn_play = Button(text="선택 재생", font_name=self.safe_font, background_color=(0.2, 0.8, 0.2, 1))
        btn_stop = Button(text="정지", font_name=self.safe_font, background_color=(1, 0.5, 0, 1))
        
        top_bar.add_widget(btn_play)
        top_bar.add_widget(btn_stop)
        content.add_widget(top_bar)
        
        scroll = ScrollView(size_hint_y=0.85)
        list_layout = GridLayout(cols=1, size_hint_y=None, spacing=2)
        list_layout.bind(minimum_height=list_layout.setter('height'))
        
        self.checkbox_refs = {} 
        for m_path in MediaManager.music_files:
            row = BoxLayout(size_hint_y=None, height=70, padding=5)
            cb = CheckBox(size_hint_x=0.15, active=(m_path in MediaManager.selected_music_paths))
            lbl = Label(text=os.path.basename(m_path), font_name=self.safe_font, size_hint_x=0.85, halign='left', shorten=True, shorten_from='right')
            lbl.bind(size=lbl.setter('text_size'))
            row.add_widget(cb)
            row.add_widget(lbl)
            list_layout.add_widget(row)
            self.checkbox_refs[m_path] = cb
            
        scroll.add_widget(list_layout)
        content.add_widget(scroll)
        popup = Popup(title="음악 플레이리스트", title_font=self.safe_font, content=content, size_hint=(0.95, 0.9))
        
        btn_play.bind(on_press=lambda x: [self.start_playlist(), popup.dismiss()])
        btn_stop.bind(on_press=lambda x: [self.stop_music(), popup.dismiss()])
        popup.open()

    def start_playlist(self):
        MediaManager.selected_music_paths.clear()
        for m_path, cb in self.checkbox_refs.items():
            if cb.active: MediaManager.selected_music_paths.add(m_path)
            
        if not MediaManager.selected_music_paths: return
        MediaManager.play_queue = [m for m in MediaManager.music_files if m in MediaManager.selected_music_paths]
        MediaManager.current_play_index = 0
        self.play_next_song()

    def play_next_song(self):
        if platform != 'android': return
        if MediaManager.current_play_index >= len(MediaManager.play_queue):
            self.stop_music() 
            return
            
        next_song = MediaManager.play_queue[MediaManager.current_play_index]
        MediaManager.current_play_index += 1
        
        try:
            from jnius import autoclass
            MediaPlayer = autoclass('android.media.MediaPlayer')
            if MediaManager.audio_player:
                MediaManager.audio_player.stop()
                MediaManager.audio_player.release()
            MediaManager.audio_player = MediaPlayer()
            MediaManager.audio_player.setDataSource(next_song)
            if not hasattr(self, 'completion_listener'):
                self.completion_listener = MusicCompletionListener(self.play_next_song)
            MediaManager.audio_player.setOnCompletionListener(self.completion_listener)
            MediaManager.audio_player.prepare()
            MediaManager.audio_player.start()
            
            MediaManager.is_music_playing = True
            self.music_btn.text = f"재생중: {os.path.basename(next_song)[:15]}..."
            self.music_btn.background_color = (1, 0.5, 0, 1)
        except Exception as e:
            self.status_label.text = f"[음악 오류] {str(e)}"
            self.play_next_song() 

    def stop_music(self):
        if MediaManager.audio_player:
            try:
                MediaManager.audio_player.stop()
                MediaManager.audio_player.release()
            except: pass
        MediaManager.audio_player = None
        MediaManager.is_music_playing = False
        self.music_btn.text = f"[배경 음악] 리스트 열기 ({len(MediaManager.music_files)}곡)"
        self.music_btn.background_color = (0.2, 0.8, 0.2, 1)
    # ---------------------------

    def go_single_player(self, instance):
        self.manager.current = 'single_player'

    def go_multi_player(self, instance):
        self.manager.current = 'multi_player'

class SinglePlayerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20)
        safe_font = get_safe_font()
        layout.add_widget(Label(text="[ 1인 모드 대기실 ]", font_name=safe_font, font_size='24sp', size_hint_y=0.2))
        btn_back = Button(text="메인으로 돌아가기", font_name=safe_font, size_hint_y=0.1)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

class MultiPlayerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.safe_font = get_safe_font()
        self.main_layout = BoxLayout(orientation='vertical')
        
        top_bar = BoxLayout(size_hint_y=0.1)
        btn_select_video = Button(text="동영상 선택", font_name=self.safe_font, background_color=(0.2, 0.8, 0.2, 1))
        btn_select_video.bind(on_press=self.open_video_list)
        btn_back = Button(text="뒤로", font_name=self.safe_font, size_hint_x=0.3)
        btn_back.bind(on_press=lambda x: self.cleanup_and_go_back())
        top_bar.add_widget(btn_select_video)
        top_bar.add_widget(btn_back)
        self.main_layout.add_widget(top_bar)
        
        self.split_layout = BoxLayout(orientation='horizontal', size_hint_y=0.9, spacing=5)
        
        self.p1_layout = FloatLayout()
        self.p1_label = Label(text="Player 1 대기중...", font_name=self.safe_font, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.p1_video = None
        self.p1_layout.add_widget(self.p1_label)
        self.split_layout.add_widget(self.p1_layout)
        
        self.p2_layout = FloatLayout()
        self.p2_label = Label(text="Player 2 대기중...", font_name=self.safe_font, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.p2_video = None
        self.p2_layout.add_widget(self.p2_label)
        self.split_layout.add_widget(self.p2_layout)

        self.main_layout.add_widget(self.split_layout)
        self.add_widget(self.main_layout)

    def open_video_list(self, instance):
        content = BoxLayout(orientation='vertical')
        scroll = ScrollView()
        list_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        list_layout.bind(minimum_height=list_layout.setter('height'))
        
        for v_path in MediaManager.video_files:
            btn = Button(text=os.path.basename(v_path), font_name=self.safe_font, size_hint_y=None, height=80)
            btn.bind(on_press=lambda x, path=v_path: [self.start_split_video(path), self.popup.dismiss()])
            list_layout.add_widget(btn)
            
        scroll.add_widget(list_layout)
        content.add_widget(scroll)
        self.popup = Popup(title="2인용 영상 선택", title_font=self.safe_font, content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def start_split_video(self, video_path):
        self.p1_layout.clear_widgets()
        self.p2_layout.clear_widgets()
        
        # options={'allow_stretch': True} 를 추가하여 비디오가 분할 화면에 맞게 늘어나도록 설정
        self.p1_video = Video(source=video_path, state='play', options={'eos': 'loop', 'allow_stretch': True})
        self.p2_video = Video(source=video_path, state='play', options={'eos': 'loop', 'allow_stretch': True})
        
        p1_overlay = Label(text="P1 (RPM: 0)", font_name=self.safe_font, color=(1,0,0,1), pos_hint={'top': 1, 'x': 0}, size_hint=(1, 0.1))
        p2_overlay = Label(text="P2 (RPM: 0)", font_name=self.safe_font, color=(0,0,1,1), pos_hint={'top': 1, 'x': 0}, size_hint=(1, 0.1))
        
        self.p1_layout.add_widget(self.p1_video)
        self.p1_layout.add_widget(p1_overlay)
        self.p2_layout.add_widget(self.p2_video)
        self.p2_layout.add_widget(p2_overlay)

    def cleanup_and_go_back(self):
        if self.p1_video: self.p1_video.state = 'stop'
        if self.p2_video: self.p2_video.state = 'stop'
        self.manager.current = 'main_menu'


# ---------------------------------------------------------
# 6. 메인 부팅 / 권한 시스템
# ---------------------------------------------------------
class MetaRiderApp(App):
    def build(self):
        self.root_layout = BoxLayout(orientation='vertical')
        self.boot_label = Label(text="System Booting...\nChecking Permissions...", font_size='20sp', halign='center')
        self.root_layout.add_widget(self.boot_label)
        Clock.schedule_once(self.check_permissions, 0.5)
        return self.root_layout

    def check_permissions(self, dt):
        if platform == 'android':
            try:
                from jnius import autoclass
                from android.permissions import request_permissions, Permission
                VERSION = autoclass('android.os.Build$VERSION')
                
                if VERSION.SDK_INT >= 30:
                    Environment = autoclass('android.os.Environment')
                    if not Environment.isExternalStorageManager():
                        Intent = autoclass('android.content.Intent')
                        Settings = autoclass('android.provider.Settings')
                        Uri = autoclass('android.net.Uri')
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        
                        intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                        uri = Uri.parse("package:" + PythonActivity.mActivity.getPackageName())
                        intent.setData(uri)
                        PythonActivity.mActivity.startActivity(intent)
                        
                        self.boot_label.text = "Please allow 'All Files Access' in settings."
                        Clock.schedule_interval(self.wait_for_all_files_permission, 1)
                        return
                else:
                    perms = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
                    request_permissions(perms, self.on_permissions_result)
                    return
            except Exception as e:
                print(f"[권한 우회] {e}")
        self.start_main_system(0)

    def wait_for_all_files_permission(self, dt):
        from jnius import autoclass
        Environment = autoclass('android.os.Environment')
        if Environment.isExternalStorageManager():
            Clock.unschedule(self.wait_for_all_files_permission)
            self.start_main_system(0)

    def on_permissions_result(self, permissions, grants):
        self.start_main_system(0)

    def start_main_system(self, dt):
        register_external_fonts()
        self.root_layout.clear_widgets()
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(SinglePlayerScreen(name='single_player'))
        sm.add_widget(MultiPlayerScreen(name='multi_player'))
        self.root_layout.add_widget(sm)

if __name__ == '__main__':
    MetaRiderApp().run()
