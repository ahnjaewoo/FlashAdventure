"""
Cross-platform computer control tool using PyAutoGUI
"""

import asyncio
import base64
import os
import platform
import shlex
import shutil
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict, cast, get_args
from uuid import uuid4
import io
from PIL import Image

# Import PyAutoGUI
import pyautogui
# Settings for improved screenshot capture speed
pyautogui.FAILSAFE = True  # Stop program when mouse moves to corner of screen
pyautogui.PAUSE = 0.1  # Default pause time between function calls

from anthropic.types.beta import BetaToolComputerUse20241022Param, BetaToolUnionParam

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run, get_temp_dir

# Create screenshots folder in current directory and set output path
CURRENT_DIR = os.path.abspath(os.path.curdir)
OUTPUT_DIR = os.path.join(CURRENT_DIR, "screenshots")
# Create directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action_20241022 = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]

Action_20250124 = (
    Action_20241022
    | Literal[
        "left_mouse_down",
        "left_mouse_up",
        "scroll",
        "hold_key",
        "wait",
        "triple_click",
    ]
)

ScrollDirection = Literal["up", "down", "left", "right"]


class Resolution(TypedDict):
    width: int
    height: int


# Define screen resolution targets
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
    # "RETINA": Resolution(width=1512, height=982)  # ✅ Added MacBook logical resolution
}

CLICK_BUTTONS = {
    "left_click": "left",
    "right_click": "right",
    "middle_click": "middle",
    "double_click": "left",  # In PyAutoGUI, specified with clicks=2 parameter instead of button
    "triple_click": "left",  # In PyAutoGUI, specified with clicks=3 parameter instead of button
}


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"


class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None


def chunks(s: str, chunk_size: int) -> list[str]:
    """Split a string into chunks of specified size."""
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]


def is_retina_display():
    """Check if display is a Retina display on macOS"""
    if platform.system() != 'Darwin':
        return False
    try:
        from AppKit import NSScreen
        scale_factor = NSScreen.mainScreen().backingScaleFactor()
        return scale_factor > 1.0
    except:
        # If AppKit is unavailable, guess based on ratio
        screen_width, screen_height = pyautogui.size()
        return abs(screen_width / screen_height - 1512 / 982) < 0.05


class PyAutoGUIComputerTool:
    """
    Cross-platform computer control tool using PyAutoGUI.
    Works on Windows, macOS, and Linux.
    """

    name: Literal["computer"] = "computer"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 0.5
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        """Return tool options."""
        width, height = self.scale_coordinates(
            ScalingSource.COMPUTER, self.width, self.height
        )
        return {
            "display_width_px": width,
            "display_height_px": height,
            "display_number": self.display_num,
        }

    def __init__(self):
        """Initialize the tool."""
        super().__init__()
        
        # Detect screen resolution
        self.width, self.height = pyautogui.size()
        
        # Use resolution provided in environment variables (if available)
        if os.getenv("WIDTH") and os.getenv("HEIGHT"):
            self.width = int(os.getenv("WIDTH"))
            self.height = int(os.getenv("HEIGHT"))
        
        assert self.width and self.height, "Could not determine screen resolution"
        
        # Set display number (if available)
        if (display_num := os.getenv("DISPLAY_NUM")) is not None:
            self.display_num = int(display_num)
        else:
            self.display_num = None
            
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Detect Retina display and log
        self._is_retina = is_retina_display()
        print(f"Retina display: {self._is_retina}")
        print(f"Screen resolution: {self.width} x {self.height}")

    async def __call__(
        self,
        *,
        action: Action_20241022,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        """Call the tool."""
        # Handle mouse movement actions
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ToolError(f"Coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"Text is not accepted for {action}")

            x, y = self.validate_and_get_coordinates(coordinate)

            if action == "mouse_move":
                return await self.mouse_move(x, y)
            elif action == "left_click_drag":
                return await self.mouse_drag(x, y)

        # Handle keyboard actions
        if action in ("key", "type"):
            if text is None:
                raise ToolError(f"Text is required for {action}")
            if coordinate is not None:
                raise ToolError(f"Coordinate is not accepted for {action}")
            if not isinstance(text, str):
                raise ToolError(output=f"{text} must be a string")

            if action == "key":
                return await self.key_press(text)
            elif action == "type":
                return await self.type_text(text)

        # Handle other actions
        if action in (
            "left_click",
            "right_click",
            "double_click",
            "middle_click",
            "screenshot",
            "cursor_position",
        ):
            if text is not None:
                raise ToolError(f"Text is not accepted for {action}")
            if coordinate is not None and action != "left_click" and action != "right_click":
                raise ToolError(f"Coordinate is not accepted for {action}")

            if action == "screenshot":
                return await self.screenshot()
            elif action == "cursor_position":
                return await self.get_cursor_position()
            else:
                # Handle clicks with optional coordinates
                if coordinate is not None:
                    x, y = self.validate_and_get_coordinates(coordinate)
                    await self.mouse_move(x, y)
                return await self.mouse_click(action)

        raise ToolError(f"Invalid action: {action}")

    async def mouse_move(self, x: int, y: int) -> ToolResult:
        """Move mouse to the specified coordinates."""
        pyautogui.moveTo(x, y)
        return await self.screenshot()

    async def mouse_drag(self, x: int, y: int) -> ToolResult:
        """Perform a drag operation from current position to specified coordinates."""
        # Get current cursor position
        current_x, current_y = pyautogui.position()
        
        # Perform drag
        pyautogui.dragTo(x, y, button='left')
        
        return await self.screenshot()

    async def key_press(self, key: str) -> ToolResult:
        """Simulate key press."""
        pyautogui.press(key)
        return await self.screenshot()

    async def type_text(self, text: str) -> ToolResult:
        """Simulate typing text."""
        # Split into chunks for typing speed control
        for chunk in chunks(text, TYPING_GROUP_SIZE):
            pyautogui.write(chunk, interval=TYPING_DELAY_MS/1000)
            
        return await self.screenshot()

    async def mouse_click(self, action: str) -> ToolResult:
        """Perform mouse click action."""
        button = CLICK_BUTTONS.get(action, "left")
        
        if action == "double_click":
            pyautogui.click(clicks=2, button=button)
        elif action == "triple_click":
            pyautogui.click(clicks=3, button=button)
        else:
            pyautogui.click(button=button)
            
        return await self.screenshot()

    async def get_cursor_position(self) -> ToolResult:
        """Get current cursor position."""
        x, y = pyautogui.position()
        x, y = self.scale_coordinates(ScalingSource.COMPUTER, x, y)
        
        return ToolResult(output=f"X={x},Y={y}")

    async def screenshot(self) -> ToolResult:
        """Take a screenshot of the current screen."""
        # Add a slight delay before taking the screenshot
        await asyncio.sleep(self._screenshot_delay)
        
        # Use screenshots directory in current folder
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"
        
        # Take screenshot with PyAutoGUI
        screenshot = pyautogui.screenshot()
        
        # Handle Retina display
        if self._scaling_enabled:
            if self._is_retina:
                # Scale Retina display to WXGA (maintain 16:10 ratio)
                target_width, target_height = 1280, 800  # WXGA
                screenshot = screenshot.resize((target_width, target_height), Image.LANCZOS)
                print(f"Retina display detected: Scaling screenshot to {target_width}x{target_height}")
            else:
                # Maintain existing scaling logic
                x, y = self.scale_coordinates(
                    ScalingSource.COMPUTER, self.width, self.height
                )
                if x != self.width or y != self.height:
                    screenshot = screenshot.resize((x, y), Image.LANCZOS)
                    print(f"Standard display: Scaling screenshot to {x}x{y}")
        
        # Save screenshot
        screenshot.save(path)
        
        if path.exists():
            print(f"Screenshot saved to: {path}")
            return ToolResult(
                base64_image=base64.b64encode(path.read_bytes()).decode()
            )
        raise ToolError(f"Failed to take screenshot")

    def validate_and_get_coordinates(self, coordinate: tuple[int, int] | None = None):
        """Validate coordinates and scale them appropriately."""
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
            raise ToolError(f"{coordinate} must be a tuple of length 2")
        if not all(isinstance(i, int) and i >= 0 for i in coordinate):
            raise ToolError(f"{coordinate} must be a tuple of non-negative integers")

        return self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])

    def scale_coordinates(self, source: ScalingSource, x: int, y: int):
        """Scale coordinates to target resolution if scaling is enabled."""
        if not self._scaling_enabled:
            return x, y
        
        # Handle Retina display
        if self._is_retina:
            # Scale Retina display to WXGA
            target_dimension = MAX_SCALING_TARGETS["WXGA"]  # Fixed at 1280x800
        else:
            # Existing logic - find best matching target based on aspect ratio
            ratio = self.width / self.height
            target_dimension = None
            for dimension in MAX_SCALING_TARGETS.values():
                if abs(dimension["width"] / dimension["height"] - ratio) < 0.02:
                    if dimension["width"] < self.width:
                        target_dimension = dimension
                        break
        
        if target_dimension is None:
            return x, y
        
        # Calculate scaling factors
        x_scaling_factor = target_dimension["width"] / self.width
        y_scaling_factor = target_dimension["height"] / self.height
        
        if source == ScalingSource.API:
            # Make sure coordinates are within bounds
            if x > target_dimension["width"] or y > target_dimension["height"]:
                raise ToolError(f"Coordinates {x}, {y} are out of bounds")
            # Scale up to actual screen coordinates
            scaled_x = round(x / x_scaling_factor)
            scaled_y = round(y / y_scaling_factor)
            print(f"Converting API coordinates {x},{y} to actual coordinates {scaled_x},{scaled_y}")
            return scaled_x, scaled_y
        else:
            # Scale down to target resolution
            scaled_x = round(x * x_scaling_factor)
            scaled_y = round(y * y_scaling_factor)
            print(f"Converting actual coordinates {x},{y} to API coordinates {scaled_x},{scaled_y}")
            return scaled_x, scaled_y


class ComputerTool20241022(PyAutoGUIComputerTool, BaseAnthropicTool):
    """Computer tool version from October 22, 2024."""
    api_type: Literal["computer_20241022"] = "computer_20241022"

    def to_params(self) -> BetaToolComputerUse20241022Param:
        """Return API parameters."""
        return {"name": self.name, "type": self.api_type, **self.options}


class ComputerTool20250124(PyAutoGUIComputerTool, BaseAnthropicTool):
    """Computer tool version from January 24, 2025."""
    api_type: Literal["computer_20250124"] = "computer_20250124"

    def to_params(self):
        """Return API parameters."""
        return cast(
            BetaToolUnionParam,
            {"name": self.name, "type": self.api_type, **self.options},
        )

    async def __call__(
        self,
        *,
        action: Action_20250124,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        scroll_direction: ScrollDirection | None = None,
        scroll_amount: int | None = None,
        duration: int | float | None = None,
        key: str | None = None,
        **kwargs,
    ):
        """Handle extended actions."""
        if action in ("left_mouse_down", "left_mouse_up"):
            if coordinate is not None:
                raise ToolError(f"{action=} does not accept coordinates.")
            
            if action == "left_mouse_down":
                pyautogui.mouseDown(button='left')
            else:
                pyautogui.mouseUp(button='left')
            
            return await self.screenshot()
            
        if action == "scroll":
            if scroll_direction is None or scroll_direction not in get_args(ScrollDirection):
                raise ToolError(f"{scroll_direction=} must be 'up', 'down', 'left', or 'right'")
            if not isinstance(scroll_amount, int) or scroll_amount < 0:
                raise ToolError(f"{scroll_amount=} must be a non-negative integer")
                
            # Move mouse first if coordinates provided
            if coordinate is not None:
                x, y = self.validate_and_get_coordinates(coordinate)
                pyautogui.moveTo(x, y)
            
            # Adjust clicks value based on scroll direction
            clicks = scroll_amount
            if scroll_direction in ("down", "right"):
                clicks = -clicks
            
            # Perform vertical or horizontal scroll
            if scroll_direction in ("up", "down"):
                pyautogui.scroll(clicks)
            else:  # left or right
                pyautogui.hscroll(clicks)
            
            return await self.screenshot()
            
        if action in ("hold_key", "wait"):
            if duration is None or not isinstance(duration, (int, float)):
                raise ToolError(f"{duration=} must be a number")
            if duration < 0:
                raise ToolError(f"{duration=} must be non-negative")
            if duration > 100:
                raise ToolError(f"{duration=} is too long.")

            if action == "hold_key":
                if text is None:
                    raise ToolError(f"{action} requires text")
                
                # Press key
                pyautogui.keyDown(text)
                # Wait for specified duration
                await asyncio.sleep(duration)
                # Release key
                pyautogui.keyUp(text)
                
                return await self.screenshot()

            if action == "wait":
                await asyncio.sleep(duration)
                return await self.screenshot()

        if action in ("left_click", "right_click", "double_click", "triple_click", "middle_click"):
            # Move mouse first if coordinates provided
            if coordinate is not None:
                x, y = self.validate_and_get_coordinates(coordinate)
                pyautogui.moveTo(x, y)

            # Press key modifier if provided
            if key:
                pyautogui.keyDown(key)
            
            # Set click button and number of clicks
            button = CLICK_BUTTONS.get(action, "left")
            clicks = 1
            if action == "double_click":
                clicks = 2
            elif action == "triple_click":
                clicks = 3
                
            # Perform click
            pyautogui.click(button=button, clicks=clicks)
            
            # Release key modifier if provided
            if key:
                pyautogui.keyUp(key)
                
            return await self.screenshot()

        # Call parent method for actions not covered by extended functionality
        return await super().__call__(
            action=action, text=text, coordinate=coordinate, **kwargs
        )
