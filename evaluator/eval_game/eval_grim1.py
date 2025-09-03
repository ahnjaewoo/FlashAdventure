import asyncio
import json
import re
from pathlib import Path
from typing import List

from eval_game.eval_utils import run_milestone

def extract_item(conversation: List[str]) -> float | None:
    for msg in reversed(conversation):
        match = re.search(r"Found Items:\s*(\d+(\.\d+)?)", msg, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None

async def eval_grim1():
    game = "Grim Tales: The Bride"
    prompt_key = "milestone_prompt1"

    # Load prompt from milestone_prompts.json
    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data or prompt_key not in data:
        print(f"❌ No milestone data found for {game} / {prompt_key}")
        return

    print(f"🎮 Running evaluation for: {game}")

    # Run agent
    conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")

    if conversation is None:
        print("⚠️ No conversation returned from agent.")
        return

    affection = extract_item(conversation)

    if affection is not None:
        print(f"Highest Experience Score: {affection}")

        result_obj = {
            "game": "grim_tales_the_bride",
            "result": f"Items: {affection}",
            "Items": affection
        }

        Path("results").mkdir(exist_ok=True)
        with open("results/result_grim1.json", "w") as f:
            json.dump(result_obj, f, indent=2)
        print("📝 Result saved to results/result_grim1.json")
    else:
        print("⚠️ Couldn't find Found Items in result.")

if __name__ == "__main__":
    asyncio.run(eval_grim1())