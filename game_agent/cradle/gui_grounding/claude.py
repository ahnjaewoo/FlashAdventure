from api import api_caller
from gui_grounding import LocalDesktopComputer
import base64
import asyncio
import json
import pyautogui
import re

# Reference resolution for Claude grounding
GROUNDING_WIDTH = 1366
GROUNDING_HEIGHT = 768

def resize_coordinates(coords):
    """Improved coordinate transformation logic"""
    screen_width, screen_height = pyautogui.size()
    
    # Calculate ratio
    x_ratio = screen_width / GROUNDING_WIDTH
    y_ratio = screen_height / GROUNDING_HEIGHT
    
    # Apply transformation - keep decimal precision then round
    new_x = round(coords[0] * x_ratio)
    new_y = round(coords[1] * y_ratio)
    
    # Detailed debug log
    print(f"Original coordinates: ({coords[0]}, {coords[1]})")
    print(f"Screen resolution: {screen_width}x{screen_height}, Reference resolution: {GROUNDING_WIDTH}x{GROUNDING_HEIGHT}")
    print(f"Scaling ratios: X={x_ratio:.4f}, Y={y_ratio:.4f}")
    print(f"Transformed coordinates: ({new_x}, {new_y})")
    
    # Ensure coordinates are within screen boundaries
    new_x = max(0, min(new_x, screen_width - 1))
    new_y = max(0, min(new_y, screen_height - 1))
    
    return [new_x, new_y]

def extract_json_from_response(response):
    """Extract JSON block from Claude response"""
    # Regex for JSON object
    json_pattern = r'({[\s\S]*})'
    match = re.search(json_pattern, response)
    
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try extracting JSON inside backticks (``` ... ```)
    code_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(code_pattern, response)
    
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Last resort: try parsing the whole response as JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError("No valid JSON found in response.")

def execute_gui_action(action: dict, computer: LocalDesktopComputer):
    print(f"\n🎯 Executing action: {action}")
    try:
        match action.get("type"):
            case "click":
                computer.click(action["x"], action["y"])
            case "double_click":
                computer.double_click(action["x"], action["y"])
            case "scroll":
                computer.scroll(
                    action["x"], action["y"],
                    action.get("scroll_x", 0),
                    action.get("scroll_y", 0),
                )
            case "type":
                computer.type(action["text"])
            case "keypress":
                computer.keypress(action["keys"])
            case "drag":
                computer.drag(action["path"])
            case "keyboard":
                key = action.get("key")
                if key:
                    computer.keypress([key])
                else:
                    print("⚠️ 'keyboard' action missing key. Ignored.")
            case _:
                print(f"⚠️ Unsupported action type: {action.get('type')} (ignored)")
    except Exception as e:
        print(f"⚠️ Error during action execution: {e} (ignored and continuing)")

async def run_claude_gui_agent(description: str, encoded_image: str, max_retries: int = 3) -> int:
    computer = LocalDesktopComputer()

    # Provide Claude with clearer instructions
    system_prompt = """You are a GUI automation agent that precisely identifies UI elements on the screen.
Always return ONLY a valid JSON object with exact pixel coordinates.
Your coordinates should be based on a reference resolution of 1366x768.
Be extremely precise in identifying the center of visual elements."""

    move_prompt = f"""
Goal: {description}

Examine the screenshot carefully and identify the exact pixel coordinates of the UI element that matches the goal.
Be extremely precise about the pixel coordinates - the exact center of the target element.

Choose one GUI action from this list:
- "click"        → Click at (x, y)
- "double_click" → Double-click at (x, y)
- "scroll"       → Scroll from (x, y) with scroll_y
- "type"         → Type a string
- "keypress"     → Press one or more keys (e.g., ["space"])
- "drag"         → Drag along a path (list of x/y coordinates)

Important: 
1. Return ONLY a JSON object with no explanation
2. Use a reference resolution of 1366x768
3. DO NOT use unsupported types like "keyboard"

Example of correct response:
{{ "type": "click", "x": 412, "y": 288 }}
"""

    for attempt in range(1, max_retries + 1):
        try:
            response = api_caller(
                api_provider="anthropic",
                system_prompt=system_prompt,
                model_name="claude-3-7-sonnet-20250219",
                move_prompts=move_prompt,
                base64_images=[encoded_image]
            )
            response = response.strip()
            print(f"\n🧾 Claude response (attempt {attempt}):\n{response}")
            
            # More robust JSON parsing
            try:
                action = extract_json_from_response(response)
            except ValueError as e:
                print(f"JSON parsing error: {e}")
                if attempt == max_retries:
                    raise
                await asyncio.sleep(1.5)
                continue

            # Store original coordinates
            original_x, original_y = None, None
            if "x" in action and "y" in action:
                original_x, original_y = action["x"], action["y"]
                
                # Apply coordinate resizing
                action["x"], action["y"] = resize_coordinates([original_x, original_y])
                
                # Show transformation result
                print(f"🎯 Final coordinates: ({action['x']}, {action['y']})")

            execute_gui_action(action, computer)
            return computer.action_count

        except Exception as e:
            print(f"⚠️ Claude API failure or response parsing error (attempt {attempt}): {e}")
            if attempt == max_retries:
                print("❌ Final attempt failed. Returning noop.")
                return 0
            await asyncio.sleep(1.5)

    return 0  # fallback

# Usage example
if __name__ == "__main__":
    import sys
    from pathlib import Path

    def encode_image_base64(image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    # Allow image path and description to be passed via command line arguments
    if len(sys.argv) > 2:
        test_image = sys.argv[1]
        description = sys.argv[2]
    else:
        # Defaults
        test_image = "./screenshots/flash_screenshot_0001.png"
        description = "Click the green start button"
    
    print(f"Image: {test_image}")
    print(f"Goal: {description}")
    
    encoded = encode_image_base64(test_image)
    asyncio.run(run_claude_gui_agent(description, encoded))