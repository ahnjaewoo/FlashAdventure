import os
import platform
import mss
import time
import subprocess


# OS 감지
IS_MAC = platform.system() == "Darwin"

# 🔹 스크린샷 저장 디렉토리 설정 (기본: screenshots/flashpoint/)
SCREENSHOT_DIR = "screenshots/flashpoint/"

# 저장 경로 디렉토리 생성
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def get_flashpoint_window_position():
    print(f"[INFO] Detecting Flashpoint window on {platform.system()}...")
    
    if IS_MAC:
        script = '''
        tell application "System Events"
            set window_list to name of every window of every process whose visible is true
        end tell
        return window_list
        '''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        windows = result.stdout.strip().split(", ")
        for window in windows:
            if "Flashpoint" in window:
                return 100, 100, 800, 600  # 기본값
    else:
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle("Flashpoint")
            if windows:
                window = windows[0]
                return window.left, window.top, window.width, window.height
        except ImportError:
            print("[ERROR] pygetwindow is not installed. Run: pip install pygetwindow")
    return None

def capture_flash_screenshot():
    position = get_flashpoint_window_position()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"flash_screenshot_{timestamp}.png")
    
    with mss.mss() as sct:
        if position:
            left, top, width, height = position
            monitor = {"top": top, "left": left, "width": width, "height": height}
        else:
            monitor = sct.monitors[1]
        
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
        print(f"[INFO] Screenshot saved: {screenshot_path}")
    
    return screenshot_path
