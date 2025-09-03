"""
Cross-platform computer interaction tools for Anthropic AI.
This package provides tools for AI to interact with computers running Windows, macOS, or Linux.
"""

from .base import BaseAnthropicTool, ToolError, ToolFailure, ToolResult
from .collection import ToolCollection
from .bash import ShellTool20241022, ShellTool20250124
from .computer import ComputerTool20241022, ComputerTool20250124
from .edit import CrossPlatformEditTool20241022, CrossPlatformEditTool20250124
from .groups import TOOL_GROUPS, TOOL_GROUPS_BY_VERSION, ToolVersion, BetaFlag

__all__ = [
    "BaseAnthropicTool",
    "ToolResult",
    "ToolError",
    "ToolFailure",
    "ToolCollection",
    "ShellTool20241022",
    "ShellTool20250124",
    "ComputerTool20241022",
    "ComputerTool20250124",
    "CrossPlatformEditTool20241022",
    "CrossPlatformEditTool20250124",
    "TOOL_GROUPS",
    "TOOL_GROUPS_BY_VERSION",
    "ToolVersion",
    "BetaFlag",
]

# Aliases for backwards compatibility
from .bash import ShellTool20250124 as BashTool20250124
from .bash import ShellTool20241022 as BashTool20241022
from .edit import CrossPlatformEditTool20250124 as EditTool20250124
from .edit import CrossPlatformEditTool20241022 as EditTool20241022

__all__ += [
    "BashTool20250124",
    "BashTool20241022",
    "EditTool20250124",
    "EditTool20241022",
]