"""
Autonomous Computer Use Agent with Claude Sonnet
"""

import argparse
import asyncio
import json
import logging
import os
from datetime import datetime
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import cast, List

from anthropic.types import TextBlock
from anthropic.types.beta import BetaTextBlock, BetaToolUseBlock
from anthropic.types.tool_use_block import ToolUseBlock
from dotenv import load_dotenv
from screeninfo import get_monitors

# Internal modules
from judge.computer_use import APIProvider, sampling_loop
from judge.computer_use.tools import ToolResult

# Load environment variables from .env
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("agent_log.txt"), logging.StreamHandler()]
)
logger = logging.getLogger("autonomous_agent")

# Screen setup
def get_screen_details():
    screens = get_monitors()
    screen_details = []

    sorted_screens = sorted(screens, key=lambda s: s.x)
    primary_index = 0

    for i, screen in enumerate(sorted_screens):
        layout = "Left" if i == 0 else "Right" if i == len(sorted_screens) - 1 else "Center"
        position = "Primary" if screen.is_primary else "Secondary"
        if screen.is_primary:
            primary_index = i
        screen_info = f"Screen {i + 1}: {screen.width}x{screen.height}, {layout}, {position}"
        screen_details.append(screen_info)

    return screen_details, primary_index

# Init screen info
screens = get_monitors()
SCREEN_NAMES, SELECTED_SCREEN_INDEX = get_screen_details()
os.environ['WIDTH'] = str(screens[SELECTED_SCREEN_INDEX].width)
os.environ['HEIGHT'] = str(screens[SELECTED_SCREEN_INDEX].height)
logger.info(f"Using screen {SCREEN_NAMES[SELECTED_SCREEN_INDEX]} (index: {SELECTED_SCREEN_INDEX})")

# Config
CONFIG_DIR = Path("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"
logger.warning("⚠️ Security Alert: Never provide access to sensitive accounts or data.")

# Enums
class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

# Argument parser
def parse_args():
    parser = argparse.ArgumentParser(description="Run Autonomous Computer Use Agent")
    parser.add_argument("--task-file", type=str, default="./tasks.json", help="Path to the tasks JSON file")
    parser.add_argument("--task-name", type=str, required=True, help="Name of the task to run")
    parser.add_argument("--prompt-type", type=str, default="computer_use_prompt", help="Prompt type to use")
    return parser.parse_args()

# API key loader
def load_api_key() -> str:
    if API_KEY_FILE.exists():
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set ANTHROPIC_API_KEY in your .env or ~/.anthropic/api_key file.")
    return api_key

# Load tasks
def load_tasks(task_path: Path) -> dict:
    try:
        with open(task_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load tasks: {e}")
        return {}

# Get prompt
def get_task_prompt(tasks: dict, task_name: str, prompt_type: str = "prompt") -> str:
    if not tasks:
        logger.warning("No tasks available.")
        return "Help me use the computer to complete a task."
    if task_name not in tasks:
        logger.warning(f"Task '{task_name}' not found. Defaulting to first task.")
        task_name = list(tasks.keys())[0]
    return tasks[task_name].get(prompt_type, tasks[task_name].get("prompt", "Help me use the computer."))

# Callbacks
def api_response_callback(request, response, exception):
    if exception:
        logger.error(f"API error: {str(exception)}")
    else:
        logger.info("Received API response.")

def tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    tool_state[tool_id] = tool_output
    if tool_output.error:
        logger.warning(f"Tool error {tool_id}: {tool_output.error[:100]}...")
    elif tool_output.output:
        logger.info(f"Tool output {tool_id}: {tool_output.output[:100]}...")
    elif tool_output.base64_image:
        logger.info(f"Tool produced image {tool_id}")

def message_callback(message, message_history: List, hide_images=False):
    def _render(msg, hide_images=False):
        if isinstance(msg, str):
            return msg
        is_tool_result = isinstance(msg, ToolResult) or msg.__class__.__name__ in ["ToolResult", "CLIResult"]
        if not msg or (is_tool_result and hide_images and not hasattr(msg, "output")):
            return None
        if is_tool_result:
            msg = cast(ToolResult, msg)
            if msg.output:
                return msg.output
            if msg.error:
                return f"Error: {msg.error}"
            if msg.base64_image and not hide_images:
                return "[IMAGE: Screenshot captured]"
        elif isinstance(msg, (BetaTextBlock, TextBlock)):
            return msg.text
        elif isinstance(msg, (BetaToolUseBlock, ToolUseBlock)):
            return f"Tool Use: {msg.name}\nInput: {msg.input}"
        return str(msg)

    rendered = _render(message, hide_images)
    if rendered:
        message_history.append(rendered)
        logger.info(f"Message: {rendered}")

# Core agent runner
async def run_agent(initial_prompt: str, custom_system_prompt: str = "", max_iterations: int = 2, only_n_most_recent_images: int = 2):
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
    }

    state["messages"].append({
        "role": Sender.USER,
        "content": [{"type": "text", "text": initial_prompt}],
    })
    state["message_history"].append(f"User: {initial_prompt}")

    for iteration in range(max_iterations):
        logger.info(f"Starting iteration {iteration + 1}/{max_iterations}")
        try:
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
                logger.info("Sampling loop returned None. Ending agent loop.")
                break

            last_msgs = state["message_history"][-3:]
            if any(phrase in msg.lower() for msg in last_msgs for phrase in ["task completed", "successfully completed", "finished the task", "new suspect"]):
                logger.info("Completion signal detected. Ending agent loop.")
                break

        except Exception as e:
            logger.error(f"Error in iteration {iteration + 1}: {str(e)}")
            break

    logger.info(f"Agent completed after {iteration + 1} iterations")
    logger.info("=== Final Conversation History ===")
    for msg in state["message_history"]:
        logger.info(msg)

    return state["message_history"]  # ✅ 전체 conversation 반환

# Main entry
async def main():
    args = parse_args()

    task_file_path = Path(args.task_file)
    task_name = args.task_name
    prompt_type = args.prompt_type

    logger.info("Loading tasks...")
    tasks = load_tasks(task_file_path)
    prompt = get_task_prompt(tasks, task_name, prompt_type)
    logger.info(f"Running task: {task_name} with prompt type: {prompt_type} prompt: {prompt}")

    system_prompt = "You are a helpful computer use assistant. Complete the task efficiently and autonomously."
    conversation = await run_agent(
        initial_prompt=prompt,
        custom_system_prompt=system_prompt,
        max_iterations=2,
        only_n_most_recent_images=5,
    )

    # Save log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"./log/conversation_{task_name}_{timestamp}.txt"
    with open(output_file, "w") as f:
        for message in conversation:
            f.write(f"{message}\n\n")
    logger.info(f"Conversation saved to {output_file}")

    return conversation  # ✅ run_milestone에서 받을 수 있게 반환

# Run entry point
if __name__ == "__main__":
    asyncio.run(main())