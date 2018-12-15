from kivy import Config
from kivy.clock import Clock
from kivy.core.window import Window
import win32gui


class WindowDragBehavior:
    window_drag_mode = 'both'
    ''' In which direction the window can be dragged.
    Possible values are *both*, *horizontal* and *vertical*. '''

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        self.touch_x, self.touch_y = touch.x, Window.height - touch.y

        self.drag_clock = Clock.schedule_interval(self._drag, 1 / int(Config.get('graphics', 'maxfps')))

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if hasattr(self, 'drag_clock'):
            self.drag_clock.cancel()

        return super().on_touch_up(touch)

    def _drag(self, *args):
        x, y = win32gui.GetCursorPos()

        x -= self.touch_x
        y -= self.touch_y

        if self.window_drag_mode == 'both' or self.window_drag_mode == 'horizontal':
            Window.left = x

        if self.window_drag_mode == 'both' or self.window_drag_mode == 'vertical':
            Window.top = y