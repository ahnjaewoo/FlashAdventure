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

async def eval_vortex2():
    game = "Vortex Point2"

    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    result_obj = {
        "game": "vortex_point2",
        "results": {},
        "failed_at": None,
        "last_attempted": None
    }

    print(f"🔍 Running evaluation for: {game}")

    try:
        for i in range(1, 5):
            key = f"milestone_prompt{i}"
            result_obj["last_attempted"] = key
            print(f"\n🏁 {key}")

            convo = await run_milestone(data[key], f"{game}_{key}")
            result = extract_boolean_result(convo)

            match i:
                case 1: result_obj["results"]["pub_owner_gone"] = result
                case 2: result_obj["results"]["magician_gone"] = result
                case 3: result_obj["results"]["security_guard_gone"] = result
                case 4: result_obj["results"]["fence_open"] = result

            print(f"✅ Result: {result}")

            if result is not True:
                print(f"🛑 Condition failed at {key}. Stopping evaluation.")
                result_obj["failed_at"] = key
                return

        print("🎉 All milestones passed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted by user.")

    finally:
        Path("results").mkdir(exist_ok=True)
        with open("results/result_vortex2.json", "w") as f:
            json.dump(result_obj, f, indent=2)
        print("📝 Result saved to results/result_vortex2.json")

if __name__ == "__main__":
    asyncio.run(eval_vortex2())