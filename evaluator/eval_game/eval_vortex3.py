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

async def eval_vortex3():
    game = "Vortex Point3"

    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    result_obj = {
        "game": "vortex_point3",
        "results": {},
        "failed_at": None,
        "last_attempted": None
    }

    print(f"🔍 Running evaluation for: {game}")

    # milestone
    milestones = [
        ("milestone_prompt1", "eat_hamburger", "Man eating hamburger"),
        ("milestone_prompt2", "toilet_open", "Toilet Open"),
        ("milestone_prompt3", "shopkeeper_gone", "Shop Keeper Gone"),
        ("milestone_prompt4", "ride_boat", "Ride Boat")
    ]

    try:
        for key, result_key, label in milestones:
            result_obj["last_attempted"] = key
            print(f"\n🏁 {key}")

            if key not in data:
                print(f"⚠️ Skipping {key} (not present in prompt data)")
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
        with open("results/result_vortex3.json", "w") as f:
            json.dump(result_obj, f, indent=2)
        print("📝 Result saved to results/result_vortex3.json")

if __name__ == "__main__":
    asyncio.run(eval_vortex3())