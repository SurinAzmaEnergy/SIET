from dataclasses import dataclass

from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
# from kivy.input.providers.mtdev import MTDMotionEvent
from kivy.input.providers.mouse import MouseMotionEvent


# TODO: Read the development flag from the config file!
# In production, this disables mouse input and allows touch-only
DEVELOPMENT = True


@dataclass(frozen=True)
class Theme:
    BOLD_RED = (0.73, 0.23, 0.23, .5)
    PURE_LIGHT = (1, 1, 1, 1)
    SKY_MIST = (0.55, 0.6, 0.7, 1)
    STALE_BLUE = (0.23, 0.29, 0.36, 1)
    STALE_GRAY = (0.85, 0.85, 0.90, 1)
    VIBRANT_GREEN = (0.28, 0.73, 0.31, .5)
    VOID_BLACK = (0, 0, 0, 1)


class Navigator(MDScreenManager):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def on_touch_down(self, touch):
        # Redundant check — kept intentionally for safety.
        if not self.collide_point(*touch.pos):
            return False

        # Reject mouse event in production!
        if not DEVELOPMENT and isinstance(touch, MouseMotionEvent):
            return False

        super().on_touch_down(touch)

    def navigate(self, screen: str) -> None:
        self.current = screen


class Main(MDApp):
    theme = Theme()

    def on_start(self):
        # Window.borderless = True
        Window.size = (1024, 600)

    def build(self):
        self.theme_cls.theme_style = "Light"
        manager = Navigator(self)
        return manager


if __name__ == "__main__":
    Main().run()
