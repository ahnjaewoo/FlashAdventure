import asyncio
import json
import re
from pathlib import Path
from typing import List

from eval_game.eval_utils import run_milestone

def extract_boolean_result(conversation: List[str]) -> bool | None:
    for msg in reversed(conversation):
        match = re.search(r"Result:\s*(True|False)", msg, re.IGNORECASE)
        if match:
            return match.group(1).lower() == "true"
    return None

async def eval_dakota():
    game = "Dakota Winchester's Adventures"

    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    result_obj = {
        "game": "dakota winchester's adventures",
        "results": {},
        "failed_at": None,
        "last_attempted": None
    }

    print(f"🔍 Running evaluation for: {game}")

    milestones = [
        ("milestone_prompt1", "stones_connected", "🪨 Stepping Stones Connected"),
        ("milestone_prompt2", "fire_burns", "🔥 Fire Burns"),
        ("milestone_prompt3", "temple_open", "🏛️ Temple Open"),
        ("milestone_prompt4", "monkey_banana", "🐒 Monkey Eats Banana"),
        ("milestone_prompt5", "lights_illuminate", "💡 Lights Illuminate"),
    ]

    try:
        for key, result_key, label in milestones:
            result_obj["last_attempted"] = key
            print(f"\n🏁 {key}")

            if key not in data:
                print(f"⚠️ Skipping {key} (not found in prompt data)")
                continue

            convo = await run_milestone(data[key], f"{game}_{key}")
            result = extract_boolean_result(convo)
            result_obj["results"][result_key] = result

            print(f"{label}: {result}")

            if result is not True:
                print(f"🛑 {label} failed. Stopping evaluation.")
                result_obj["failed_at"] = key
                return

        print("🎉 All milestones passed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted by user.")

    finally:
        Path("results").mkdir(exist_ok=True)
        with open("results/result_dakota.json", "w") as f:
            json.dump(result_obj, f, indent=2)
        print("📝 Result saved to results/result_dakota.json")

if __name__ == "__main__":
    asyncio.run(eval_dakota())