from agent.skill_curation import update_or_add_verified_skill
from ours.agent.planner import plan_actions
from agent.subtask_planning import plan_subtask
from agent.info_gathering import info_gather
from agent.self_reflection import check_action_success, self_reflect
from agent.game_end import game_end
from agent.memory import add_task_memory, add_reflection_memory
from tools import load_game_prompt, load_system_prompt, capture_flash_screenshot, encode_image
from gui_agent.gpt_cua import main_gpt_cua
from gui_agent.claude_cua import run_agent as main_claude_cua
from gui_agent.gui_grounding import agent_step as main_uground
from gui_agent.gui_grounding import run_claude_gui_agent as main_claude
from api import api_caller
import json
import re

class head():
    
    def __init__(self, reasoning_model, gui_model, game_name, task_prompt, width):
        self.reasoning_model=reasoning_model ## anthropic or openai
        self.gui_model = gui_model ## claude_cua, gpt_cua, claude, uground
        self.game_name = game_name
        self.task_prompt = task_prompt
        self.width = width
        self.before_image = None
        self.env_summary = None
        
    ##### info_gathering - environment_summary #####

    
    def environment_summary(self, encoded_image):
        self.before_image = encoded_image
        if self.reasoning_model == "anthropic":
            self.env_summary = info_gather(self.task_prompt, self.reasoning_model, "claude-3-7-sonnet-20250219", self.before_image)
        elif self.reasoning_model == "openai":
            self.env_summary = info_gather(self.task_prompt, self.reasoning_model, "gpt-4o", self.before_image)
        else:
            ValueError("environment_summary: This model is not working")
            
    ##### planning_subtask #####

    def planning_subtask(self):
        if self.reasoning_model == "anthropic":
            planning_result = plan_subtask(self.task_prompt, self.reasoning_model, "claude-3-7-sonnet-20250219", self.gui_model, self.game_name, self.env_summary, self.before_image, self.width)
        elif self.reasoning_model == "openai":
            planning_result = plan_subtask(self.task_prompt, self.reasoning_model, "gpt-4o", self.gui_model, self.game_name, self.env_summary, self.before_image, self.width)
        else:
            ValueError("planning_subtask: This model is not working")
            
        # ✅ parsing
        actions = self.parse_actions_from_result(planning_result)
        return actions
    
    def parse_actions_from_result(self, text):
        """Extracts the JSON list of actions after the [Result] tag."""
        match = re.search(r'\[Result\]\s*(\[[\s\S]*?\])', text)
        if not match:
            return []
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
        
    def run(self):
        print(f"🎮 Execution started: Game = {self.game_name}, GUI Model = {self.gui_model}, Reasoning = {self.reasoning_model}")
        
        # 1. Capture screen
        screenshot_path = capture_flash_screenshot(game_name=self.game_name, cua=self.gui_model, model_name=self.reasoning_model)
        print(f"📸 Screenshot path: {screenshot_path}")
        
        self.before_image = encode_image(screenshot_path)

        # 2. Summarize environment
        self.environment_summary(self.before_image)
        print("🌍 Environment summary complete")
        print(self.env_summary)

        # 3. Plan subtasks
        actions = self.planning_subtask()
        print("\n📝 Planned subtask list:")
        for i, act in enumerate(actions, 1):
            print(f"{i}. {act}")

        # Additional action execution, evaluation, and self-reflection can be added here
        return actions