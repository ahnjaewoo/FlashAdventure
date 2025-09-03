from agent import Agent
from tools import  extract_clues_from_text, extract_episodic_memory_from_text, extract_json_block_from_response
from gui_agent import execute_action as action_Agent
import json, os
from api import api_caller
import re

"""
Our Agents:
    SeekerBot  → Clue Seeker Agent
    MatcherBot → Clue Matcher Agent
    SolverBot  → Problem Solver Agent
"""


## Seek Clue bot
class SeekerBot(Agent):
    """
    Information used:
    - Clue Memory

    Information to save:
    - Found Clues
    - Episodic Memory of the screens seen while moving (pair summaries of each {observation, action})
    """

    def __init__(self, config_path: str = "config.yaml", game_name: str = None, mapping: str = None):
        super().__init__(config_path=config_path, moduler="clue_seeker", game_name=game_name)

    def make_prompt(self):

        if self.gui_model == "claude_cua":
            self.system_prompt = f"{self.system_prompt.strip()}\n\n{self.game_prompt.strip()}\n\n"
            self.final_prompt = (
                f"{self.action_prompt.strip()}\n\n"
                "Do not store the same clue more than once in memory.\n\n"
                f"[Clues]\n{json.dumps(self.clue_memory, indent=2)}\n\n"

            )
        else:
            self.final_prompt = (
                f"{self.system_prompt.strip()}\n\n"
                f"{self.game_prompt.strip()}\n\n"
                f"{self.action_prompt.strip()}\n\n"
                "Do not store the same clue more than once in memory.\n\n"
                f"[Clues]\n{json.dumps(self.clue_memory, indent=2)}\n\n"
            )
            
        print("🥔SeekerBot:", self.final_prompt)
            
    def execute_action(self):
        result = super().execute_action()
        
        # Extract clues and episodic_memory from messages
        clues = []
        episodic = []
        
        if isinstance(result, dict) and "messages" in result:
            # Since the last message usually contains the result, iterate in reverse
            for message in reversed(result["messages"]):
                # Extract text from dicts
                if isinstance(message, dict) and "text" in message:
                    message = message.get("text", "")
                elif not isinstance(message, str):
                    continue
                
                # Find <RESPO> tags and pre-process the content
                if "<RESPO>" in message and "</RESPO>" in message:
                    # Simple preprocessing: handle escaped characters
                    content = message.split("<RESPO>")[1].split("</RESPO>")[0].strip()
                    content = content.replace("\\n", "\n").replace("\\\"", "\"").replace("\\'", "'")
                    
                    try:
                        # Try JSON parsing
                        data = json.loads(content)
                        if "clues" in data and data["clues"]:
                            clues = data["clues"]
                        if "episodic_memory" in data and data["episodic_memory"]:
                            episodic = data["episodic_memory"]
                        # If valid data is found, exit loop
                        if clues and episodic:
                            break
                    except json.JSONDecodeError as e:
                        print(f"[⚠️] JSON parsing failed (simple method): {str(e)[:50]}")
                        print(f"Content sample: {content[:50]}...")
        
        # Fallback method if extraction failed
        if not clues or not episodic:
            try:
                # Concatenate all text from result
                all_text = ""
                if isinstance(result, dict) and "messages" in result:
                    for msg in result["messages"]:
                        if isinstance(msg, dict) and "text" in msg:
                            all_text += msg["text"] + "\n"
                        elif isinstance(msg, str):
                            all_text += msg + "\n"
                
                # Find text inside <RESPO> tags
                if "<RESPO>" in all_text and "</RESPO>" in all_text:
                    tag_content = all_text.split("<RESPO>")[1].split("</RESPO>")[0].strip()
                    
                    # Handle escaped strings
                    tag_content = tag_content.replace("\\n", "\n").replace("\\\"", "\"").replace("\\'", "'")
                    
                    # Simple patterns — extract only the "clues" and "episodic_memory" fields
                    clues_pattern = r'"clues"\s*:\s*\[(.*?)\]'
                    episodic_pattern = r'"episodic_memory"\s*:\s*\[(.*?)\]'
                    
                    clues_match = re.search(clues_pattern, tag_content, re.DOTALL)
                    episodic_match = re.search(episodic_pattern, tag_content, re.DOTALL)
                    
                    if clues_match:
                        # Extract and clean clues text
                        clues_text = clues_match.group(1).strip()
                        # Find each clue item and process
                        clue_pattern = r'{\s*"clue"\s*:\s*"(.*?)",\s*"description"\s*:\s*"(.*?)",\s*"location"\s*:\s*"(.*?)"\s*}'
                        for match in re.finditer(clue_pattern, clues_text):
                            clue = {
                                "clue": match.group(1),
                                "description": match.group(2),
                                "location": match.group(3)
                            }
                            clues.append(clue)
                    
                    if episodic_match:
                        # Extract and clean episodic_memory text
                        episodic_text = episodic_match.group(1).strip()
                        # Find entries wrapped in double quotes
                        memory_pattern = r'"(.*?[^\\])"'  # Up to an unescaped double quote
                        for match in re.finditer(memory_pattern, episodic_text):
                            episodic.append(match.group(1))
            
            except Exception as e:
                print(f"[⚠️] Fallback method also failed: {str(e)}")
        
        # Save and print extracted data
        if clues:
            self.clue_memory = clues
            print(f"[✅] Found clues: {len(clues)}")
            for idx, clue in enumerate(clues, 1):
                print(f"  {idx}. {clue.get('clue', 'Unknown')}")
            self.save_memory("clue")
        else:
            print("[❌] Could not find clues.")
        
        if episodic:
            self.episodic_memory = episodic
            print(f"[✅] Recorded episodic_memory: {len(episodic)}")
            for idx, memory in enumerate(episodic, 1):
                print(f"  {idx}. {memory[:50]}..." if len(memory) > 50 else f"  {idx}. {memory}")
            self.save_memory("episodic")
        else:
            print("[❌] Could not find episodic_memory.")
        
        return result.get("action_count", 0)
    def run(self):
        self.load_prompt(option="game", type="system_prompt")
        self.load_prompt(option="game", type="game_prompt")
        self.load_prompt(option="action")
        self.load_memory("clue")
        self.make_prompt()

        return self.execute_action()
    
    
## Bot for solving problems

class SolverBot(Agent):
    """
    SolverBot → Agent responsible for problem solving

    Information used:
    - mapping result: {Clue, Episodic Memory, Expected Action}

    Information to save:
    - Keep the entire mapping_memory (do not overwrite)
    - Accumulate only successful mappings in success_memory
    - Record episodic_memory
    """

    def __init__(self, config_path: str = "config.yaml", game_name: str = None):
        super().__init__(config_path=config_path, moduler="problem_solver", game_name=game_name)

    def get_mapping(self, mapping_data=None, max_items: int = 5):
        if mapping_data is not None:
            lines = ["[Mapping History]"]
            for match in mapping_data:
                clue = match.get("clue", "")
                memory = match.get("related_memory", "")
                expected_action = match.get("expected_action", "")
                lines.append(f"- Clue: {clue}\n  Related Memory: {memory} \n Expected Action: {expected_action}")
            self.mapping = "\n".join(lines)
            return

        mapping_path = os.path.join(self.memory_path, "mapping_memory.json")
        if not os.path.exists(mapping_path):
            self.mapping = "[Mapping]\n(No mapping history available)"
            return

        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                all_mappings = json.load(f)
                recent = all_mappings[-max_items:] if isinstance(all_mappings, list) else []
        except json.JSONDecodeError:
            recent = []

        lines = ["[Mapping History]"]
        for match in recent:
            if isinstance(match, list):
                for item in match:
                    clue = item.get("clue", "")
                    memory = item.get("related_memory", "")
                    expected_action = item.get("expected_action", "")
                    lines.append(f"- Clue: {clue}\n  Related Memory: {memory} \n Expected Action: {expected_action}")
            elif isinstance(match, dict):
                lines.append(json.dumps(match, indent=2))

        self.mapping = "\n".join(lines) if lines else "[Mapping]\n(No valid mapping entries found)"

    def make_prompt(self):
        if self.gui_model == "claude_cua":
            self.system_prompt = f"{self.system_prompt.strip()}\n\n{self.game_prompt.strip()}\n\n"
            self.final_prompt = (
                f"{self.action_prompt.strip()}\n\n"
                f"{self.mapping if self.mapping else ''}"
            )
        else:
            self.final_prompt = (
                f"{self.system_prompt.strip()}\n\n"
                f"{self.game_prompt.strip()}\n\n"
                f"{self.action_prompt.strip()}\n\n"
                f"{self.mapping if self.mapping else ''}"
            )

    def execute_action(self):
        result = super().execute_action()
        messages = result.get("messages", [])
        action_count = result.get("action_count", 0)

        mapping_result = None
        episodic = []

        for msg in messages:
            if isinstance(msg, str) and "<RESPO>" in msg and "</RESPO>" in msg:
                content = msg.split("<RESPO>")[1].split("</RESPO>")[0].strip()
                content = content.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        mapping_result = data.get("mapping_result", [])
                        episodic = data.get("episodic_memory", [])
                except json.JSONDecodeError as e:
                    print(f"[⚠️] SolverBot: JSON parsing failed - {e}")

        if episodic:
            self.episodic_memory = episodic
            print(f"[✅] SolverBot: Recorded episodic_memory {len(episodic)}")
            self.save_memory("episodic")
        else:
            print("[❌] SolverBot: Could not find episodic_memory.")

        if mapping_result:
            for item in mapping_result:
                if isinstance(item, dict):
                    item["success"] = True

            # Save successes separately
            successful = [m for m in mapping_result if m.get("success") is True]
            if successful:
                self.success_memory = successful
                self.save_memory("success")
        else:
            print("[❌] SolverBot: Could not find mapping_result.")

        return action_count

    def run(self):
        self.load_prompt(option="game", type="system_prompt")
        self.load_prompt(option="game", type="game_prompt")
        self.load_prompt(option="action")
        self.load_memory("success")
        self.get_mapping()
        self.make_prompt()
        return self.execute_action()


    
    
## Mapping between clues and episodic memory
class MapperBot(Agent):
    """
    Information used:
    - Found clues
    - Episodic Memory
    
    Information to save:
    - Mapping results: {Clue, Episodic Memory, Expected Action}
    """
    def __init__(self, config_path: str = "config.yaml", game_name: str = None):
        super().__init__(config_path=config_path, moduler="clue_mapper", game_name=game_name)

    def make_prompt(self):
        success_data = self.success_memory if self.success_memory else []
        if self.reasoning_model == "claude-3-7-sonnet-20250219":
            self.system_prompt = (f"{self.system_prompt.strip()}\n\n"
                                  f"{self.game_prompt.strip()}\n\n")
            self.final_prompt = (
                f"{self.action_prompt.strip()}\n\n"
                f"[Clues]\n{json.dumps(self.clue_memory, indent=2)}\n\n"
                f"[Episodic Memory]\n{json.dumps(self.episodic_memory, indent=2)}\n\n"
                "Do not generate mapping memory that has already succeeded.\n\n"
                f"[Success Memory]\n{json.dumps(success_data, indent=2)}\n\n"
            )
        else:
            self.final_prompt = (
                f"{self.system_prompt.strip()}\n\n"
                f"{self.game_prompt.strip()}\n\n"
                f"{self.action_prompt.strip()}\n\n"
                f"[Clues]\n{json.dumps(self.clue_memory, indent=2)}\n\n"
                f"[Episodic Memory]\n{json.dumps(self.episodic_memory, indent=2)}\n\n"
                "Do not generate mapping memory that has already succeeded.\n\n"
                f"[Success Memory]\n{json.dumps(success_data, indent=2)}\n\n"    
            )
        print(self.final_prompt)

    def execute_action(self):
        try:
            response = api_caller(
                api_provider=self.provider,
                system_prompt=self.system_prompt,
                model_name=self.reasoning_model,
                move_prompts=self.final_prompt,
                base64_images=[]
            )
            print(response)

            # Parsing based on <RESPO> tags
            if "<RESPO>" in response and "</RESPO>" in response:
                content = response.split("<RESPO>")[1].split("</RESPO>")[0].strip()
                content = content.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")

                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, list):  # MapperBot returns a list
                        return parsed
                    elif isinstance(parsed, str) and parsed.strip() == "[Nobody]":
                        return []
                    else:
                        print("[⚠️] Unexpected structure: not a list")
                except json.JSONDecodeError as e:
                    print(f"[❌] MapperBot: JSON parsing failed - {e}")
                    print("▶️ Original content snippet:", content)
            else:
                print("[❌] <RESPO> tag not included in response.")

            return []  # fallback

        except Exception as e:
            print(f"[❌] Exception during execute_action: {e}")
            return [{"error": str(e)}]

    def run(self):
        self.load_prompt(option="game", type="system_prompt")
        self.load_prompt(option="game", type="game_prompt")
        self.load_prompt(option="action")
        
        self.load_memory("clue")
        self.load_memory("episodic", n=10)
        self.load_memory("success")

        self.make_prompt()
        self.mapping = self.execute_action()

        # ✅ Save mapping memory in overwrite mode
        mapping_path = os.path.join(self.memory_path, "mapping_memory.json")
        try:
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(self.mapping, f, indent=2, ensure_ascii=False)
            print("[✅] MapperBot: Saved mapping information anew.")
        except Exception as e:
            print(f"[❌] MapperBot: Failed to save mapping - {e}")

        return self.mapping