from agent.agent import Agent
from computers import LocalDesktopComputer
from dotenv import load_dotenv
import json
import os
import sys
import argparse
from datetime import datetime
import re
import time

# Logger class that also saves output logs to a file
class Logger(object):
    def __init__(self, file_path):
        self.terminal = sys.stdout
        self.log = open(file_path, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def slugify(text: str, max_length: int = 30) -> str:
    text = re.sub(r'\s+', '_', text.strip())
    text = re.sub(r'[^\w\-_.]', '', text)
    return text[:max_length]

# [Changed] Create log folder per game
def setup_logging(game_name="session"):
    safe_game_name = slugify(game_name)
    log_dir = os.path.join("log", safe_game_name)
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"{safe_game_name}_{timestamp}.txt")
    sys.stdout = Logger(log_filename)
    print(f"📝 Log file saved to: {log_filename}")

def acknowledge_safety_check_callback(message: str) -> bool:
    response = input(f"⚠️ Safety warning: {message}\nContinue? (y/n): ").lower()
    return response.strip() == "y"

def action_limit_reached_callback():
    print("🚫 Action limit reached.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the game agent.")
    parser.add_argument("json_file", nargs="?", default=None, help="Path to the JSON file containing game prompts")
    parser.add_argument("--history", type=int, default=5, help="Number of recent conversation turns to send to the model")
    return parser.parse_args()

def main():
    load_dotenv()
    args = parse_arguments()
    turn_limit = args.history

    base_screenshots_folder = os.getenv("SCREENSHOTS_FOLDER", "screenshots")  # [Default folder]
    save_screenshots = True
    max_actions = int(os.getenv("MAX_ACTIONS", "100"))
    default_prompt = os.getenv("DEFAULT_PROMPT", "Go to openai.com and get the first text that exists.")
    prompt = default_prompt
    selected_game = "default"

    try:
        if args.json_file:
            json_file_path = args.json_file
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    json_data = json.load(file)
                    print("🎮 Available games:")
                    for idx, game in enumerate(json_data.keys()):
                        print(f"{idx + 1}. {game}")
                    selected_idx = int(input("🔎 Select a game number to run: ")) - 1
                    selected_game = list(json_data.keys())[selected_idx]
                    if 'prompt' in json_data[selected_game]:
                        prompt = json_data[selected_game]['prompt']
                        print(f"📝 Prompt for '{selected_game}' loaded successfully.")
                    else:
                        print(f"❌ '{selected_game}' has no 'prompt'.")
                        return
            else:
                print(f"❌ File not found: {json_file_path}")
                return
        else:
            print("📄 No JSON path. Using .env or default prompt.")

        setup_logging(selected_game)  # [Changed]

        # [Changed] Create screenshot folder per game
        screenshots_folder = os.path.join(base_screenshots_folder, slugify(selected_game))
        os.makedirs(screenshots_folder, exist_ok=True)

        print(f"🔢 Maximum number of actions: {max_actions}")
        print(f"🧠 Number of recent conversation turns to send to the model: {turn_limit}")

        computer = LocalDesktopComputer(
            max_actions=max_actions,
            action_limit_callback=action_limit_reached_callback
        )

        agent = Agent(
            computer=computer,
            acknowledge_safety_check_callback=acknowledge_safety_check_callback,
            save_screenshots=save_screenshots,
            screenshots_folder=screenshots_folder
        )

        prompt += (
            f"\n\n[Important]: I REQUIRE a text explanation before EVERY action. If you fail to provide text before an action, your response will be considered incomplete. Each step 'MUST include text reasoning followed by exactly one action'."
        )

        initial_prompt = {"role": "user", "content": [{"type": "input_text", "text": prompt}]}
        include_initial_prompt = True
        all_outputs = []

        max_retries = 100
        for attempt in range(max_retries):
            try:
                print(f"🧠 [DEBUG] Initial request - sending only the initial prompt")
                response = agent.run_full_turn([initial_prompt], debug=True, show_images=False)
                if response:
                    all_outputs.append(response)
                    print(f"🔍 Number of output items: {len(response)} items")
                    break
                else:
                    print(f"⚠️ Model response is empty. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(1)
            except Exception as e:
                print(f"❌ Error occurred: {e}. Retrying... ({attempt + 1}/{max_retries})")
                time.sleep(2)
        else:
            print("❌ Model response failed, terminating session.")
            return

        while not computer.action_limit_reached:
            request_items = []
            if include_initial_prompt:
                request_items.append(initial_prompt)

            max_history = min(len(all_outputs), turn_limit)
            for i in range(len(all_outputs) - max_history, len(all_outputs)):
                request_items.extend(all_outputs[i])

            print(f"🧠 [DEBUG] Request - total turns: {len(all_outputs)}, turns sent: {max_history}")
            print(f"🧠 [DEBUG] Number of items sent: {len(request_items)}")

            for attempt in range(max_retries):
                try:
                    response = agent.run_full_turn(request_items, debug=True, show_images=False)
                    if response:
                        all_outputs.append(response)
                        print(f"🔁 Automatic turn complete (current actions: {computer.action_count})")
                        break
                    else:
                        print(f"⚠️ No model response. Retrying... ({attempt + 1}/{max_retries})")
                        time.sleep(1)
                except Exception as e:
                    print(f"❌ Error occurred: {e}. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
            else:
                print("❌ Model response failed even after repeated attempts. Stopping automatic progression.")
                break

        print("✅ Automatic session execution ended")

    finally:
        print("✅ Program terminated")

if __name__ == "__main__":
    main()