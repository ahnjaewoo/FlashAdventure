from agent.skill_curation import update_or_add_verified_skill
from agent.planner import plan_actions,plan_subtask
from agent.info_gathering import summary_env, find_clue
from agent.self_reflection import check_action_success, self_reflect
from agent.game_end import game_end
from agent.memory import add_task_memory, add_reflection_memory, add_clue_memory
from tools import load_game_prompt, load_system_prompt, capture_flash_screenshot, encode_image
from gui_agent.gpt_cua import main_gpt_operator
from gui_agent.claude_cua import run_agent as main_claude_cua
from gui_agent.gui_grounding import agent_step as main_uground
from gui_agent.gui_grounding import run_claude_gui_agent as main_claude
from api import api_caller
import json
import re


class Planner:
    
    def __init__(self, reasoning_model, gui_model, game_name, task_prompt, width, mode="action", current_subtask=None):
        self.reasoning_model = reasoning_model  # "openai" or "anthropic"
        self.gui_model = gui_model              # e.g., "gpt_cua", "claude", etc.
        self.game_name = game_name
        self.task_prompt = task_prompt
        self.width = width
        self.mode = mode                        # "action" or "subtask"
        self.before_image = None
        self.env_summary = None
        self.clue_result = None
        self.current_subtask = current_subtask

    ##### Step 1: Info Gathering #####

    def environment_summary(self, encoded_image):
        self.before_image = encoded_image
        model_name = "claude-3-7-sonnet-20250219" if self.reasoning_model == "anthropic" else "gpt-4o"

        self.env_summary = summary_env(
            self.task_prompt,
            self.reasoning_model,
            model_name,
            self.before_image
        )

    ##### Step 2: Planning #####

    def plan(self):
        model_name = "claude-3-7-sonnet-20250219" if self.reasoning_model == "anthropic" else "gpt-4o"

        if self.mode == "action":
            result = plan_actions(
                self.task_prompt,
                self.reasoning_model,
                model_name,
                self.gui_model,
                self.game_name,
                self.env_summary,
                self.before_image,
                self.width,
                self.current_subtask
            )
        elif self.mode == "subtask":
            result = plan_subtask(
                self.task_prompt,
                self.reasoning_model,
                model_name,
                self.gui_model,
                self.game_name,
                self.env_summary,
                self.before_image,
                self.task_prompt,  # main_task = same as prompt for now
                self.width
            )
        else:
            raise ValueError(f"❌ Unknown mode: {self.mode}")

        return result

    ##### Util: Parse LLM JSON Output #####
    def parse_actions_from_result(self, text):
        import json
        import re

        try:
            # Extracts the first list-like form ([...]) from the text using regex
            match = re.search(r'\[\s*(?:".*?"\s*,?\s*)+\]', text, re.DOTALL)
            if match:
                array_str = match.group(0)
                # Attempt to parse as JSON
                parsed = json.loads(array_str)
                if isinstance(parsed, list):
                    return parsed
        except Exception as e:
            print(f"❌ JSON parsing failed: {e}")

        print("⚠️ [Parser] JSON array parsing failed. Returning empty list.")
        return []

    ##### Runner #####

    def run(self):
        print(f"🎮 Execution started: Game = {self.game_name}, Mode = {self.mode}, Reasoning = {self.reasoning_model}")

        # 1. Capture screen
        screenshot_path = capture_flash_screenshot(
            game_name=self.game_name,
            cua=self.gui_model,
            model_name=self.reasoning_model
        )
        print(f"📸 Screenshot path: {screenshot_path}")
        self.before_image = encode_image(screenshot_path)

        # 2. Summarize environment
        self.environment_summary(self.before_image)
        print("🌍 Environment summary complete")
        print(self.env_summary)
        
        # 3. Plan formulation (action or subtask)
        actions = self.parse_actions_from_result(self.plan())
        print(actions)
        print(f"\n📝 Planned {self.mode} list:")
        for i, act in enumerate(actions, 1):
            print(f"{i}. {act}")

        return actions