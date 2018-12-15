CONTROL_PANEL_HEIGHT = 40
WINDOW_HEIGHT_EXPANDED = 300

import kivy
kivy.require('1.10.1')

from kivy.logger import Logger

from kivy import Config
Config.set('graphics', 'multisamples', 0) # OpenGL bug hotfix
Config.set('graphics', 'width', 300)
Config.set('graphics', 'height', CONTROL_PANEL_HEIGHT)
Config.set('graphics', 'borderless', True)
Config.set('graphics', 'resizable', False)
Config.set('kivy', 'exit_on_escape', False)
Config.set('input', 'mouse', 'mouse, multitouch_on_demand')

from kivy.app import App

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.textinput import TextInput

from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window

from kivy.graphics import Rectangle

import os
import sys
import win32com.client
import win32gui
import infi.systray
import yaml
import itertools

from window_drag_behavior import WindowDragBehavior

from KivyOnTop import register_topmost
register_topmost(Window, 'FFL')

DESKTOP_RELOAD_INTERVAL = 10
WINDOW_HIDE_MIN_TIME = 1.5
WINDOW_HIDE_CHECK_INTERVAL = 1 / int(Config.get('graphics', 'maxfps'))


def get_lnk_path(path_to_lnk):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(path_to_lnk)
    return shortcut.Targetpath


def get_type_string(filename):
    ext = os.path.splitext(filename)[1]

    if ext == '.lnk':
        ext = os.path.splitext(get_lnk_path(filename))[1]

    TYPES = {'': 'dir', '.exe': 'App'}

    if ext in TYPES:
        return TYPES[ext]

    return ext


class SearchInput(TextInput):
    _hint_text_alpha = NumericProperty(1)

    def on_focus(self, __, has_focus):
        Animation(_hint_text_alpha=not has_focus, d=.1).start(self)


class DesktopViewItem(Button):
    name = StringProperty()
    ''' Filename. '''

    path = ''
    ''' Absolute path to the file. '''

    type_string = StringProperty()
    ''' Gray text displayed on the right side of the widget. Eg. *dir*,
    *exe*, etc. '''

    def on_release(self):
        self.open_path()

    def open_path(self):
        os.startfile(self.path)

    def on_name(self, __, name):
        self.name = name.strip('.lnk')


class PseudoDirentry:
    name = None
    path = None

    def __init__(self, name, path):
        self.name = name
        self.path = path


class DesktopView(RecycleView):
    _desktop_path = os.path.expanduser('~\\Desktop')
    _no_results_color = ListProperty((0, 0, 0, 0))
    _face_size = (140 * .8, 121 * .8)

    def __init__(self, **kw):
        super().__init__(**kw)

        self.reload_desktop()
        Clock.schedule_interval(self.reload_and_filter,
                                DESKTOP_RELOAD_INTERVAL)

    def reload_and_filter(self, *args):
        self.reload_desktop()
        self.filter_items()

    def reload_desktop(self, *args):
        ''' Reloads items from desktop + custom paths. '''

        self.data = []

        CustomDirentrys = [
            PseudoDirentry(name=os.path.split(path)[1], path=path)
            for path in getattr(Config, 'CustomPaths', set())
        ]

        for direntry in itertools.chain(
                os.scandir(self._desktop_path), CustomDirentrys):
            if direntry.path in [item['path'] for item in self.data]:
                continue

            self.data.append({
                'name': os.path.splitext(direntry.name)[0],
                'path': direntry.path,
                'type_string': get_type_string(direntry.path),
            })

    def filter_items(self, *args):
        ''' Filters shown data by the searched term. '''

        self.reload_desktop()
        term = app.root.ids.search_input.text.lower().replace('.', '')

        new_data = []
        for item in self.data:
            if term in f"{item['path']}{item['type_string']}".lower():
                new_data.append(item)

        self.data = new_data

    def on_data(self, *__):
        ''' Will sort shown data by the text.'''

        data = list(self.data)
        data.sort(key=lambda item: item['name'])
        self.unbind(data=self.on_data)
        self.data = data
        self.bind(data=self.on_data)

        # self._no_results_color = (1, 1, 1, not len(data))
        Animation(
            _no_results_color=(1, 1, 1, (not self.data) * .2),
            d=.2).start(self)


class IconButton(ButtonBehavior, Widget):
    icon = StringProperty()
    """ The relative path to the icon. """

    background_color = ListProperty((1, 1, 1, 1))
    """ The color used for drawing background. """

    padding = NumericProperty()
    """ Distance from the border of the button to the border of the image. """

    icon_angle = NumericProperty()
    """ Rotation of the image. """

    _icon_side_size_normal = NumericProperty(1)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            Animation(
                _icon_side_size_normal=.8, d=.3, t='out_expo').start(self)

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        Animation(_icon_side_size_normal=1, d=.3, t='out_expo').start(self)
        return super().on_touch_up(touch)


class Root(WindowDragBehavior, BoxLayout):
    _list_shown = False
    _window_state_event = None
    _window_state = 'HIDDEN'
    _user_request_window_state = 'VISIBLE'

    def __init__(self, **kw):
        super().__init__(**kw)

        self.ids.search_input.bind(
            focus=lambda __, val: setattr(self, 'list_shown', val),
            text=self.ids.desktop_view.filter_items)

        self._window_state_conditions_check_clock = Clock.schedule_interval(
            self._check_window_state_conditions, WINDOW_HIDE_CHECK_INTERVAL)
        self._window_state_event = Clock.create_trigger(
            self._change_window_state_if_conditions, WINDOW_HIDE_MIN_TIME)

        Window.bind(on_dropfile=self.on_dropfile, focus=self.on_window_focus, on_cursor_enter=lambda *__: Window.show())

    @property
    def list_shown(self):
        return self._list_shown

    @list_shown.setter
    def list_shown(self, value):
        self._list_shown = value

        Animation(
            size=(Window.width,
                  WINDOW_HEIGHT_EXPANDED if value else CONTROL_PANEL_HEIGHT),
            d=.5,
            t='out_expo').start(Window)

        Animation(
            icon_angle=180 * value, d=.3,
            t='out_expo').start(self.ids.dropdown_btn)

    @property
    def _will_touch_cursor(self):
        ''' Will window touch the curson when it will be visible? '''

        *__, (x, y) = win32gui.GetCursorInfo()
        return Window.left <= x <= Window.left + Window.width and 0 <= y <= Window.height

    @property
    def window_state(self):
        return self._window_state

    @window_state.setter
    def window_state(self, value):
        print(value, self._window_state)
        VALID_VALUES = ('VISIBLE', 'HIDDEN', 'INVERT')
        if value not in VALID_VALUES:
            raise ValueError

        if value == 'INVERT':
            self._window_state = 'VISIBLE' if self._window_state == 'HIDDEN' else 'HIDDEN'
        else:
            self._window_state = value

        Animation.stop_all(Window)
        Animation(
            top=0 if self._window_state == 'VISIBLE' else -Window.height,
            d=.5,
            t='out_expo').start(Window)

    @property
    def user_request_window_state(self):
        return self._user_request_window_state

    @user_request_window_state.setter
    def user_request_window_state(self, value):
        VALID_VALUES = ('VISIBLE', 'HIDDEN', 'INVERT')
        if value not in VALID_VALUES:
            raise ValueError

        if value == 'INVERT':
            self._user_request_window_state = 'VISIBLE' if self._user_request_window_state == 'HIDDEN' else 'HIDDEN'
        else:
            self._user_request_window_state = value

    def _check_window_state_conditions(self, *args):
        if (self._will_touch_cursor
                and not self._window_state_event.is_triggered
                and self.user_request_window_state == self.window_state
                and not self.list_shown):
            self._window_state_event()

        elif (self.user_request_window_state != self.window_state
              and not self._will_touch_cursor):
            self.window_state = 'INVERT'

        elif not self._will_touch_cursor:
            self._window_state_event.cancel()

    def _change_window_state_if_conditions(self, *args):
        if self._will_touch_cursor and not self.list_shown:
            # may cause issues if window hidden and list shown
            self.window_state = 'INVERT'

    def on_dropfile(self, __, path):
        CustomPaths = getattr(Config, 'CustomPaths', set)
        if not isinstance(CustomPaths, set):
            CustomPaths = set()

        CustomPaths.update({path.decode('utf-8')})
        Config.CustomPaths = CustomPaths

        self.ids.desktop_view.reload_and_filter()

    def on_window_focus(self, *__):
        self.ids.search_input.focus = False

    def open_first_item(self, *args):
        try:
            self.ids.desktop_view.layout_manager.children[-1].open_path()
        except IndexError:
            pass
        else:
            self.ids.search_input.text = ''


class FFLApp(App):
    def on_start(self):
        Window.top = -Window.height
        self.root.user_request_window_state = getattr(Config, 'window_state',
                                                      'VISIBLE')

    def stop(self):
        tray.shutdown()
        return super().stop()

    def request_stop(self):
        tray.shutdown()
        self.root._window_state_conditions_check_clock.cancel()
        self.root.window_state = 'HIDDEN'
        Clock.schedule_interval(self._stop_if_conditions,
                                WINDOW_HIDE_CHECK_INTERVAL)

    def _stop_if_conditions(self, *args):
        if Window.top <= -Window.height:
            self.stop()
            return False


class TrayIcon(infi.systray.SysTrayIcon):
    def __init__(self, *args, **kw):
        MENU_OPTIONS = (('Show / Hide', None, self._show_hide_callbak), )

        super().__init__(
            'img/icon.ico',
            'FastFastLauncher',
            MENU_OPTIONS,
            default_menu_index=0,
            on_quit=self.on_quit)

    def on_quit(self, *__):
        app.request_stop()

    def shutdown(self):
        try:
            return super().shutdown()
        except RuntimeError:
            pass

    def _show_hide_callbak(self, *__):
        app.root.user_request_window_state = 'INVERT'
        Config.window_state = app.root.user_request_window_state


class ConfigMeta(type):
    PATH = 'config.yaml'

    def __getattr__(cls, key):
        cls._ensure_file()

        with open(cls.PATH) as f:
            try:
                return yaml.load(f)[key]
            except KeyError:
                raise AttributeError

    def __setattr__(cls, key, value):
        with open(cls.PATH) as f:
            data = yaml.load(f)

        data[key] = value

        with open(cls.PATH, 'w') as f:
            yaml.dump(data, f)

    def _ensure_file(cls):
        try:
            assert os.path.isfile(cls.PATH)

            with open(cls.PATH) as f:
                _data = yaml.load(f)

            assert isinstance(_data, dict)

        except Exception:
            cls._create_file()

    def _create_file(cls):
        os.makedirs(os.path.split(cls.PATH)[0], exist_ok=True)
        with open(cls.PATH, 'w') as f:
            yaml.dump({'App': 'FastFastLauncher'}, f)


class Config(metaclass=ConfigMeta):
    PATH = '.config/config.yaml'


if __name__ == '__main__':
    tray = TrayIcon()
    tray.start()

    app = FFLApp()
    app.run()

__version__ = '1.3.2'
