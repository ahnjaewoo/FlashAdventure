import asyncio
import json
import re
from pathlib import Path
from typing import List

from eval_game.eval_utils import run_milestone

def extract_found_places(conversation: List[str]) -> int:
    for msg in reversed(conversation):
        match = re.search(r"#Found Place:\s*(\d+)", msg, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return -1

def extract_boolean_result(conversation: List[str]) -> bool | None:
    for msg in reversed(conversation):
        match = re.search(r"Result:\s*(True|False)", msg, re.IGNORECASE)
        if match:
            return match.group(1).lower() == "true"
    return None

async def eval_vortex():
    game = "Vortex Point1"

    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    result_obj = {
        "game": "vortex_point1",
        "results": {}
    }

    print(f"🔍 Running evaluation for: {game}")

    # === milestone_prompt1 ===
    key = "milestone_prompt1"
    print(f"\n🏁 {key}")
    convo1 = await run_milestone(data[key], f"{game}_{key}")
    places = extract_found_places(convo1)

    result_obj["results"]["found_places"] = places
    print(f"📌 Found Places: {places}")

    if places != 8:
        print("🛑 Found Places is not exactly 8. Stopping evaluation.")
        return

    # === milestone_prompt2 ===
    key = "milestone_prompt2"
    print(f"\n🏁 {key}")
    convo2 = await run_milestone(data[key], f"{game}_{key}")
    result2 = extract_boolean_result(convo2)

    result_obj["results"]["door_2956_open"] = result2
    print(f"🚪 2956 Vineyard Drive Door Open: {result2}")

    if result2 is not True:
        print("🛑 Door is not open. Stopping evaluation.")
        return

    # === milestone_prompt3 ===
    key = "milestone_prompt3"
    print(f"\n🏁 {key}")
    convo3 = await run_milestone(data[key], f"{game}_{key}")
    result3 = extract_boolean_result(convo3)

    result_obj["results"]["wing_c_open"] = result3
    print(f"🚪 Wing C Door Open: {result3}")

    Path("results").mkdir(exist_ok=True)
    with open("results/result_vortex.json", "w") as f:
        json.dump(result_obj, f, indent=2)
    print("📝 Result saved to results/result_vortex.json")

if __name__ == "__main__":
    asyncio.run(eval_vortex())