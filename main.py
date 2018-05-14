from win32api import GetSystemMetrics
from win32gui import GetCursorInfo
from _thread import start_new
from time import sleep
from nop import NOP
import os
import sys
import win32com.client
import win32gui
import win32con
import string

import kivy
kivy.require('1.10.0')

from kivy.config import Config

Config.set('graphics', 'height', '40')
Config.set('graphics', 'width', '300')
Config.set('graphics', 'borderless', '1')
Config.set('graphics', 'minimum_height', '40')
Config.set('graphics', 'minimum_width', '300')
Config.set('graphics', 'resizable', 0)

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation, AnimationTransition

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView

from kivymd.button import MaterialIconButton


def get_desktop_dir() -> list:
    desktop_path = os.path.join(os.environ['HOMEPATH'], 'Desktop')
    
    return desktop_path

def get_lnk_target(lnk: str) -> str:
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(lnk)
    return shortcut.Targetpath

def width(value: int) -> tuple:
    h = Window.height
    size = (value, h)
    
    return size

def height(value: int) -> tuple:
    w = Window.width
    size = (w, value)

    return size

def prepare_rv_list(paths: list) -> list:
    LNK = '.lnk'
    paths = [
        get_lnk_target(path)
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

def get_filtered(string_: str) -> list:
    paths = list_desktop()
    items = prepare_rv_list(paths)

    condition = lambda item: string_.lower() in f"{item['text']}{item['ext']}".lower()
    filtered_items = filter(condition, items)

    return filtered_items

def list_desktop() -> list:
    desktop = get_desktop_dir()
    items = os.listdir(get_desktop_dir())
    items.remove('desktop.ini')
    for item, index in zip(items, range(len(items))):
        items[index] = f"{desktop}\\{item}"

    return items

def open_file(path: str):
    path = os.path.abspath(path)
    start = lambda path: os.startfile(path)

    if os.path.exists(path):
        start(path)

    else:
        x86 = 'Program Files (x86)'
        x64 = 'Program Files'

        path = path.replace(x86, x64)

        start(path)


class CustBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(CustBoxLayout, self).__init__(**kwargs)

        self.dropdown_shown = False

    def dropdown_show(self):
        if self.dropdown_shown:
            return

        else:
            self.dropdown_shown = True

        TRANS = 'out_expo'
        btn = self.ids.dropdown_button
        
        btn.on_release = NOP

        win_anim = Animation(size=height(300), transition=TRANS)
        button_out_anim = Animation(height=120, transition=TRANS, duration=.2)
        button_in_anim = Animation(height=btn.height, transition=TRANS, duration=.2)

        def update_button(*args):
            btn.icon = 'md-cancel'
            btn.on_release = self.dropdown_hide

        button_out_anim.on_complete = update_button
        
        start_times = {
        # ~ Animation: [after, widget] ~
            win_anim: [0, Window],
            button_out_anim: [0, btn],
            button_in_anim: [.2, btn]
        }

        for anim, values in start_times.items():
            time = values[0]
            widget = values[1]

            fn = lambda clock, anim=anim, widget=widget: anim.start(widget)

            Clock.schedule_once(fn, time)


    def dropdown_hide(self):
        if not self.dropdown_shown:
            return

        else:
            self.dropdown_shown = False

        TRANS = 'out_expo'
        btn = self.ids.dropdown_button
        
        btn.on_release = NOP

        win_anim = Animation(size=height(32), transition=TRANS)
        button_out_anim = Animation(height=120, transition=TRANS, duration=.2)
        button_in_anim = Animation(height=btn.height, transition=TRANS, duration=.2)

        def update_button(*args):
            btn.icon = 'md-arrow-drop-down-circle'
            btn.on_release = self.dropdown_show

        button_out_anim.on_complete = update_button
        
        start_times = {
        # ~ Animation: [after, widget] ~
            win_anim: [0, Window],
            button_out_anim: [0, btn],
            button_in_anim: [.2, btn]
        }

        for anim, values in start_times.items():
            time = values[0]
            widget = values[1]

            fn = lambda clock, anim=anim, widget=widget: anim.start(widget)

            Clock.schedule_once(fn, time)


class LauncherApp(App):
    def __init__(self, **kwargs):
        super(LauncherApp, self).__init__(**kwargs)

        Window.on_cursor_enter = self.enter_countdown

    def build(self):
        self.l = CustBoxLayout()

        self.load_desktop()

        inp = self.l.ids.search_field
        inp.bind(text=self.filter_results)
        
        TITLE = 'FastFastLauncher'
        self.title = TITLE

        return self.l

    def load_desktop(self):
        paths = list_desktop()
        items = prepare_rv_list(paths)

        self.l.ids.item_list.data = items

    def enter_countdown(self):
        Window.orig_on_touch_down = Window.on_touch_down

        Window.on_touch_down = self.cancel_countdown

        TIME = .5
        self.countdown_clock = Clock.schedule_once(self.check_countdown_valid,
                                                   TIME)

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

    def item_click_callback(self, path):
        open_file(path)
        self.l.dropdown_hide()

    def enter_hit_callback(self):
        inp = self.l.ids.search_field
        inp.text = ''

        RV = self.l.ids.item_list
        data = RV.data

        if len(data) == 0:
            return

        first_item = data[0]
        path = first_item['path']

        open_file(path)
        self.l.dropdown_hide()

    def filter_results(self, *args):
        text = args[1]

        if text.strip() == '':
            self.l.dropdown_hide()
            return

        else:
            self.l.dropdown_show()

        filtered_items = get_filtered(text)

        RV = self.l.ids.item_list
        RV.data = filtered_items

    def find_hwnd(self):
        Window.create_window()

        TITLE = self.title
        self.HWND = win32gui.FindWindow(None, TITLE)
        
        return self.HWND

    def pos(self, pos: tuple=(None, None), size: tuple=(None, None)):
        DEFAULT = (None, None)

        if pos == DEFAULT and size == DEFAULT:
            raise Exception('You have to put in atleast one of two parameters')

        if pos == DEFAULT:
            x = Window.left
            y = Window.top
            
            pos = (x, y)

        if size == DEFAULT:
            w = Window.width
            h = Window.height

            size = (w, h)

        hwnd = self.HWND
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, *pos, *size, 0)

    def set_always_on_top(self):
        if not hasattr(self, 'HWND'):
            raise Exception('Call "find_hwnd" method first!')

        hwnd = self.HWND
        rect = win32gui.GetWindowRect(hwnd)
        x = rect[0]
        y = rect[1]
        w = rect[2] - x
        h = rect[3] - y

        win32gui.SetWindowPos(self.HWND, win32con.HWND_TOPMOST, x, y, w, h, 0)

    def on_start(self):
        # Executed when window loaded so it can set the position
        self.find_hwnd()

        screen_width = GetSystemMetrics(0)
        window_width = Window.width

        x = (screen_width // 2) - (window_width // 2)
        y = 0

        pos = ((x, y))
        self.pos(pos)

        def on_draw():
            Window.old_on_draw()
            self.set_always_on_top()
        
        Window.old_on_draw = Window.on_draw
        Window.on_draw = on_draw


if __name__ == '__main__' or __name__ == 'main':
    launcher = LauncherApp()
    launcher.run()

# TODO
# Add support for moving the window