import os
import mss

def get_screenshot_dir(base_dir, cua, model_name, game_name):
    """Create directory based on game / model / agent"""
    directory = os.path.join(base_dir, cua, model_name, game_name)
    os.makedirs(directory, exist_ok=True)
    return directory

def get_next_screenshot_filename(directory):
    """Generate the next sequential screenshot filename in the given directory"""
    existing_files = [
        f for f in os.listdir(directory)
        if f.startswith("flash_screenshot_") and f.endswith(".png")
    ]

    numbers = []
    for filename in existing_files:
        try:
            num_str = filename.replace("flash_screenshot_", "").replace(".png", "")
            numbers.append(int(num_str))
        except ValueError:
            continue

    next_num = max(numbers, default=0) + 1
    return f"flash_screenshot_{next_num:04d}.png"

def capture_flash_screenshot(game_name, cua, model_name, time=None):
    """
    Capture the full screen and save it into a folder structured by GUI agent / model.
    - time=None or "": screenshots/
    - time="after": screenshots_after/
    - time="final": screenshots_final/
    """
    if time not in (None, "", "after", "final"):
        raise ValueError("Invalid value for 'time'. Use 'after', 'final', or leave it empty.")

    if time == "after":
        base_dir = "screenshots_after"
    elif time == "final":
        base_dir = "screenshots_final"
    else:
        base_dir = "screenshots"

    directory = get_screenshot_dir(base_dir, cua, model_name, game_name)
    filename = get_next_screenshot_filename(directory)
    screenshot_path = os.path.join(directory, filename)

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)

    print(f"[INFO] Screenshot saved to: {screenshot_path}")
    return screenshot_path