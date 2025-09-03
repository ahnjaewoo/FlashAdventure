import platform
import time
import base64
from typing import List, Dict, Literal
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import pyautogui
from .computer import Computer

class LocalDesktopComputer(Computer):
    def __init__(self, max_actions: int = 3):
        os_name = platform.system().lower()
        if "darwin" in os_name:
            self._environment = "mac"
        elif "linux" in os_name:
            self._environment = "linux"
        else:
            self._environment = "windows"
        self._dimensions = pyautogui.size()

        self._action_count = 0
        self._max_actions = max_actions
        self._countable = ["click", "double_click", "scroll", "type", "keypress", "drag"]

    @property
    def environment(self) -> Literal["windows", "mac", "linux"]:
        return self._environment

    @property
    def dimensions(self) -> tuple[int, int]:
        return self._dimensions

    @property
    def action_count(self) -> int:
        return self._action_count

    @property
    def max_actions(self) -> int:
        return self._max_actions

    def _maybe_count(self, action_name: str):
        if action_name in self._countable:
            self._action_count += 1
            print(f"⬆️ 액션 카운터 증가: {self._action_count}/{self._max_actions}")

    def screenshot(self) -> str:
        img = pyautogui.screenshot()
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def click(self, x: int, y: int, button: str = "left") -> None:
        self._maybe_count("click")
        pyautogui.click(x=x, y=y, button=button)

    def double_click(self, x: int, y: int) -> None:
        self._maybe_count("double_click")
        pyautogui.doubleClick(x=x, y=y)

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        self._maybe_count("scroll")
        pyautogui.moveTo(x, y)
        pyautogui.scroll(scroll_y)

    def type(self, text: str) -> None:
        self._maybe_count("type")
        pyautogui.write(text)

    def wait(self, ms: int = 1000) -> None:
        time.sleep(ms / 1000)

    def move(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y)

    def keypress(self, keys: List[str]) -> None:
        self._maybe_count("keypress")
        for key in keys:
            pyautogui.keyDown(key)
        for key in reversed(keys):
            pyautogui.keyUp(key)

    def drag(self, path: List[Dict[str, int]]) -> None:
        self._maybe_count("drag")
        if not path:
            return
        pyautogui.moveTo(path[0]["x"], path[0]["y"])
        pyautogui.mouseDown()
        for point in path[1:]:
            pyautogui.moveTo(point["x"], point["y"])
        pyautogui.mouseUp()

    def get_current_url(self) -> str:
        return "file://local-desktop"

    def reset_action_counter(self):
        self._action_count = 0
