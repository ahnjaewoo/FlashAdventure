"""Utility to run shell commands asynchronously with a timeout across platforms."""

import asyncio
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Union

TRUNCATED_MESSAGE: str = "<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>"
MAX_RESPONSE_LEN: int = 16000


def maybe_truncate(content: str, truncate_after: int | None = MAX_RESPONSE_LEN):
    """Truncate content and append a notice if content exceeds the specified length."""
    return (
        content
        if not truncate_after or len(content) <= truncate_after
        else content[:truncate_after] + TRUNCATED_MESSAGE
    )


async def run(
    cmd: str,
    timeout: float | None = 120.0,  # seconds
    truncate_after: int | None = MAX_RESPONSE_LEN,
    shell: bool = True,
):
    """Run a shell command asynchronously with a timeout across platforms."""
    system = platform.system().lower()
    
    # Handle Windows-specific commands
    if system == "windows" and shell:
        # For PowerShell commands, ensure proper shell usage
        if cmd.startswith("powershell") and not cmd.startswith("powershell.exe"):
            cmd = cmd.replace("powershell", "powershell.exe", 1)
    
    process = await asyncio.create_subprocess_shell(
        cmd, 
        stdout=asyncio.subprocess.PIPE, 
        stderr=asyncio.subprocess.PIPE,
        # On Windows, sometimes we need to create a new process group to properly kill processes
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if system == "windows" else 0
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return (
            process.returncode or 0,
            maybe_truncate(stdout.decode(errors='replace'), truncate_after=truncate_after),
            maybe_truncate(stderr.decode(errors='replace'), truncate_after=truncate_after),
        )
    except asyncio.TimeoutError as exc:
        try:
            # On Windows, using CTRL+C signal
            if system == "windows":
                process.send_signal(subprocess.CTRL_C_EVENT)
                # Give it a chance to terminate gracefully
                try:
                    await asyncio.wait_for(process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    process.kill()
            else:
                process.kill()
        except ProcessLookupError:
            pass
        raise TimeoutError(
            f"Command '{cmd}' timed out after {timeout} seconds"
        ) from exc


def run_sync(
    cmd: str,
    timeout: float | None = 120.0,  # seconds
    truncate_after: int | None = MAX_RESPONSE_LEN,
    shell: bool = True,
):
    """
    Synchronous version of run for simpler usage when async isn't needed.
    Returns (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            encoding='utf-8',
            errors='replace'
        )
        return (
            result.returncode,
            maybe_truncate(result.stdout, truncate_after=truncate_after),
            maybe_truncate(result.stderr, truncate_after=truncate_after),
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"Command '{cmd}' timed out after {timeout} seconds"
        ) from exc


def get_temp_dir() -> Path:
    """Get appropriate temp directory for current platform."""
    system = platform.system().lower()
    if system == "windows":
        return Path(os.environ.get("TEMP", "C:/temp"))
    else:  # Linux or macOS
        return Path("/tmp")