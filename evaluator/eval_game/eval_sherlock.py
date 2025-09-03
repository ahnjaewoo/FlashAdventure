import asyncio
import json
import re
from eval_game.eval_utils import run_milestone
from pathlib import Path
from typing import List

def extract_result(conversation: List[str]) -> str | None:
    for msg in reversed(conversation):
        if "New Suspect:" in msg:
            return msg.strip()
    return None

def get_suspect_count(result_text: str) -> int:
    match = re.search(r"New Suspect:\s*(\d+)", result_text, re.IGNORECASE)
    return int(match.group(1)) if match else 0

async def eval_sherlock():
    game = "sherlock_holmes_the_tea_shop_murder_mystery"
    prompt_key = "milestone_prompt1"

    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    print(f"🕵️ Running evaluation for: Sherlock Holmes")

    conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")

    if conversation is None:
        print("⚠️ No conversation returned from agent.")
        return

    result_text = extract_result(conversation)

    if result_text:
        count = get_suspect_count(result_text)
        print(f"🔍 Final Result: {result_text}")
        print(f"🧮 Counted Suspects: {count}")

        # ✅ Save Result
        result_obj = {
            "game": "sherlock",
            "result": result_text,
            "#New Suspects": count
        }

        Path("results").mkdir(exist_ok=True)
        with open("results/result_sherlock.json", "w") as f:
            json.dump(result_obj, f, indent=2)
        print("📝 Result saved to results/result_sherlock.json")

    else:
        print("⚠️ No 'New Suspect' result found.")

if __name__ == "__main__":
    asyncio.run(eval_sherlock())