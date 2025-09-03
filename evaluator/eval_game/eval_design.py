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

async def eval_design():
    game = "Design House Escape"

    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    result_obj = {
        "game": "design_house_escape",
        "results": {},
        "failed_at": None,
        "last_attempted": None
    }

    print(f"🔍 Running evaluation for: {game}")

    milestones = [
        ("milestone_prompt1", "cube_exists", "🧊 Cube Exists"),
        ("milestone_prompt2", "1st_door_open", "🚪 1st Door Open"),
        ("milestone_prompt3", "2nd_door_open", "🚪 2nd Door Open"),
        ("milestone_prompt4", "3rd_door_open", "🚪 3rd Door Open"),
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
        with open("results/result_design.json", "w") as f:
            json.dump(result_obj, f, indent=2)
        print("📝 Result saved to results/result_design.json")

if __name__ == "__main__":
    asyncio.run(eval_design())