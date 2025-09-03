"""
Cross-platform computer interaction tools for Anthropic AI.
This package provides tools for AI to interact with computers running Windows, macOS, or Linux.
"""

__version__ = "0.1.0"
__author__ = "FlashAdventure"

"""
Autonomous Computer Use Agent with Claude Sonnet
"""

from .evaluator import (
    main,
)

from .load_data import(
    load_game_prompt_eval,
)



__all__ = [
    "main",
    "load_game_prompt_eval",
    
]
