import pyautogui
import time
from mss import mss
from PIL import Image
from datetime import datetime
import os


class LocalController:
    def __init__(self, screenshot_dir="screenshots", game_name="None"):
        self.screenshot_dir = f"{screenshot_dir}/{game_name}"

        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def get_screenshot(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")

        with mss() as sct:
            monitor = sct.monitors[1]  
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            img.save(path)

        return path

    def execute_python_command(self, command: str):
        exec(command)

    def execute_action(self, action):
        if isinstance(action, str):
            if action == "WAIT":
                time.sleep(2)
            elif action in ["DONE", "FAIL"]:
                return
            else:
                exec(action)
        elif isinstance(action, dict):
            action_type = action.get("action_type")
            params = action.get("parameters", {})

            if action_type == "MOVE_TO":
                pyautogui.moveTo(params.get("x", 0), params.get("y", 0))
            elif action_type == "CLICK":
                pyautogui.click(params.get("x", None), params.get("y", None), button=params.get("button", "left"))
            elif action_type == "DOUBLE_CLICK":
                pyautogui.doubleClick()
            elif action_type == "TYPING":
                pyautogui.typewrite(params.get("text", ""))
            elif action_type == "KEY_DOWN":
                pyautogui.keyDown(params.get("key", ""))
            elif action_type == "KEY_UP":
                pyautogui.keyUp(params.get("key", ""))
            elif action_type == "HOTKEY":
                keys = params.get("keys", [])
                pyautogui.hotkey(*keys)
            elif action_type == "WAIT":
                time.sleep(2)
            elif action_type in ["DONE", "FAIL"]:
                pass
            else:
                print(f"Unknown action type: {action_type}")
        else:
            print("Invalid action format")

    def start_recording(self):
        print("[Recording start - no-op for local]")

    def end_recording(self, path):
        print(f"[Recording end - no-op for local] Saved to {path}")