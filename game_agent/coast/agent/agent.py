import json
import os
from gui_agent import execute_action as action_Agent
from tools import (
    load_config, capture_flash_screenshot, encode_image,
    load_action_prompt, load_game_prompt, load_memory
)

class Agent:
    def __init__(self, config_path: str, moduler: str, game_name: str = None):
        self.config = load_config(config_path)
        self.moduler = moduler
        self.game_name = game_name

        # prompt
        self.action_prompt_path = self.config.get("action_prompt_path")
        self.game_prompt_path = self.config.get("game_prompt_path")
        self.final_prompt = None
        self.action_prompt = None
        self.system_prompt = None
        self.game_prompt = None

        # model
        self.gui_model = self.config.get("gui_model")
        self.reasoning_model = self.config.get("reasoning_model")
        self.provider = "anthropic" if self.reasoning_model == "claude-3-7-sonnet-20250219" else "openai"

        # image
        self.image = None

        # memory
        self.memory_path = f"./memory/{self.gui_model}/{self.reasoning_model}/{self.game_name}/"
        self.clue_memory = None
        self.episodic_memory = None
        self.task_memory = None
        self.reflection = None
        self.mapping = None
        self.success_memory = None

    def load_memory(self, type: str = "episodic", n: int = None):
        memory = load_memory(self.memory_path, type=type, n=n)
        if type == "episodic":
            self.episodic_memory = memory
        elif type == "clue":
            self.clue_memory = memory
        elif type == "mapping":
            self.mapping = memory
        elif type == "reflection":
            self.reflection = memory
        elif type == "success":
            self.success_memory=memory
        
        else:
            raise ValueError(f"Unknown memory type: {type}")

    def save_memory(self, type: str = "episodic"):
        os.makedirs(self.memory_path, exist_ok=True)

        if type == "episodic":
            data = self.episodic_memory
        elif type == "clue":
            data = self.clue_memory
        elif type == "mapping":
            data = self.mapping
        elif type == "reflection":
            data = self.reflection
        elif type == "success":
            data = self.success_memory
        else:
            raise ValueError(f"Unknown memory type: {type}")

        if data is None:
            print(f"[WARNING] 저장할 {type} memory가 없습니다.")
            return

        file_path = os.path.join(self.memory_path, f"{type}_memory.json")

        # Memory Load
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
        else:
            existing = []

        # Merge and Eliminate duplicated data
        if type == "clue":
            seen = {(c["clue"], c["location"]) for c in existing if isinstance(c, dict)}
            merged = existing + [c for c in data if (c["clue"], c["location"]) not in seen]

        elif isinstance(data, list):
            if all(isinstance(d, dict) for d in data):
                serialized = {json.dumps(d, sort_keys=True): d for d in existing if isinstance(d, dict)}
                for d in data:
                    key = json.dumps(d, sort_keys=True)
                    if key not in serialized:
                        serialized[key] = d
                merged = list(serialized.values())
            else:
                merged = list(dict.fromkeys(existing + data))
        else:
            merged = data 

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        print(f"[✅] Success to save {type}_memory.json: {file_path}")

    def load_prompt(self, option="action", type: str = None):
        if option == "action":
            self.action_prompt = load_action_prompt(self.action_prompt_path, self.moduler)
        elif option == "game":
            if type == "game_prompt":
                self.game_prompt = load_game_prompt(self.game_prompt_path, game_name=self.game_name, type=type)
            elif type == "system_prompt":
                self.system_prompt = load_game_prompt(self.game_prompt_path, game_name=self.game_name, type=type)
        else:
            raise ValueError("The prompt type does not exist.")

    def capture_and_encode_image(self):
        self.image = encode_image(capture_flash_screenshot(self.game_name, self.gui_model, self.reasoning_model))
        return self.image

    def needs_image(self):
        return self.gui_model not in ["gpt_operator", "claude_cua"]

    def execute_action(self):
        if self.needs_image():
            self.capture_and_encode_image()

        result = action_Agent(
            action_prompt=self.final_prompt,
            system_prompt=self.system_prompt if self.gui_model == "claude_cua" else None,
            encoded_image=self.image,
            gui_model=self.gui_model,
            reasoning_model=self.reasoning_model,
            type=self.moduler
        )

        if self.moduler == "clue_seeker" and isinstance(result, dict):
            return result

        print("👡 Finish Action")
        return result