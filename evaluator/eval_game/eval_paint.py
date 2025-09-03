import asyncio
import json
import re
from pathlib import Path
from typing import List, Optional

from eval_game.eval_utils import run_milestone

DOOR_INDEX_RE = re.compile(r"Door\s*Index\s*:\s*(\d+(?:\.\d+)?)", re.IGNORECASE)

def extract_door_index(conversation: List[str]) -> Optional[float]:
    for msg in reversed(conversation or []):
        m = DOOR_INDEX_RE.search(msg)
        if m:
            return float(m.group(1))
    return None

async def eval_paint():
    game = "Paint Room Escape"

    # Load prompt from milestone_prompts.json
    with open("milestone_prompts.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    print(f"🎮 Running evaluation for: {game}")

    # 1) Instruction 
    if "Instruction" in data:
        _ = await run_milestone(data["Instruction"], f"{game}_Instruction")

    # 2) milestone_prompt1 
    prompt_key = "milestone_prompt1"
    if prompt_key not in data:
        print(f"❌ No milestone data found for {game} / {prompt_key}")
        return

    conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")
    if conversation is None:
        print("⚠️ No conversation returned from agent.")
        return

    door_index = extract_door_index(conversation)

    if door_index is not None:
        print(f"Door color index: {door_index}")

        result_obj = {
            "game": "paint_room_escape",
            "result": f"door_color_index: {door_index}",
            "door_color_index": door_index,
        }

        Path("results").mkdir(exist_ok=True)
        with open("results/result_paint.json", "w", encoding="utf-8") as f:
            json.dump(result_obj, f, indent=2, ensure_ascii=False)
        print("📝 Result saved to results/result_paint.json")
    else:
        print("⚠️ Couldn't find door_color_index in result.")

if __name__ == "__main__":
    asyncio.run(eval_paint())