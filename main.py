from win32api import GetSystemMetrics
from win32gui import GetCursorInfo
from time import sleep
from nop import NOP
import os
import sys
import win32com.client
import win32gui
import win32con
import string
import shutil

import kivy
kivy.require('1.10.0')

from kivy.config import Config

Config.set('graphics', 'multisamples', 0)
Config.set('graphics', 'height', '40')
Config.set('graphics', 'width', '300')
Config.set('graphics', 'borderless', '1')
Config.set('graphics', 'minimum_height', '40')
Config.set('graphics', 'minimum_width', '300')
Config.set('graphics', 'resizable', 0)
Config.set('input', 'mouse', 'mouse, disable_multitouch')

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.uix.popup import Popup

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
        get_lnk_target(path) if os.path.splitext(path)[1] == LNK else path
        for path in paths
    ]

    basenames = [os.path.splitext(os.path.basename(path))[0] for path in paths]
    exts = [os.path.splitext(path)[1].replace('.', '') for path in paths]
    exts = [
        ext if os.path.isfile(paths[index]) else 'dir'
        for index, ext in enumerate(exts)
    ]

    items = [{
        'path': path,
        'text': base,
        'ext': ext
    } for path, base, ext in zip(paths, basenames, exts)]

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


class Config:
    PATH = os.path.expanduser('~\\Xtremeware\\FastFastLauncher\\paths.txt')
    paths = []

    @staticmethod
    def new(path: str):
        Config._ensure_config_file()
        Config._ensure_loaded()

        if path in Config.paths:
            return

        with open(Config.PATH, 'a') as f:
            f.write(path + '\n')

        Config.paths.append(path)

    @staticmethod
    def remove(path: str):
        Config._ensure_config_file()

        with open(Config.PATH) as f:
            paths = [line for line in f]

        paths = [path_ for path_ in paths if path_ != path]

        with open(Config.PATH) as f:
            f.writelines(paths)

    @staticmethod
    def get_all() -> list:
        Config._ensure_config_file()
        Config._ensure_loaded()

        return Config.paths

    @staticmethod
    def _get_paths() -> list:
        with open(Config.PATH) as f:
            return [path.replace('\n', '') for path in f.readlines()]

    @staticmethod
    def _update_paths():
        Config.paths = Config._get_paths()

    @staticmethod
    def _ensure_config_file():
        if not os.path.isdir(os.path.dirname(Config.PATH)):
            os.makedirs(Config.PATH)

        if not os.path.isfile(Config.PATH):
            Config._create_empty_file(Config.PATH)

    @staticmethod
    def _create_empty_file(path: str):
        open(path, 'w').close()

    @staticmethod
    def _ensure_loaded():
        if Config.paths == []:
            Config._update_paths()


class WindowDragBehavior:
    both = False
    horizontal = False
    vertical = False

    def drag_behavior_init(self, mode: str='both'):
        '''
        mode - both, horizontal, vertical
        '''

        exec(f'self.{mode} = True')

        self.bind(on_touch_down=self._on_touch_down)
        self.bind(on_touch_up=self._on_touch_up)

    def _on_touch_down(self, _, touch):
        self._click(touch)
        self.drag_clock = Clock.schedule_interval(self._drag, 1 / 60)

    def _on_touch_up(self, _, touch):
        if hasattr(self, 'drag_clock'):
            self.drag_clock.cancel()

    def _click(self, touch):
        x = touch.x
        y = touch.y

        y = Window.height - y

        self.touch_x, self.touch_y = x, y

    def _drag(self, *args):
        x, y = win32gui.GetCursorPos()

        x -= self.touch_x
        y -= self.touch_y

        if self.both or self.horizontal:
            Window.left = x
        
        if self.both or self.vertical:
            Window.top = y


class CustBoxLayout(WindowDragBehavior, BoxLayout):
    size_ = ObjectProperty((None, None))
    width_ = NumericProperty(None)
    height_ = NumericProperty(None)

    def __init__(self, **kwargs):
        super(CustBoxLayout, self).__init__(**kwargs)
        self.drag_behavior_init(mode='horizontal')

        self.dropdown_shown = False
        self.dialog_shown = False

        self.bind(width_=self.update_size_property)
        self.bind(height_=self.update_size_property)

    def update_size_property(self, *args):
        self.size_ = (self.width_, self.height_)

    def show_load(self):
        self.dialog_shown = True

        visible_wgs = [
            self.ids.search_field, self.ids.dropdown_button,
            self.ids.add_button, self.ids.item_list
        ]
        fade_anim = Animation(opacity=0, t='out_expo')
        for wg in visible_wgs:
            wg.old_opacity = wg.opacity
            fade_anim.start(wg)

        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title='Add file', content=content)
        Clock.schedule_once(self._popup.open, 1)

        NEW_WIDTH = 800
        self.expand(height=500, width=NEW_WIDTH)

    def load(self, *args):
        self.dismiss_popup()

        path = args[1][0]

        Config.new(path)

    def dismiss_popup(self):
        self.dialog_shown = False

        self._popup.dismiss()
        self.expand(height=27, width=290)

        visible_wgs = [
            self.ids.search_field, self.ids.dropdown_button,
            self.ids.add_button, self.ids.item_list
        ]
        for wg in visible_wgs:
            fade_anim = Animation(opacity=wg.old_opacity, t='out_expo')
            fade_anim.start(wg)

    def expand(self, width: int = None, height: int = None, **anim_kwargs):
        if width == None:
            self.width_ = Window.width
        else:
            self.width_ = width

        if height == None:
            self.height_ = Window.height
        else:
            self.height_ = height

        anim = Animation(size=self.size_, t='out_expo')
        anim.bind(**anim_kwargs)
        anim.start(Window)

        Clock.schedule_once(lambda *args: self.center_window(), # hotfix for https://github.com/kivy/kivy/issues/5757
                            getattr(
                                anim,
                                'duration',
                                getattr(anim, 'd', 1)))

    def center_window(self):
        scw = GetSystemMetrics(0)
        ww = Window.width

        x = (scw // 2) - (ww // 2)

        anim = Animation(left=x, t='out_expo')
        anim.start(Window)

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
        button_in_anim = Animation(
            height=btn.height, transition=TRANS, duration=.2)

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

    def dropdown_hide(self, *args):
        '''
        args:
            force - Forces dropdown to hide even if not *not self.dropdown_shown or self.dialog_shown or self.ids.search_field.focus*
        '''
        if not self.dropdown_shown or self.dialog_shown or self.ids.search_field.focus and not 'force' in args:
            return

        else:
            self.dropdown_shown = False

        TRANS = 'out_expo'
        btn = self.ids.dropdown_button

        btn.on_release = NOP

        win_anim = Animation(size=height(32), transition=TRANS)
        button_out_anim = Animation(height=120, transition=TRANS, duration=.2)
        button_in_anim = Animation(
            height=btn.height, transition=TRANS, duration=.2)

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


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class LauncherApp(App):
    def __init__(self, **kwargs):
        super(LauncherApp, self).__init__(**kwargs)

        Window.on_cursor_enter = self.set_countdown

    def build(self):
        self.l = CustBoxLayout()

        self.load_desktop()

        inp = self.l.ids.search_field
        inp.bind(text=self.filter_results)

        TITLE = 'FastFastLauncher'
        self.title = TITLE

        Window.bind(on_cursor_leave=self.l.dropdown_hide)

        return self.l

    def load_desktop(self):
        paths = list_desktop()
        items = prepare_rv_list(paths)
        custom_items = prepare_rv_list(Config.get_all())
        items.extend(custom_items)

        self.l.ids.item_list.data = items

    def set_countdown(self):
        if self.l.dropdown_shown or self.l.dialog_shown:
            return

        Window.on_touch_down = self.cancel_countdown_touch
        Window.on_cursor_leave = self.cancel_countdown

        TIME = .5
        self.countdown_clock = Clock.schedule_once(self.move_window_away, TIME)

    def cancel_countdown(self):
        del Window.on_touch_down
        del Window.on_cursor_leave

        self.countdown_clock.cancel()

        Window.on_cursor_enter = self.set_countdown

    def cancel_countdown_touch(self, touch):
        del Window.on_touch_down
        del Window.on_cursor_leave

        self.countdown_clock.cancel()

        Window.on_touch_down(touch)
        Window.on_cursor_enter = self.set_countdown

    def move_window_away(self, *args):
        x = Window.left
        y = Window.top

        self.orig_pos = {'x': x, 'y': y}

        curr_x = Window.left
        w_width = Window.width

        new_x = curr_x - w_width

        anim = Animation(left=new_x, transition='out_expo', duration=.5)
        anim.start(Window)

        self.pos_restore_hook()

    def pos_restore_hook(self):
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
                self.restore_pos()
                self.pos_check_clock.cancel()

        INTERVAL = .1
        self.pos_check_clock = Clock.schedule_interval(loop, INTERVAL)

    def restore_pos(self):
        x = self.orig_pos['x']

        anim = Animation(left=x, transition='out_expo', duration=.5)

        def restore_enter_event(*args):
            Window.on_cursor_enter = self.set_countdown

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

    def _find_hwnd(self):
        Window.create_window()

        TITLE = self.title
        self.HWND = win32gui.FindWindow(None, TITLE)

        return self.HWND

    def pos(self, pos: tuple = (None, None), size: tuple = (None, None)):
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

    def set_always_on_top(self, *args):
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

        self._find_hwnd()

        screen_width = GetSystemMetrics(0)
        window_width = Window.width

        x = (screen_width // 2) - (window_width // 2)
        y = 0

        pos = ((x, y))
        self.pos(pos)

        Window.bind(on_draw=self.set_always_on_top)


if __name__ == '__main__' or __name__ == 'main':
    launcher = LauncherApp()
    launcher.run()
