"""
Autonomous Computer Use Agent with Claude Sonnet
"""

import platform
import asyncio
import base64
import os
import io
import json
from datetime import datetime
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import cast, Dict, List, Optional, Callable, Any
import logging

from anthropic import APIResponse
from anthropic.types import TextBlock
from anthropic.types.beta import BetaMessage, BetaTextBlock, BetaToolUseBlock, BetaMessageParam, BetaContentBlockParam
from anthropic.types.tool_use_block import ToolUseBlock

from screeninfo import get_monitors

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("autonomous_agent")

# Get screen details
screens = get_monitors()
logger.info(f"Detected screens: {screens}")

from claude_computer_use.loop import (
    APIProvider,
    sampling_loop
)

from claude_computer_use.tools import ToolResult

def get_screen_details():
    screens = get_monitors()
    screen_details = []

    # Sort screens by x position to arrange from left to right
    sorted_screens = sorted(screens, key=lambda s: s.x)

    # Loop through sorted screens and assign positions
    primary_index = 0
    for i, screen in enumerate(sorted_screens):
        if i == 0:
            layout = "Left"
        elif i == len(sorted_screens) - 1:
            layout = "Right"
        else:
            layout = "Center"
        
        if screen.is_primary:
            position = "Primary" 
            primary_index = i
        else:
            position = "Secondary"
        screen_info = f"Screen {i + 1}: {screen.width}x{screen.height}, {layout}, {position}"
        screen_details.append(screen_info)

    return screen_details, primary_index


# Initialize screen details
SCREEN_NAMES, SELECTED_SCREEN_INDEX = get_screen_details()
os.environ['WIDTH'] = str(screens[SELECTED_SCREEN_INDEX].width)
os.environ['HEIGHT'] = str(screens[SELECTED_SCREEN_INDEX].height)
logger.info(f"Using screen {SCREEN_NAMES[SELECTED_SCREEN_INDEX]} (index: {SELECTED_SCREEN_INDEX})")

# Configuration setup
CONFIG_DIR = Path("~/.anthropic").expanduser()
API_KEY_FILE = CONFIG_DIR / "api_key"
TASKS_FILE = Path("./tasks.json")  # New JSON format with tasks

# Warning for security
WARNING_TEXT = "⚠️ Security Alert: Never provide access to sensitive accounts or data, as malicious web content can hijack Claude's behavior"
logger.warning(WARNING_TEXT)


class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"


def load_api_key() -> str:
    """Load API key from file or environment"""
    if API_KEY_FILE.exists():
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    
    # Try to get from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Please set ANTHROPIC_API_KEY environment variable or create ~/.anthropic/api_key file")
    return api_key


def load_tasks() -> dict:
    """Load tasks from JSON file"""
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load tasks: {e}")
        return {}


def get_task_prompt(tasks: dict, task_name: str, prompt_type: str = "prompt") -> str:
    """
    Get a specific prompt from a task
    
    Args:
        tasks: Dictionary of tasks
        task_name: Name of the task to retrieve
        prompt_type: Type of prompt to retrieve (prompt, evaluation_prompt, etc.)
        
    Returns:
        The prompt text
    """
    if not tasks:
        logger.warning("No tasks available")
        return "Help me use the computer to complete a task."
    
    # If task doesn't exist, use the first one
    if task_name not in tasks:
        logger.warning(f"Task '{task_name}' not found, using first available task")
        task_name = list(tasks.keys())[0]
    
    # Get the specified prompt type
    try:
        if prompt_type in tasks[task_name]:
            return tasks[task_name][prompt_type]
        else:
            logger.warning(f"Prompt type '{prompt_type}' not found in task '{task_name}', using 'prompt' instead")
            return tasks[task_name]["prompt"]
    except KeyError as e:
        logger.error(f"Error retrieving prompt: {e}")
        return "Help me use the computer to complete a task."


def api_response_callback(request, response, exception):
    """Callback for API responses"""
    response_id = datetime.now().isoformat()
    # 예외 로깅
    if exception:
        logger.error(f"API error: {str(exception)}")
    logger.info(f"Received API response: {response_id}")



def tool_output_callback(tool_output: ToolResult, tool_id: str, tool_state: dict):
    """Callback for tool outputs"""
    tool_state[tool_id] = tool_output
    
    # Log tool usage
    if tool_output.error:
        logger.warning(f"Tool error {tool_id}: {tool_output.error[:100]}...")
    elif tool_output.output:
        logger.info(f"Tool output {tool_id}: {tool_output.output[:100]}...")
    elif tool_output.base64_image:
        logger.info(f"Tool produced image {tool_id}")


def message_callback(message, message_history: List, hide_images=False):
    """Handle messages from the model"""
    def _render_message(message: str | BetaTextBlock | BetaToolUseBlock | ToolResult, hide_images=False):
        if isinstance(message, str):
            return message
        
        is_tool_result = not isinstance(message, str) and (
            isinstance(message, ToolResult)
            or message.__class__.__name__ == "ToolResult"
            or message.__class__.__name__ == "CLIResult"
        )
        
        if not message or (
            is_tool_result
            and hide_images
            and not hasattr(message, "error")
            and not hasattr(message, "output")
        ):
            return None
        
        # Render tool result
        if is_tool_result:
            message = cast(ToolResult, message)
            if message.output:
                return message.output
            if message.error:
                return f"Error: {message.error}"
            if message.base64_image and not hide_images:
                return f"[IMAGE: Screenshot captured]"
        elif isinstance(message, BetaTextBlock) or isinstance(message, TextBlock):
            return message.text
        elif isinstance(message, BetaToolUseBlock) or isinstance(message, ToolUseBlock):
            return f"Tool Use: {message.name}\nInput: {message.input}"
        else:
            return str(message)

    rendered = _render_message(message, hide_images)
    if rendered:
        message_history.append(rendered)
        logger.info(f"Message: {rendered}")




async def run_agent(
    initial_prompt: str,
    custom_system_prompt: str = "",
    max_iterations: int = 2,
    only_n_most_recent_images: int = 2,
):
    """Run the autonomous agent with a given prompt"""
    # Initialize state
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
    
    # Add to message history
    state["message_history"].append(f"User: {initial_prompt}")
    
    # Run the agent loop
    iteration = 0
    
    while iteration < max_iterations:
        logger.info(f"Starting iteration {iteration + 1}/{max_iterations}")
        
        try:
            messages_result = await sampling_loop(
                system_prompt_suffix=state["custom_system_prompt"],
                model=state["model"],
                provider=state["provider"],
                messages=state["messages"],
                output_callback=partial(message_callback, message_history=state["message_history"], hide_images=state["hide_images"]),
                tool_output_callback=partial(tool_output_callback, tool_state=state["tools"]),
                api_response_callback=api_response_callback,  # partial을 사용하지 않음
                api_key=state["api_key"],
                only_n_most_recent_images=state["only_n_most_recent_images"],
                tool_version=state["tool_version"],
                thinking_budget= 1024,
                token_efficient_tools_beta=False
            )
            
            # Check if the sampling loop returned None, which indicates completion
            if messages_result is None:
                logger.info("Sampling loop returned None, ending agent loop.")
                break
            
            # Check for completion signal in the last message
            last_messages = state["message_history"][-3:]  # Check the last few messages
            completion_signals = ["task completed", "finished the task", "successfully completed", "New Suspect: "]
            
            if any(signal.lower() in msg.lower() for signal in completion_signals for msg in last_messages):
                logger.info("Task completion detected. Ending agent loop.")
                break
                
        except Exception as e:
            logger.error(f"Error in iteration {iteration}: {str(e)}")
            break
            
        # Increment iteration counter
        iteration += 1
        
    logger.info(f"Agent completed after {iteration} iterations")
    
    # Print final conversation history
    logger.info("=== Final Conversation History ===")
    for msg in state["message_history"]:
        logger.info(msg)
    
    return state["message_history"]


async def main():
    """Main entry point"""
    logger.info("Starting Autonomous Computer Use Agent")
    
    # Load tasks from file or use defaults
    tasks = load_tasks()
    # if not tasks:
    #     logger.info("Using default tasks")
    #     tasks = get_default_tasks()
    
    # Specify which task to run
    task_name = "sherlock_holmes_the_tea_shop_murder_mystery"
    
    # Specify which prompt type to use
    prompt_type = "computer_use_prompt"
    
    # Get the prompt
    prompt = get_task_prompt(tasks, task_name, prompt_type)
    logger.info(f"Running task: {task_name} with prompt type: {prompt_type}, prompt: {prompt}")
    
    # System prompt
    system_prompt = "You are a helpful computer use assistant. Complete the task efficiently and autonomously."
    
    # Run the agent
    conversation = await run_agent(
        initial_prompt=prompt,
        custom_system_prompt=system_prompt,
        max_iterations=2,  # Adjust as needed
        only_n_most_recent_images=5,  # Keep last 2 screenshots
    )
    
    # Save the conversation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"conversation_{timestamp}.txt", "w") as f:
        for message in conversation:
            f.write(f"{message}\n\n")
    
    logger.info(f"Conversation saved to conversation_{timestamp}.txt")


if __name__ == "__main__":
    asyncio.run(main())