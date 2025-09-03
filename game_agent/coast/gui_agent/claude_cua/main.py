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

import yaml
from anthropic.types import TextBlock
from anthropic.types.beta import BetaTextBlock, BetaToolUseBlock
from anthropic.types.tool_use_block import ToolUseBlock
from dotenv import load_dotenv
from screeninfo import get_monitors

from .loop import APIProvider, sampling_loop
from .tools import ToolResult

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("agent_log.txt"), logging.StreamHandler()]
)
logger = logging.getLogger("autonomous_agent")

def load_config(path: str = "config.yaml") -> dict:
    try:
        path = os.path.abspath(path)
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if not config:
                raise ValueError("Loaded config is empty or invalid.")
            return config
    except Exception as e:
        logger.error(f"Failed to load config.yaml: {e}")
        return {"max_actions": 20}

def get_screen_details():
    screens = get_monitors()
    sorted_screens = sorted(screens, key=lambda s: s.x)
    primary_index = next((i for i, s in enumerate(sorted_screens) if s.is_primary), 0)
    return [f"Screen {i + 1}: {s.width}x{s.height}" for i, s in enumerate(sorted_screens)], primary_index

screens = get_monitors()
SCREEN_NAMES, SELECTED_SCREEN_INDEX = get_screen_details()
os.environ['WIDTH'] = str(screens[SELECTED_SCREEN_INDEX].width)
os.environ['HEIGHT'] = str(screens[SELECTED_SCREEN_INDEX].height)
logger.info(f"Using screen {SCREEN_NAMES[SELECTED_SCREEN_INDEX]} (index: {SELECTED_SCREEN_INDEX})")

CONFIG_DIR = Path("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

COUNTABLE_ACTIONS = {
    "left_click", "right_click", "middle_click", "double_click", "triple_click",
    "key", "type", "hold_key", "left_click_drag", "scroll"
}

def load_api_key() -> str:
    if API_KEY_FILE.exists():
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return os.getenv("ANTHROPIC_API_KEY", "")

def tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    tool_state[tool_id] = tool_output
    if "action_count" not in tool_state:
        tool_state["action_count"] = 0

    if isinstance(tool_output.output, str):
        return

    last_tool_use = tool_state.get("_messages", [])[-1] if tool_state.get("_messages") else {}
    if isinstance(last_tool_use, dict):
        for block in last_tool_use.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                action = block.get("input", {}).get("action")
                if action in COUNTABLE_ACTIONS:
                    tool_state["action_count"] += 1
                    logger.info(f"[ACTION COUNT] {tool_state['action_count']}/{tool_state['max_actions']}")
                    if tool_state["action_count"] >= tool_state["max_actions"]:
                        tool_state["action_limit_reached"] = True
                        logger.info("[LIMIT REACHED] Max actions reached.")
                break

def message_callback(message, message_history: List, hide_images=False):
    def _render(msg, hide_images=False):
        if isinstance(msg, str): return msg
        if isinstance(msg, ToolResult):
            return msg.output or f"Error: {msg.error}" if msg.error else "[IMAGE: Screenshot captured]"
        elif isinstance(msg, (BetaTextBlock, TextBlock)):
            return msg.text
        elif isinstance(msg, (BetaToolUseBlock, ToolUseBlock)):
            return f"Tool Use: {msg.name}\nInput: {msg.input}"
        return str(msg)

    rendered = _render(message, hide_images)
    if rendered:
        message_history.append(rendered)
        logger.info(f"Message: {rendered}")
        
        
        
async def run_agent(initial_prompt: str, base_system_prompt: str = "", config_path: str = "config.yaml",
                    max_iterations: int = 3, only_n_most_recent_images: int = 2,
                    max_actions: int | None = None, agent_type: str = ""):

    state = {
        "api_key": load_api_key(),
        "model": "claude-3-7-sonnet-20250219",
        "provider": APIProvider.ANTHROPIC,
        "messages": [],
        "message_history": [],
        "tools": {"max_actions": max_actions},
        "responses": {},
        "custom_system_prompt": base_system_prompt,
        "only_n_most_recent_images": only_n_most_recent_images,
        "hide_images": False,
        "selected_screen": 1,
        "max_pixels": 1344,
        "awq_4bit": False,
        "tool_version": "computer_use_20250124",
    }

    state["messages"].append({
        "role": Sender.USER,
        "content": [{"type": "text", "text": initial_prompt}]
    })
    state["message_history"].append(f"User: {initial_prompt}")

    for iteration in range(max_iterations):
        logger.info(f"Starting iteration {iteration + 1}/{max_iterations}")

        action_count = state["tools"].get("action_count", 0)
        if action_count >= max_actions:
            logger.info("[SYSTEM] Action limit reached. Returning early.")
            return {
                "messages": state["message_history"],
                "action_count": action_count
            }


        state["tools"]["_messages"] = state["messages"]

        try:
            result = await sampling_loop(
                system_prompt_suffix=state["custom_system_prompt"],
                model=state["model"],
                provider=state["provider"],
                messages=state["messages"],
                output_callback=partial(message_callback, message_history=state["message_history"],
                                        hide_images=state["hide_images"]),
                tool_output_callback=partial(tool_output_callback, tool_state=state["tools"]),
                tool_state=state["tools"],
                api_response_callback=lambda *_: None,
                api_key=state["api_key"],
                only_n_most_recent_images=state["only_n_most_recent_images"],
                tool_version=state["tool_version"],
                thinking_budget=1024,
                token_efficient_tools_beta=False
            )

            if result is None:
                logger.info("Sampling loop returned None. Ending agent loop.")
                break

            if any(
                phrase in msg.lower()
                for msg in state["message_history"][-3:]
                for phrase in ["task completed", "successfully completed", "finished the task"]
            ):
                logger.info("Completion signal detected. Ending agent loop.")
                break

        except Exception as e:
            logger.error(f"Error in iteration {iteration + 1}: {str(e)}")
            break

    logger.info("Agent finished.")
    return {
        "messages": state["message_history"],
        "action_count": state["tools"].get("action_count", 0)
    }


async def main(user_prompt: str, system_prompt: str, type: str, config_path="config.yaml"):
    logger.info("Launching GUI Agent (Claude)...")
    
    
    config = load_config(config_path)
    max_actions = config.get("max_actions_seeker", 20) if type == "clue_seeker" else config.get("max_actions_solver", 20)

    result = await run_agent(
        initial_prompt=user_prompt,
        base_system_prompt=system_prompt,
        config_path=config_path,
        max_iterations=1,
        only_n_most_recent_images=10,
        max_actions = max_actions + 1,
        agent_type=type
    )
    # print("ACtion 결과:", result)
    return result

if __name__ == "__main__":
    asyncio.run(main("Your task prompt here", "Your system prompt here", type="clue_seeker"))