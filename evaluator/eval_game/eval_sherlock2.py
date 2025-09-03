import asyncio
import json
import re
from pathlib import Path
from typing import List

from eval_game.eval_utils import run_milestone

def extract_found_items(conversation: List[str]) -> int:
    for msg in reversed(conversation):
        match = re.search(r"#Found Items:\s*(\d+)", msg, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return -1

def extract_boolean_result(conversation: List[str]) -> bool | None:
    for msg in reversed(conversation):
        match = re.search(r"Result:\s*(True|False)", msg, re.IGNORECASE)
        if match:
            return match.group(1).lower() == "true"
    return None

async def eval_sherlock2():
    game = "Sherlock Holmes 2"

    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    result_obj = {
        "game": "sherlock_holmes_2",
        "results": {},
        "failed_at": None
    }

    print(f"🔍 Running evaluation for: {game}")

    try:
        # === milestone_prompt1 (Always run, even if it fails) ===
        key = "milestone_prompt1"
        print(f"\n🏁 {key}")
        convo1 = await run_milestone(data[key], f"{game}_{key}")
        found_items = extract_found_items(convo1)

        result_obj["results"]["found_items"] = found_items
        print(f"🧾 Found Items: {found_items}")

        # === milestone_prompt2 (fails => stop) ===
        key = "milestone_prompt2"
        print(f"\n🏁 {key}")
        convo2 = await run_milestone(data[key], f"{game}_{key}")
        result2 = extract_boolean_result(convo2)

        result_obj["results"]["fire_alarm_open"] = result2
        print(f"🚨 Fire Alarm Open (2F): {result2}")

        if result2 is not True:
            result_obj["failed_at"] = key
            print(f"🛑 Failed at {key}: Fire alarm is not open.")
            return

        # === milestone_prompt3 (fails => stop) ===
        key = "milestone_prompt3"
        print(f"\n🏁 {key}")
        convo3 = await run_milestone(data[key], f"{game}_{key}")
        result3 = extract_boolean_result(convo3)

        result_obj["results"]["leaves_burn"] = result3
        print(f"🔥 Leaves Burning (1F): {result3}")

        if result3 is not True:
            result_obj["failed_at"] = key
            print(f"🛑 Failed at {key}: Leaves are not burning.")
            return

        # ✅ All passed
        print("🎉 All milestones passed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted by user.")

    finally:
        save_results(result_obj)

def save_results(result_obj):
    Path("results").mkdir(exist_ok=True)
    with open("results/result_sherlock2.json", "w") as f:
        json.dump(result_obj, f, indent=2)
    print("📝 Result saved to results/result_sherlock2.json")

if __name__ == "__main__":
    asyncio.run(eval_sherlock2())