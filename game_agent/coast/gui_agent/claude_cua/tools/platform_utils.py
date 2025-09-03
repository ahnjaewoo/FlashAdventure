"""Utility module to handle platform-specific operations."""

import os
import platform
import shutil
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, Union


class Platform(Enum):
    """Enum representing supported platforms."""
    LINUX = "linux"
    MACOS = "darwin"
    WINDOWS = "windows"


def get_platform() -> Platform:
    """Get the current platform."""
    system = platform.system().lower()
    if system == "linux":
        return Platform.LINUX
    elif system == "darwin":
        return Platform.MACOS
    elif system == "windows":
        return Platform.WINDOWS
    else:
        raise ValueError(f"Unsupported platform: {system}")


class PlatformManager:
    """Manage platform-specific operations."""

    def __init__(self):
        self.platform = get_platform()
        self._setup_paths()
        self._check_dependencies()

    def _setup_paths(self):
        """Set up platform-specific paths."""
        if self.platform == Platform.WINDOWS:
            self.temp_dir = Path(os.environ.get("TEMP", "C:/temp"))
            self.output_dir = self.temp_dir / "outputs"
        else:  # Linux or macOS
            self.temp_dir = Path("/tmp")
            self.output_dir = self.temp_dir / "outputs"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _check_dependencies(self):
        """Check if required dependencies are installed."""
        if self.platform == Platform.LINUX:
            self.has_xdotool = bool(shutil.which("xdotool"))
            self.has_gnome_screenshot = bool(shutil.which("gnome-screenshot"))
            self.has_scrot = bool(shutil.which("scrot"))
            self.screenshot_cmd = "gnome-screenshot" if self.has_gnome_screenshot else "scrot"
        elif self.platform == Platform.MACOS:
            self.has_screencapture = bool(shutil.which("screencapture"))
        elif self.platform == Platform.WINDOWS:
            # Check for PowerShell
            self.has_powershell = bool(shutil.which("powershell.exe"))

    def get_shell_command(self) -> str:
        """Get the appropriate shell command for the platform."""
        if self.platform == Platform.WINDOWS:
            return "powershell.exe"
        else:
            return "/bin/bash"

    def get_screenshot_command(self, output_path: Union[str, Path]) -> str:
        """Get the appropriate screenshot command for the platform."""
        output_path = str(output_path)
        
        if self.platform == Platform.LINUX:
            if self.has_gnome_screenshot:
                return f"gnome-screenshot -f {output_path} -p"
            elif self.has_scrot:
                return f"scrot -p {output_path}"
            raise RuntimeError("No screenshot tool found on Linux. Install gnome-screenshot or scrot.")
        
        elif self.platform == Platform.MACOS:
            if self.has_screencapture:
                return f"screencapture -x {output_path}"
            raise RuntimeError("screencapture command not found on macOS.")
        
        elif self.platform == Platform.WINDOWS:
            # PowerShell command to take screenshot
            return f'powershell.exe -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\'%{{{{{output_path}}}}}%\'\); Start-Sleep -Milliseconds 500; $bmp=New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $graphics=[System.Drawing.Graphics]::FromImage($bmp); $graphics.CopyFromScreen((New-Object System.Drawing.Point(0,0)), (New-Object System.Drawing.Point(0,0)), $bmp.Size); $bmp.Save(\'{output_path}\'); $graphics.Dispose(); $bmp.Dispose()"'

    def simulate_mouse_click(self, x: int, y: int, button: str = "left") -> str:
        """Get command to simulate mouse click at coordinates."""
        if self.platform == Platform.LINUX:
            button_map = {"left": "1", "right": "3", "middle": "2"}
            btn = button_map.get(button, "1")
            return f"xdotool mousemove {x} {y} click {btn}"
        
        elif self.platform == Platform.MACOS:
            # macOS uses AppleScript for mouse events
            button_map = {"left": "1", "right": "2", "middle": "3"}
            btn = button_map.get(button, "1")
            return f'''osascript -e 'tell application "System Events" to tell process "Finder" to click at {{{x}, {y}}} using button {btn}' '''
        
        elif self.platform == Platform.WINDOWS:
            button_map = {"left": "left", "right": "right", "middle": "middle"}
            btn = button_map.get(button, "left")
            return f'powershell.exe -Command "[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y}); $mouse = [System.Windows.Forms.MouseOperations]; $mouse::{btn}MouseDown(); $mouse::{btn}MouseUp()"'
        
        return ""

    def simulate_key_press(self, key: str) -> str:
        """Get command to simulate key press."""
        if self.platform == Platform.LINUX:
            return f"xdotool key {key}"
        
        elif self.platform == Platform.MACOS:
            # This is simplified; actual implementation would need to map keys appropriately
            return f'''osascript -e 'tell application "System Events" to keystroke "{key}"' '''
        
        elif self.platform == Platform.WINDOWS:
            return f'powershell.exe -Command "[System.Windows.Forms.SendKeys]::SendWait(\'{key}\')"'
        
        return ""

    def get_screen_resolution(self) -> Tuple[int, int]:
        """Get the screen resolution."""
        if self.platform == Platform.LINUX:
            try:
                cmd = "xdpyinfo | grep dimensions | awk '{print $2}'"
                result = subprocess.check_output(cmd, shell=True, text=True).strip()
                width, height = map(int, result.split('x'))
                return width, height
            except Exception:
                return 1024, 768  # Default fallback
        
        elif self.platform == Platform.MACOS:
            try:
                cmd = "system_profiler SPDisplaysDataType | grep Resolution | awk '{print $2, $4}'"
                result = subprocess.check_output(cmd, shell=True, text=True).strip().split('\n')[0]
                width, height = map(int, result.split())
                return width, height
            except Exception:
                return 1440, 900  # Default fallback for macOS
        
        elif self.platform == Platform.WINDOWS:
            try:
                cmd = 'powershell.exe -Command "[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height"'
                result = subprocess.check_output(cmd, shell=True, text=True).strip().split('\n')
                width, height = int(result[0]), int(result[1])
                return width, height
            except Exception:
                return 1920, 1080  # Default fallback for Windows
        
        return 1024, 768  # Default fallback