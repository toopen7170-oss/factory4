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
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

class MasterCoreEngine(FloatLayout):
    def __init__(self, **kwargs):
        super(MasterCoreEngine, self).__init__(**kwargs)
        self.secret_tap_count = 0
        self.last_tap_time = 0
        self.app_title = "실내 사이클 메타버스"
        self.control_dir = "/sdcard/Download/factory/factory2"
        self.control_path = os.path.join(self.control_dir, "control.txt")
        
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.title_label = Label(text=self.app_title, font_size='30sp', size_hint=(1, 0.2))
        self.main_layout.add_widget(self.title_label)
        self.add_widget(self.main_layout)

class Factory4MasterApp(App):
    def build(self):
        if os.path.exists('font/NanumGothic.ttf'):
            LabelBase.register(name='Roboto', fn_regular='font/NanumGothic.ttf')
        Window.clearcolor = (0.05, 0.05, 0.1, 1)
        return MasterCoreEngine()

if __name__ == '__main__':
    Factory4MasterApp().run()
