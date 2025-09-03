import base64
import json
import asyncio
import os
import re
from typing import Dict, Any, Tuple
from openai import AsyncOpenAI
from PIL import Image
import io
from dotenv import load_dotenv

from api import api_caller
from . import LocalDesktopComputer


# --- JSON Extraction Utility ---
def extract_json_from_text(text: str) -> dict | None:
    if "```" in text:
        text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r'\{[\s\S]*?\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed (regex-based): {e}")
    return None


# --- GUI Action Execution ---
def execute_gui_action(action: Dict[str, Any], computer: LocalDesktopComputer):
    action_type = action.get("type")
    print(f"\n🎯 Action to be executed: {action}")

    match action_type:
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
        case "keyboard":
            key = action.get("key")
            if not key:
                print("⚠️ 'keyboard' action has no 'key' value. Ignoring.")
                return
            computer.keypress([key])
        case "drag":
            computer.drag(action["path"])
        case _:
            print(f"⚠️ Unsupported action type (ignoring): {action_type}")
            return


# --- Plan Formulation (including API errors, max 3 retries) ---
async def plan_with_api_caller(
    user_goal: str,
    encoded_image: str,
    api_provider: str = "openai",
    model_name: str = "gpt-4o",
    max_retries: int = 3
) -> Dict[str, Any]:
    system_prompt = "You are a GUI agent that returns a single GUI action in JSON format."

    move_prompt = f'''
Goal: {user_goal}

You must return exactly one GUI action in JSON format using one of the following types:

- "click": Click at a specific (x, y). e.g. {{ "type": "click", "description": "green start button" }}
- "double_click": Double-click at (x, y)
- "scroll": Scroll starting from (x, y) using scroll_y. e.g. {{ "type": "scroll", "description": "scroll down panel" }}
- "type": Type a string. e.g. {{ "type": "type", "text": "hello" }}
- "keypress": Press one or more keys. e.g. {{ "type": "keypress", "keys": ["space"] }}
- "drag": Drag the mouse along a path. e.g. {{ "type": "drag", "description": "slide the slider" }}

⚠️ DO NOT include "x" or "y" fields. Leave spatial grounding (location) to a separate system.
⚠️ DO NOT use "keyboard". Use "keypress" instead.
⚠️ Only return the action as a valid JSON object. Do not explain or comment.
'''

    for attempt in range(1, max_retries + 1):
        try:
            result = api_caller(
                api_provider=api_provider,
                system_prompt=system_prompt,
                model_name=model_name,
                move_prompts=move_prompt,
                base64_images=[encoded_image]
            )
        except Exception as e:
            print(f"❌ API call failed (attempt {attempt}): {e}")
            if attempt == max_retries:
                return {"type": "noop", "description": "API call failed after retries"}
            await asyncio.sleep(1.5)
            continue

        result = result.strip()
        print(f"\n🧾 Model response (attempt {attempt}):\n{result}")

        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        extracted = extract_json_from_text(result)
        if extracted:
            return extracted

        print(f"⚠️ JSON parsing failed (attempt {attempt})")
        if attempt == max_retries:
            return {"type": "noop", "description": "Failed to parse model response"}
        await asyncio.sleep(1.5)


# --- Grounding Coordinate Calculation ---
async def ground_with_uground(target_description: str, encoded_image: str, client: AsyncOpenAI) -> Tuple[int, int]:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}},
                {"type": "text", "text": f"""
Your task is to help find the pixel coordinates (x, y) of the element described as:
"{target_description}"

Answer with a string in the form: (x, y)
"""}
            ]
        }
    ]

    response = await client.chat.completions.create(
        model="osunlp/UGround-V1-7B",
        messages=messages,
        temperature=0
    )

    x_ratio, y_ratio = eval(response.choices[0].message.content.strip())

    img_data = base64.b64decode(encoded_image)
    img = Image.open(io.BytesIO(img_data))
    w, h = img.size
    return int(x_ratio / 1000 * w), int(y_ratio / 1000 * h)


# --- Full Agent Execution ---
async def agent_step(
    user_prompt: str,
    encoded_image: str,
    provider: str = "openai",
    model: str = "gpt-4o"
) -> int:
    load_dotenv()
    computer = LocalDesktopComputer()

    # 1. Plan Formulation
    plan = await plan_with_api_caller(
        user_goal=user_prompt,
        encoded_image=encoded_image,
        api_provider=provider,
        model_name=model,
        max_retries=3
    )
    print(f"\n🧠 Model response plan: {plan}")

    # 2. If grounding is needed
    if plan["type"] in ["click", "double_click", "drag", "scroll"]:
        client_uground = AsyncOpenAI(api_key="empty", base_url="...")
        x, y = await ground_with_uground(plan["description"], encoded_image, client_uground)
        plan["x"] = x
        plan["y"] = y

    # 3. Execution (ignore errors)
    try:
        execute_gui_action(plan, computer)
    except Exception as e:
        print(f"⚠️ An error occurred during action execution (ignoring and continuing): {e}")

    return computer.action_count