import argparse
import asyncio
import base64
import io
import json
import logging
import os
from datetime import datetime
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import List

from anthropic.types import TextBlock
from anthropic.types.beta import BetaTextBlock, BetaToolUseBlock
from anthropic.types.tool_use_block import ToolUseBlock
from dotenv import load_dotenv
from screeninfo import get_monitors

# Internal modules
from claude_computer_use.loop import APIProvider, sampling_loop
from claude_computer_use.tools import ToolResult

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.FileHandler("agent_log.txt"), logging.StreamHandler()]
)
logger = logging.getLogger("autonomous_agent")

ACTION_COUNT = 0
MAX_ACTIONS = 100

COUNTABLE_ACTIONS = [
    "left_click", "right_click", "middle_click", "double_click", "triple_click",
    "key", "type", "hold_key", "left_click_drag", "scroll"
]

def get_screen_details():
    screens = get_monitors()
    screen_details = []
    sorted_screens = sorted(screens, key=lambda s: s.x)
    primary_index = 0
    for i, screen in enumerate(sorted_screens):
        if screen.is_primary:
            primary_index = i
        screen_info = f"Screen {i + 1}: {screen.width}x{screen.height}"
        screen_details.append(screen_info)
    return screen_details, primary_index

screens = get_monitors()
SCREEN_NAMES, SELECTED_SCREEN_INDEX = get_screen_details()
os.environ['WIDTH'] = str(screens[SELECTED_SCREEN_INDEX].width)
os.environ['HEIGHT'] = str(screens[SELECTED_SCREEN_INDEX].height)

CONFIG_DIR = Path("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

def parse_args():
    parser = argparse.ArgumentParser(description="Run Autonomous Computer Use Agent")
    parser.add_argument("--task-file", type=str, default="./tasks.json", help="Path to the tasks JSON file")
    parser.add_argument("--task-name", type=str, help="Name of the task to run (optional if --task-id is provided)")
    parser.add_argument("--task-id", type=int, help="ID of the task to run (1-based index)")
    parser.add_argument("--prompt-type", type=str, default="computer_use_prompt", help="Prompt type to use")
    parser.add_argument("--max-actions", type=int, default=100, help="Maximum number of actions allowed")
    return parser.parse_args()

def load_api_key() -> str:
    if API_KEY_FILE.exists():
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set ANTHROPIC_API_KEY in your .env or ~/.anthropic/api_key file.")
    return api_key

def load_tasks(task_path: Path) -> dict:
    try:
        with open(task_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_task_prompt(tasks: dict, task_name: str, prompt_type: str = "prompt") -> str:
    if not tasks or task_name not in tasks:
        task_name = list(tasks.keys())[0] if tasks else "default"
    return tasks.get(task_name, {}).get(prompt_type, tasks.get(task_name, {}).get("prompt", "Help me use the computer."))

def api_response_callback(request, response, exception):
    if exception:
        logger.info(f"[ERROR] API: {str(exception)}")

def tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    global ACTION_COUNT, MAX_ACTIONS
    tool_state[tool_id] = tool_output
    if tool_id and isinstance(tool_id, str) and tool_id.startswith("toolu_"):
        try:
            for msg in reversed(tool_state.get("_messages", [])):
                if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                    for block in msg.get("content", []):
                        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id") == tool_id:
                            action = block.get("input", {}).get("action")
                            if action in COUNTABLE_ACTIONS:
                                ACTION_COUNT += 1
                                logger.info(f"[ACTION] {ACTION_COUNT}/{MAX_ACTIONS}")
                                if ACTION_COUNT >= MAX_ACTIONS:
                                    tool_state["action_limit_reached"] = True
                                    logger.info(f"[SYSTEM] Action limit of {MAX_ACTIONS} reached. Ending session.")
                                    if "_messages" in tool_state:
                                        tool_state["_messages"].append({
                                            "role": "user",
                                            "content": [{"type": "text", "text": f"Action limit of {MAX_ACTIONS} reached. Session will now end."}]
                                        })
                            break
        except Exception as e:
            logger.info(f"[ERROR] Counter: {e}")

def message_callback(message, message_history: List, hide_images=False):
    def _render_message(message, hide_images=False):
        if isinstance(message, str):
            return message
        if isinstance(message, ToolResult):
            return message.output if message.output else f"Error: {message.error}"
        elif isinstance(message, (BetaTextBlock, TextBlock)):
            return message.text
        elif isinstance(message, dict) and message.get("type") == "text":
            return message.get("text")
        elif isinstance(message, (BetaToolUseBlock, ToolUseBlock)):
            return f"[ACTION] {message.input['action']}" if isinstance(message.input, dict) and "action" in message.input else f"[TOOL] {message.name}"
        return str(message)

    rendered = _render_message(message, hide_images)
    if rendered:
        message_history.append(rendered)
        logger.info(rendered if rendered.startswith("[") else f"[TEXT] {rendered}")

async def run_agent(initial_prompt: str, custom_system_prompt: str = "", task_name: str = "unknown_task", max_iterations: int = 2, only_n_most_recent_images: int = 2):
    global ACTION_COUNT
    ACTION_COUNT = 0

    safe_task_name = task_name.replace(" ", "_").replace(":", "").replace("/", "_")
    log_dir = Path(f"./log/{safe_task_name}")
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["SCREENSHOT_DIR"] = str(log_dir / "screenshots")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = log_dir / f"conversation_{safe_task_name}_{timestamp}.txt"

    state = {
        "api_key": load_api_key(),
        "model": "claude-3-7-sonnet-20250219",
        "provider": APIProvider.ANTHROPIC,
        "messages": [],
        "message_history": [],
        "tools": {},
        "responses": {},
        "custom_system_prompt": custom_system_prompt,
        "only_n_most_recent_images": only_n_most_recent_images,
        "hide_images": False,
        "selected_screen": 1,
        "max_pixels": 1344,
        "awq_4bit": False,
        "tool_version": "computer_use_20250124",
        "action_limit_reached": False,
    }

    state["messages"].append({"role": Sender.USER, "content": [{"type": "text", "text": initial_prompt}]})
    state["message_history"].append(f"User: {initial_prompt}")

    try:
        for iteration in range(max_iterations):
            if state.get("action_limit_reached") or state["tools"].get("action_limit_reached"):
                logger.info(f"[SYSTEM] Action limit of {MAX_ACTIONS} reached. Ending session.")
                state["message_history"].append(f"[SYSTEM] Action limit of {MAX_ACTIONS} reached. Ending session.")
                break

            state["tools"]["_messages"] = state["messages"]

            result = await sampling_loop(
                system_prompt_suffix=state["custom_system_prompt"],
                model=state["model"],
                provider=state["provider"],
                messages=state["messages"],
                output_callback=partial(message_callback, message_history=state["message_history"], hide_images=state["hide_images"]),
                tool_output_callback=partial(tool_output_callback, tool_state=state["tools"]),
                api_response_callback=api_response_callback,
                api_key=state["api_key"],
                only_n_most_recent_images=state["only_n_most_recent_images"],
                tool_version=state["tool_version"],
                thinking_budget=1024,
                token_efficient_tools_beta=False
            )

            if result is None:
                break

            if state["tools"].get("action_limit_reached"):
                state["action_limit_reached"] = True
                state["message_history"].append(f"[SYSTEM] Action limit of {MAX_ACTIONS} reached. Ending session.")
                break

    except Exception as e:
        logger.info(f"[ERROR] Iteration: {e}")
        state["message_history"].append(f"[ERROR] {str(e)}")

    finally:
        state["message_history"].append(f"[SYSTEM] Final action count: {ACTION_COUNT}/{MAX_ACTIONS}")
        with open("your_output_file.txt", "w", encoding="utf-8") as f:
            for message in state["message_history"]:
                f.write(f"{message}\n\n")
        logger.info(f"Saved to {output_file}")

    return state["message_history"]

async def main():
    global args, MAX_ACTIONS
    args = parse_args()
    MAX_ACTIONS = args.max_actions

    task_file_path = Path(args.task_file)
    tasks = load_tasks(task_file_path)

    task_keys = list(tasks.keys())
    print("\nAvailable Tasks:")
    for i, task_key in enumerate(task_keys, 1):
        print(f"{i}. {task_key}")

    if args.task_name:
        task_name = args.task_name
    elif args.task_id and 1 <= args.task_id <= len(task_keys):
        task_name = task_keys[args.task_id - 1]
        print(f"\nSelected Task [{args.task_id}]: {task_name}")
    else:
        selected_id = int(input("\nEnter the number of the task to run: "))
        if 1 <= selected_id <= len(task_keys):
            task_name = task_keys[selected_id - 1]
            print(f"\nSelected Task [{selected_id}]: {task_name}")
        else:
            raise ValueError("Invalid task number.")

    prompt_type = args.prompt_type
    prompt = get_task_prompt(tasks, task_name, prompt_type)
    system_prompt = get_task_prompt(tasks, task_name, 'system_prompt')

    await run_agent(
        initial_prompt=prompt,
        custom_system_prompt=system_prompt,
        task_name=task_name,
        max_iterations=3,
        only_n_most_recent_images=10,
    )

if __name__ == "__main__":
    asyncio.run(main())