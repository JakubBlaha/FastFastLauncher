from win32api import GetSystemMetrics
from win32gui import GetCursorInfo
from _thread import start_new
from time import sleep
import os
import sys
import win32com.client

import kivy
kivy.require('1.10.0')

from kivy.config import Config

Config.set('graphics', 'height', '40')
Config.set('graphics', 'width', '300')
Config.set('graphics', 'borderless', '1')
Config.set('graphics', 'minimum_height', '40')
Config.set('graphics', 'minimum_width', '300')

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation, AnimationTransition

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView

from kivymd.button import MaterialIconButton


class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)

        self.data = [{'text': 'spam'} for x in range(100)]


class CustBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(CustBoxLayout, self).__init__(**kwargs)

        self.dropdown_shown = False

    def dropdown_show(self):
        self.dropdown_shown = True

        curr_width = Window.width
        anim = Animation(
            size=(curr_width, 300), transition=AnimationTransition.out_expo)
        anim.start(Window)

        orig_h = self.ids.dropdown_button.height

        btn_anim_dur_half = .2

        icon_anim = Animation(
            height=120,
            duration=btn_anim_dur_half,
            transition=AnimationTransition.out_expo)
        icon_anim.start(self.ids.dropdown_button)

        def after_btn_anim(*args):
            self.ids.dropdown_button.icon = 'md-cancel'

            icon_anim = Animation(
                height=orig_h,
                duration=btn_anim_dur_half,
                transition=AnimationTransition.out_expo)
            icon_anim.start(self.ids.dropdown_button)

            self.ids.dropdown_button.on_release = self.dropdown_hide

        Clock.schedule_once(after_btn_anim, btn_anim_dur_half)

        Window.on_cursor_leave = self.dropdown_hide

    def dropdown_hide(self):
        if not self.dropdown_shown:
            return

        self.dropdown_shown = False

        curr_width = Window.width
        anim = Animation(
            size=(curr_width, 32), transition=AnimationTransition.out_expo)
        anim.start(Window)

        orig_h = self.ids.dropdown_button.height

        btn_anim_dur_half = .2

        icon_anim = Animation(
            height=120,
            duration=btn_anim_dur_half,
            transition=AnimationTransition.out_expo)
        icon_anim.start(self.ids.dropdown_button)

        def after_btn_anim(*args):
            self.ids.dropdown_button.icon = 'md-arrow-drop-down-circle'

            icon_anim = Animation(
                height=orig_h,
                duration=btn_anim_dur_half,
                transition=AnimationTransition.out_expo)
            icon_anim.start(self.ids.dropdown_button)

            self.ids.dropdown_button.on_release = self.dropdown_show

        Clock.schedule_once(after_btn_anim, btn_anim_dur_half)


class LauncherApp(App):
    def __init__(self, **kwargs):
        super(LauncherApp, self).__init__(**kwargs)

        Window.on_cursor_enter = self.enter_countdown

    def build(self):
        self.l = CustBoxLayout()

        self.load_list_items()

        inp = self.l.ids.search_field

        inp.bind(text=self.filter_results)

        return self.l

    def load_list_items(self):
        paths = self.list_desktop()
        items = self.prepare_rv_list(paths)

        self.l.ids.item_list.data = items

    def get_lnk_target(self, lnk):
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk)
        return shortcut.Targetpath

    def enter_countdown(self):
        Window.orig_on_touch_down = Window.on_touch_down

        Window.on_touch_down = self.cancel_countdown
        if hasattr(Window, 'on_cursor_enter'):
            del Window.on_cursor_enter

        self.countdown_clock = Clock.schedule_once(self.check_countdown_valid,
                                                   1)

    def cancel_countdown(self, touch):
        self.countdown_clock.cancel()

        Window.on_touch_down = Window.orig_on_touch_down
        Window.on_touch_down(touch)
        Window.on_cursor_enter = self.enter_countdown

    def check_countdown_valid(self, touch):
        if hasattr(Window, 'on_touch_down'):
            del Window.on_touch_down

        x = Window.left
        y = Window.top

        self.orig_pos = {'x': x, 'y': y}

        self.temp_move_app()

    def temp_move_app(self):
        curr_x = Window.left
        w_width = Window.width

        new_x = curr_x - w_width

        anim = Animation(
            left=new_x, transition=AnimationTransition.out_expo, duration=.5)
        anim.start(Window)

        self.check_loop()

    def check_loop(self):
        w = Window.width
        h = Window.height

        x1 = self.orig_pos['x']
        x2 = x1 + w
        y1 = self.orig_pos['y'] - 1
        y2 = y1 + h

        def loop(*args):
            *rest, (cursor_x, cursor_y) = GetCursorInfo()

            horizontal_in = cursor_x > x1 and cursor_x < x2
            vertical_in = cursor_y > y1 and cursor_y < y2

            if horizontal_in and vertical_in:
                pass

            else:
                self.restore_orig_pos()
                self.pos_check_clock.cancel()

        self.pos_check_clock = Clock.schedule_interval(loop, .1)

    def restore_orig_pos(self):
        x = self.orig_pos['x']

        del self.orig_pos

        anim = Animation(
            left=x, transition=AnimationTransition.out_expo, duration=.5)

        def restore_enter_event(*args):
            Window.on_cursor_enter = self.enter_countdown

        anim.on_complete = restore_enter_event

        anim.start(Window)

    def get_desktop_dir(self):
        return os.path.join(os.environ["HOMEPATH"], "Desktop")

    def list_desktop(self):
        desktop = self.get_desktop_dir()
        items = os.listdir(self.get_desktop_dir())
        items.remove('desktop.ini')
        for item, index in zip(items, range(len(items))):
            items[index] = f"{desktop}\\{item}"

        return items

    def start_file(self, path):
        try:
            os.startfile(os.path.abspath(path))
        except FileNotFoundError:
            path = path.replace('Program Files (x86)', 'Program Files')
            os.startfile(path)

        self.l.dropdown_hide()

    def filter_results(self, *args):
        inp = self.l.ids.search_field

        text = inp.text

        if text.strip() == '':
            self.cancel_filter()
            return

        filtered_items = self.get_filtered(text)

        RV = self.l.ids.item_list
        RV.data = filtered_items

    def prepare_rv_list(self, paths):
        LNK = '.lnk'
        paths = [
            self.get_lnk_target(path)
            if os.path.splitext(path)[1] == LNK else path for path in paths
        ]

        basenames = [os.path.splitext(os.path.basename(path))[0] for path in paths]
        exts = [os.path.splitext(path)[1] for path in paths]

        items = [{
            'path': path,
            'text': base,
            'ext': ext
            } for path, base, ext in zip(paths, basenames, exts)
            ]

        return items

    def get_filtered(self, string):
        paths = self.list_desktop()
        items = self.prepare_rv_list(paths)
        filtered_items = [
            item for item in items if string.lower().strip() in (item['text'] + item['ext']).lower()
        ]

        return filtered_items

    def cancel_filter(self):
        self.load_list_items()


if __name__ == '__main__' or __name__ == 'main':
    screen_width = GetSystemMetrics(0)
    window_width = Window.width
    pos = (screen_width // 2) - (window_width // 2)

    Window.left = pos
    Window.top = 0
    Window.on_hide = Window.raise_window

    launcher = LauncherApp()
    launcher.run()
