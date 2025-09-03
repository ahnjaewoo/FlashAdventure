import platform
import time
import base64
from typing import List, Dict, Optional, Callable
from io import BytesIO
from PIL import Image
import pyautogui
from .computer import Computer
from typing import Protocol, List, Literal, Dict


class LocalDesktopComputer(Computer):
    """Local desktop automation implementation - Supports Windows / Mac / Linux (with action limit measurement feature)"""

    def __init__(self, max_actions: int = 3, action_limit_callback: Optional[Callable[[], None]] = None):
        os_name = platform.system().lower()
        if "darwin" in os_name:
            self._environment = "mac"
        elif "linux" in os_name:
            self._environment = "linux"
        else:
            self._environment = "windows"
        self._dimensions = pyautogui.size()
        
        # Action counting related variables
        self._action_count = 0
        self._max_actions = max_actions
        self._action_limit_reached = False
        self._action_limit_callback = action_limit_callback
        
        # Define actions to be counted
        self._countable_actions = [
            "click", "double_click", "type", "keypress", "drag", "scroll"
        ]

    @property
    def environment(self) -> Literal["windows", "mac", "linux"]:
        return self._environment

    @property
    def dimensions(self) -> tuple[int, int]:
        return self._dimensions
    
    @property
    def action_count(self) -> int:
        """Returns the current action count"""
        return self._action_count
    
    @property
    def max_actions(self) -> int:
        """Returns the maximum number of actions"""
        return self._max_actions
    
    @property
    def action_limit_reached(self) -> bool:
        """Returns whether the action limit has been reached"""
        return self._action_limit_reached
    
    def _increment_action_counter(self, action_name: str) -> bool:
        """
        Increments the action counter and checks if the limit has been reached
        Returns True if the action is countable, otherwise returns False
        """
        if action_name in self._countable_actions:
            self._action_count += 1
            print(f"⬆️ Action counter incremented: {self._action_count}/{self._max_actions}")
            
            # Check if action limit is reached
            if self._action_count >= self._max_actions and not self._action_limit_reached:
                self._action_limit_reached = True
                print(f"🚫 Action limit reached: {self._action_count}/{self._max_actions}")
                
                # Execute callback (if provided)
                if self._action_limit_callback:
                    self._action_limit_callback()
            
            return True
        else:
            print(f"⏩ Action '{action_name}' is not counted")
            return False

    def screenshot(self) -> str:
        """
        Takes a screenshot and returns it as a base64 encoded string (uncounted action)
        """
        img = pyautogui.screenshot()
        
        # Add action counter overlay to screenshot
        if hasattr(img, 'paste'):
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("arial", 24)
                except:
                    font = ImageFont.load_default()
                
                counter_text = f"Actions: {self._action_count}/{self._max_actions}"
                text_position = (10, 10)
                
                # Text background (for improved readability)
                text_width, text_height = draw.textbbox((0, 0), counter_text, font=font)[2:4]
                draw.rectangle(
                    [text_position[0], text_position[1], 
                     text_position[0] + text_width, text_position[1] + text_height], 
                    fill=(255, 255, 255, 180)
                )
                
                # Draw text
                draw.text(text_position, counter_text, fill=(255, 0, 0), font=font)
            except Exception as e:
                print(f"⚠️ Failed to add screenshot overlay: {e}")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def click(self, x: int, y: int, button: str = "left") -> None:
        """
        Clicks the mouse at the given coordinates (counted action)
        """
        self._increment_action_counter("click")
        pyautogui.click(x=x, y=y, button=button)

    def double_click(self, x: int, y: int) -> None:
        """
        Double-clicks at the given coordinates (counted action)
        """
        self._increment_action_counter("double_click")
        pyautogui.doubleClick(x=x, y=y)

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        """
        Scrolls at the given coordinates (counted action)
        """
        self._increment_action_counter("scroll")
        pyautogui.moveTo(x, y)
        pyautogui.scroll(scroll_y)

    def type(self, text: str) -> None:
        """
        Types text (counted action)
        """
        self._increment_action_counter("type")
        pyautogui.write(text)

    def wait(self, ms: int = 1000) -> None:
        """
        Waits for the specified time (ms) (uncounted action)
        """
        time.sleep(ms / 1000)

    def move(self, x: int, y: int) -> None:
        """
        Moves the mouse pointer (uncounted action)
        """
        pyautogui.moveTo(x, y)

    def keypress(self, keys: List[str]) -> None:
        """
        Presses keys (counted action)
        """
        self._increment_action_counter("keypress")
        for key in keys:
            pyautogui.keyDown(key)
        for key in reversed(keys):
            pyautogui.keyUp(key)

    def drag(self, path: List[Dict[str, int]]) -> None:
        """
        Drags (counted action)
        """
        self._increment_action_counter("drag")
        if not path:
            return
        pyautogui.moveTo(path[0]["x"], path[0]["y"])
        pyautogui.mouseDown()
        for point in path[1:]:
            pyautogui.moveTo(point["x"], point["y"])
        pyautogui.mouseUp()

    def get_current_url(self) -> str:
        """
        Returns the current URL (uncounted action)
        """
        return "file://local-desktop"
    
    def reset_action_counter(self) -> None:
        """
        Resets the action counter
        """
        self._action_count = 0
        self._action_limit_reached = False
        print(f"🔄 Action counter reset: {self._action_count}/{self._max_actions}")