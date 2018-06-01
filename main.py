from win32api import GetSystemMetrics
from win32gui import GetCursorInfo
from KivyOnTop import *
import os
import sys
import win32com.client
import win32gui
import win32con
from infi.systray import SysTrayIcon

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
from kivy.properties import ObjectProperty
from kivy.properties import BooleanProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivymd.button import MaterialIconButton


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS',
                        os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


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
    paths.extend(Config.get_all())
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
    PATH = os.path.expanduser('~\\.xtremeware\\FastFastLauncher\\paths.txt')
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
        dirname = os.path.dirname(Config.PATH)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

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

    def drag_behavior_init(self, mode: str = 'both'):
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


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class CustBoxLayout(WindowDragBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super(CustBoxLayout, self).__init__(**kwargs)
        self.drag_behavior_init(mode='horizontal')

        self.dropdown_shown = False
        self.dialog_shown = False

        self.ids.search_field.bind(
            text=lambda *args: App.get_running_app().filter_results(*args))

    def show_load(self):
        self.dialog_shown = True

        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title='Add file', content=content)
        Clock.schedule_once(self._popup.open, .3)

        new_size = (800, 500)
        new_x = Window.left - (new_size[0] // 2) + (Window.size[0] // 2)
        window_anim = Animation(size=new_size, left=new_x, t='out_expo', d=.5)
        window_anim.start(Window)

    def load(self, *args):
        self.dismiss_popup()

        try:
            path = args[1][0]

        except IndexError:
            path = args[0]

        Config.new(path)

    def dismiss_popup(self):
        self.dialog_shown = False

        self._popup.dismiss()

        new_size = (300, 40)
        new_x = Window.left - (new_size[0] // 2) + (Window.size[0] // 2)
        window_anim = Animation(size=new_size, left=new_x, t='out_expo', d=.5)
        Clock.schedule_once(lambda _: window_anim.start(Window), .1)

    def dropdown_show(self):
        if self.dropdown_shown:
            return

        self.dropdown_shown = True

        TRANS = 'out_expo'
        btn = self.ids.dropdown_button

        btn.on_release = lambda: None

        win_anim = Animation(size=height(300), t=TRANS, d=.5)
        button_out_anim = Animation(opacity=0, t=TRANS, d=.2)
        button_in_anim = Animation(opacity=1, t=TRANS, d=.2)

        def update_button_icon(*args):
            btn.icon = 'md-cancel'

        def restore_button_command(*args):
            btn.on_release = self.dropdown_hide

        button_out_anim.bind(on_complete=update_button_icon)
        button_in_anim.bind(on_complete=restore_button_command)

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
        if not self.dropdown_shown:
            return

        self.dropdown_shown = False

        TRANS = 'out_expo'
        btn = self.ids.dropdown_button

        btn.on_release = lambda: None

        win_anim = Animation(size=height(40), t=TRANS, d=.5)
        button_out_anim = Animation(opacity=0, t=TRANS, d=.2)
        button_in_anim = Animation(opacity=1, t=TRANS, d=.2)

        def update_button_icon(*args):
            btn.icon = 'md-arrow-drop-down-circle'

        def restore_button_command(*args):
            btn.on_release = self.dropdown_show

        button_out_anim.bind(on_complete=update_button_icon)
        button_in_anim.bind(on_complete=restore_button_command)

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
    visible = BooleanProperty(True)
    stop_request = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(LauncherApp, self).__init__(**kwargs)

        Window.on_cursor_enter = self.set_countdown

        self.bind(
            visible=lambda *args: self.__toggle_visible(),
            stop_request=self.stop_hook)
        self.title = 'FastFastLauncher'

    def build(self):
        self.l = CustBoxLayout()
        return self.l

    def stop_hook(self, *args):
        self.visible = False
        Clock.schedule_once(self.stop, .5)

    def __toggle_visible(self, *args):
        if self.visible:
            self.show()

        else:
            self.hide()

    def set_countdown(self, *args):
        if self.l.dropdown_shown or self.l.dialog_shown:
            return

        Window.bind(
            on_touch_down=self.cancel_countdown,
            on_cursor_leave=self.cancel_countdown)

        self.countdown_clock = Clock.schedule_once(self.hide, 1)

    def cancel_countdown(self, *args):
        Window.unbind(
            on_touch_down=self.cancel_countdown,
            on_cursor_leave=self.cancel_countdown)

        self.countdown_clock.cancel()

    def hide(self, *args, **bkwargs):
        self.orig_y = Window.top
        new_y = self.orig_y - Window.height

        anim = Animation(top=new_y, t='out_expo', d=.5)
        anim.bind(**bkwargs)
        anim.start(Window)

        self.show()

    def show(self, *args, **bkwargs):
        w = Window.width
        h = Window.height

        x1 = Window.left
        x2 = x1 + w
        y1 = self.orig_y - 1
        y2 = y1 + h

        def loop(*args):
            *rest, (cursor_x, cursor_y) = GetCursorInfo()

            horizontal_in = cursor_x > x1 and cursor_x < x2
            vertical_in = cursor_y > y1 and cursor_y < y2

            if not (horizontal_in and vertical_in):
                if self.visible:
                    self.pos_check_clock.cancel()
                    self.restore_pos(**bkwargs)

        self.pos_check_clock = Clock.schedule_interval(loop, .1)

    def restore_pos(self, **bkwargs):
        anim = Animation(top=self.orig_y, t='out_expo', d=.5)
        anim.bind(**bkwargs)
        anim.start(Window)

    def item_click_callback(self, path):
        open_file(path)
        self.l.dropdown_hide()

    def enter_hit_callback(self):
        data = self.l.ids.item_list.data

        if len(data) == 0:
            return

        path = data[0]['path']
        open_file(path)

        self.l.ids.search_field.text = ''

    def filter_results(self, *args):
        text = dict(enumerate(args)).get(1, '')

        if text.strip() == '':
            self.l.dropdown_hide()

        else:
            self.l.dropdown_show()

        filtered_items = get_filtered(text)
        self.l.ids.item_list.data = filtered_items

    def on_start(self):
        sw = GetSystemMetrics(0)
        ww = Window.width

        Window.left = sw // 2 - ww // 2
        Window.top = -1

        register_topmost(Window, self.title)


class LauncherIcon(SysTrayIcon):
    ICON = 'img/icon.ico'
    TOOLTIP_TEXT = 'FastFastLauncher'

    def __init__(self):
        menu_options = (('Visible', None, self.toggle_visible), )

        args = (self.ICON, self.TOOLTIP_TEXT)
        kwargs = {
            'on_quit': self.on_quit_callback,
            'menu_options': menu_options,
        }

        super(LauncherIcon, self).__init__(*args, **kwargs)

    def on_quit_callback(self, *args):
        App.get_running_app().stop_request = True

    def toggle_visible(self, *args):
        app = App.get_running_app()
        app.visible = not app.visible


if __name__ == '__main__':
    icon = LauncherIcon()
    icon.start()

    launcher = LauncherApp()
    launcher.run()
