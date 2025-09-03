import asyncio
import os
import platform
import subprocess
from typing import Any, Literal

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from .platform_utils import PlatformManager, Platform


class _ShellSession:
    """A session of a shell that works across platforms."""

    _started: bool
    _process: asyncio.subprocess.Process

    _output_delay: float = 0.2  # seconds
    _timeout: float = 120.0  # seconds
    _sentinel: str = "<<exit>>"

    def __init__(self):
        self._started = False
        self._timed_out = False
        self.platform_manager = PlatformManager()
        # Get the appropriate shell command based on platform
        self.command = self.platform_manager.get_shell_command()

    async def start(self):
        if self._started:
            return

        # Handle different shell startup based on platform
        system = platform.system().lower()
        if system == "windows":
            # On Windows, use cmd.exe or PowerShell
            self._process = await asyncio.create_subprocess_shell(
                self.command,
                # Windows-specific creation flags if needed
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                bufsize=0,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            # Unix-like systems
            self._process = await asyncio.create_subprocess_shell(
                self.command,
                preexec_fn=os.setsid,
                shell=True,
                bufsize=0,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        self._started = True

    def stop(self):
        """Terminate the shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            return
        
        # Platform-specific termination
        system = platform.system().lower()
        if system == "windows":
            # On Windows, send CTRL+C first as a graceful shutdown
            try:
                self._process.send_signal(subprocess.CTRL_C_EVENT)
            except Exception:
                pass
            # Give it a moment to shutdown
            import time
            time.sleep(0.5)
            
        # Then forcibly terminate if still running
        self._process.terminate()

    async def run(self, command: str):
        """Execute a command in the shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            shell_name = "PowerShell" if platform.system().lower() == "windows" else "bash"
            return ToolResult(
                system="tool must be restarted",
                error=f"{shell_name} has exited with returncode {self._process.returncode}",
            )
        if self._timed_out:
            shell_name = "PowerShell" if platform.system().lower() == "windows" else "bash"
            raise ToolError(
                f"timed out: {shell_name} has not returned in {self._timeout} seconds and must be restarted",
            )

        # we know these are not None because we created the process with PIPEs
        assert self._process.stdin
        assert self._process.stdout
        assert self._process.stderr

        # Platform-specific command handling
        system = platform.system().lower()
        if system == "windows":
            # On Windows, we might need special handling for PowerShell
            if self.command.lower().endswith("powershell.exe"):
                # Ensure command ends with a semicolon for PowerShell
                if not command.strip().endswith(";"):
                    command = command + ";"
                # Add PowerShell echo for the sentinel
                send_cmd = command + f' Write-Output "{self._sentinel}"\n'
            else:
                # Cmd.exe syntax
                send_cmd = command + f' && echo {self._sentinel}\n'
            
            self._process.stdin.write(send_cmd.encode())
        else:
            # Unix-like systems
            self._process.stdin.write(
                command.encode() + f"; echo '{self._sentinel}'\n".encode()
            )
        
        await self._process.stdin.drain()

        # read output from the process, until the sentinel is found
        try:
            async with asyncio.timeout(self._timeout):
                while True:
                    await asyncio.sleep(self._output_delay)
                    # if we read directly from stdout/stderr, it will wait forever for
                    # EOF. use the StreamReader buffer directly instead.
                    output = self._process.stdout._buffer.decode(errors='replace')  # pyright: ignore[reportAttributeAccessIssue]
                    if self._sentinel in output:
                        # strip the sentinel and break
                        output = output[: output.index(self._sentinel)]
                        break
        except asyncio.TimeoutError:
            self._timed_out = True
            shell_name = "PowerShell" if platform.system().lower() == "windows" else "bash"
            raise ToolError(
                f"timed out: {shell_name} has not returned in {self._timeout} seconds and must be restarted",
            ) from None

        if output.endswith("\n"):
            output = output[:-1]

        error = self._process.stderr._buffer.decode(errors='replace')  # pyright: ignore[reportAttributeAccessIssue]
        if error.endswith("\n"):
            error = error[:-1]

        # clear the buffers so that the next output can be read correctly
        self._process.stdout._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]
        self._process.stderr._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]

        return CLIResult(output=output, error=error)


class ShellTool20250124(BaseAnthropicTool):
    """
    A cross-platform shell tool that allows the agent to run commands.
    Works on Windows, macOS, and Linux.
    """

    _session: _ShellSession | None

    api_type: Literal["bash_20250124"] = "bash_20250124"
    name: Literal["bash"] = "bash" 

    def __init__(self):
        self._session = None
        super().__init__()

    def to_params(self) -> Any:
        return {
            "type": self.api_type,
            "name": self.name,
        }

    async def __call__(
        self, command: str | None = None, restart: bool = False, **kwargs
    ):
        if restart:
            if self._session:
                self._session.stop()
            self._session = _ShellSession()
            await self._session.start()

            return ToolResult(system="tool has been restarted.")

        if self._session is None:
            self._session = _ShellSession()
            await self._session.start()

        if command is not None:
            return await self._session.run(command)

        raise ToolError("no command provided.")


class ShellTool20241022(ShellTool20250124):
    api_type: Literal["bash_20241022"] = "bash_20241022"  # pyright: ignore[reportIncompatibleVariableOverride]