import asyncio
import base64
import os
import platform
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict, cast, get_args
from uuid import uuid4
from datetime import datetime
from PIL import Image
import pyautogui

from anthropic.types.beta import BetaToolComputerUse20241022Param, BetaToolUnionParam

from .base import BaseAnthropicTool, ToolError, ToolResult

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action_20241022 = Literal[
    "key", "type", "mouse_move", "left_click", "left_click_drag",
    "right_click", "middle_click", "double_click", "screenshot", "cursor_position",
]

Action_20250124 = Action_20241022 | Literal[
    "left_mouse_down", "left_mouse_up", "scroll", "hold_key", "wait", "triple_click",
]

ScrollDirection = Literal["up", "down", "left", "right"]

CLICK_BUTTONS = {
    "left_click": "left",
    "right_click": "right",
    "middle_click": "middle",
    "double_click": "left",
    "triple_click": "left",
}

class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"

class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None

def chunks(s: str, chunk_size: int) -> list[str]:
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]

def is_retina_display():
    if platform.system() != 'Darwin':
        return False
    try:
        from AppKit import NSScreen
        return NSScreen.mainScreen().backingScaleFactor() > 1.0
    except:
        w, h = pyautogui.size()
        return abs(w / h - 1512 / 982) < 0.05

class PyAutoGUIComputerTool:
    name: Literal["computer"] = "computer"
    width: int
    height: int
    display_num: int | None
    _screenshot_delay = 0.5
    _scaling_enabled = True

    def __init__(self):
        super().__init__()
        self.width, self.height = pyautogui.size()
        if os.getenv("WIDTH") and os.getenv("HEIGHT"):
            self.width = int(os.getenv("WIDTH"))
            self.height = int(os.getenv("HEIGHT"))
        self.display_num = int(os.getenv("DISPLAY_NUM")) if os.getenv("DISPLAY_NUM") else None

        self.screenshot_dir = Path(os.getenv("SCREENSHOT_DIR", "./screenshots"))
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.game_name = self.screenshot_dir.parent.name
        self.screenshot_counter = 1
        self._is_retina = is_retina_display()

    @property
    def options(self) -> ComputerToolOptions:
        w, h = self.scale_coordinates(ScalingSource.COMPUTER, self.width, self.height)
        return {"display_width_px": w, "display_height_px": h, "display_number": self.display_num}

    def should_count_action(self, action: str) -> bool:
        return action in [
            "left_click", "right_click", "middle_click", "double_click", "triple_click",
            "key", "type", "hold_key", "left_click_drag", "scroll",
        ]

    async def __call__(self, *, action: Action_20241022, text: str | None = None,
                       coordinate: tuple[int, int] | None = None, **kwargs):
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None: raise ToolError("Coordinate is required")
            x, y = self.validate_and_get_coordinates(coordinate)
            return await self.mouse_move(x, y) if action == "mouse_move" else await self.mouse_drag(x, y)

        if action in ("key", "type"):
            if text is None: raise ToolError("Text is required")
            return await self.key_press(text) if action == "key" else await self.type_text(text)

        if action in ("left_click", "right_click", "double_click", "middle_click", "screenshot", "cursor_position"):
            if action == "screenshot": return await self.screenshot()
            if action == "cursor_position": return await self.get_cursor_position()
            if coordinate is not None: x, y = self.validate_and_get_coordinates(coordinate); pyautogui.moveTo(x, y)
            return await self.mouse_click(action)

        raise ToolError(f"Invalid action: {action}")

    async def screenshot(self) -> ToolResult:
        await asyncio.sleep(self._screenshot_delay)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{self.game_name}_{timestamp}_{self.screenshot_counter:04}.png"
        self.screenshot_counter += 1
        path = self.screenshot_dir / filename
        shot = pyautogui.screenshot()
        if self._scaling_enabled:
            if self._is_retina:
                shot = shot.resize((1280, 800), Image.LANCZOS)
            else:
                x, y = self.scale_coordinates(ScalingSource.COMPUTER, self.width, self.height)
                if x != self.width or y != self.height:
                    shot = shot.resize((x, y), Image.LANCZOS)
        shot.save(path)
        return ToolResult(base64_image=base64.b64encode(path.read_bytes()).decode())

    async def mouse_move(self, x: int, y: int) -> ToolResult:
        pyautogui.moveTo(x, y)
        return await self.screenshot()

    async def mouse_drag(self, x: int, y: int) -> ToolResult:
        pyautogui.dragTo(x, y, button='left')
        return await self.screenshot()

    async def key_press(self, key: str) -> ToolResult:
        pyautogui.press(key)
        return await self.screenshot()

    async def type_text(self, text: str) -> ToolResult:
        for chunk in chunks(text, TYPING_GROUP_SIZE):
            pyautogui.write(chunk, interval=TYPING_DELAY_MS / 1000)
        return await self.screenshot()

    async def mouse_click(self, action: str) -> ToolResult:
        button = CLICK_BUTTONS.get(action, "left")
        clicks = {"double_click": 2, "triple_click": 3}.get(action, 1)
        pyautogui.click(button=button, clicks=clicks)
        return await self.screenshot()

    async def get_cursor_position(self) -> ToolResult:
        x, y = pyautogui.position()
        x, y = self.scale_coordinates(ScalingSource.COMPUTER, x, y)
        return ToolResult(output=f"X={x},Y={y}")

    def validate_and_get_coordinates(self, coordinate: tuple[int, int]) -> tuple[int, int]:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
            raise ToolError("Invalid coordinate format")
        return self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> tuple[int, int]:
        targets = {"WXGA": {"width": 1280, "height": 800}}
        target = targets["WXGA"]
        x_scale = target["width"] / self.width
        y_scale = target["height"] / self.height
        return (
            round(x / x_scale) if source == ScalingSource.API else round(x * x_scale),
            round(y / y_scale) if source == ScalingSource.API else round(y * y_scale),
        )

class ComputerTool20241022(PyAutoGUIComputerTool, BaseAnthropicTool):
    api_type: Literal["computer_20241022"] = "computer_20241022"

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

class ComputerTool20250124(PyAutoGUIComputerTool, BaseAnthropicTool):
    api_type: Literal["computer_20250124"] = "computer_20250124"

    def to_params(self):
        return cast(BetaToolUnionParam, {"name": self.name, "type": self.api_type, **self.options})