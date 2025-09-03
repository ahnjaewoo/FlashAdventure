import logging
import time
from typing import Tuple, Dict, Any, Optional

from desktop_env.controllers.python import LocalController
logger = logging.getLogger("desktopenv.env")


class LocalDesktopEnv:
    def __init__(
        self,
        game_name,
        action_space: str = "pyautogui",
        screen_size: Tuple[int, int] = (1920, 1080),
        require_a11y_tree: bool = False,
        require_terminal: bool = False,
    ):
        assert action_space == "pyautogui", "Only 'pyautogui' is supported in local mode."

        self.action_space = action_space
        self.screen_size = screen_size
        self.require_a11y_tree = require_a11y_tree
        self.require_terminal = require_terminal

        self.instruction = ""
        self.task_id = "default_task"
        self.action_history = []

        self.controller = LocalController("./screehshots", game_name)  

    def reset(self, task_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        self.action_history.clear()
        self.task_id = task_config.get("id", "default_task") if task_config else "default_task"
        self.instruction = task_config.get("instruction", "") if task_config else ""
        return self._get_obs()

    def _get_obs(self):
        return {
            "screenshot": self.controller.get_screenshot(),
            "accessibility_tree": None,
            "terminal": None,
            "instruction": self.instruction,
        }

    def step(self, action: str, pause: float = 1.0):
        self.action_history.append(action)

        done = False
        info = {}

        if action == "WAIT":
            time.sleep(pause)
        elif action == "FAIL":
            done = True
            info["fail"] = True
        elif action == "DONE":
            done = True
            info["done"] = True
        else:
            self.controller.execute_python_command(action)

        time.sleep(pause)
        obs = self._get_obs()
        return obs, 0.0, done, info

    def evaluate(self):
        return 0.0  

    def close(self):
        logger.info("LocalDesktopEnv closed.")

    def render(self, mode="rgb_array"):
        if mode == "rgb_array":
            return self.controller.get_screenshot()
        raise ValueError(f"Unsupported render mode: {mode}")