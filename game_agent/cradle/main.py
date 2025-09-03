import argparse
from agent.cradle import run_game_agent
import json
import time

def select_game_from_json(prompt_file_path="./json/game_prompts.json"):
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        game_data = json.load(f)

    game_names = list(game_data.keys())

    print("🎮 Select a game to play:")
    for idx, name in enumerate(game_names, start=1):
        print(f"{idx}. {name}")

    while True:
        try:
            choice = int(input("\nEnter number ▶ "))
            if 1 <= choice <= len(game_names):
                return game_names[choice - 1]
            else:
                print("❌ Invalid number. Please try again.")
        except ValueError:
            print("❌ Please enter a number.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4")
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--cua", default="gpt")
    parser.add_argument("--max_actions", default=1000)
    args = parser.parse_args()
    
    game_name = select_game_from_json("./json/game_prompts.json")
    
    print("\n⏳ Preparing game... please wait.")
    time.sleep(5)  # ✅ Delay before execution

    result = run_game_agent(
        api_provider=args.provider,
        model_name=args.model,
        game_name=game_name,
        cua=args.cua,
        max_actions=args.max_actions
    )

    print("\n📦 Final execution result:")
    print(result)

if __name__ == "__main__":
    main()