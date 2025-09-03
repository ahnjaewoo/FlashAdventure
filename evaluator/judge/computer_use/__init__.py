"""
Cross-platform computer interaction tools for Anthropic AI.
This package provides tools for AI to interact with computers running Windows, macOS, or Linux.
"""

__version__ = "0.1.0"
__author__ = "FlashAdventure"

"""
Autonomous Computer Use Agent with Claude Sonnet
"""

from .app import (
    get_screen_details,
    load_api_key,
    load_tasks,
    get_task_prompt,
    api_response_callback,
    tool_output_callback,
    message_callback,
    run_agent,
    main,
)

# loop 모듈
from .loop import (
    APIProvider,
    sampling_loop,
)

__all__ = [
    "get_screen_details",
    "load_api_key",
    "load_tasks",
    "get_task_prompt",
    "api_response_callback",
    "tool_output_callback",
    "message_callback",
    "run_agent",
    "main",
    "APIProvider",
    "sampling_loop",
]
