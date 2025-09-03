import asyncio
import json
import re
from pathlib import Path
from typing import List, Optional

from eval_game.eval_utils import run_milestone

GREEN_RE = re.compile(r"Green\s*Lights\s*:\s*(\d+(?:\.\d+)?)", re.IGNORECASE)

def extract_green_lights(conversation: List[str]) -> Optional[float]:
    for msg in reversed(conversation or []):
        m = GREEN_RE.search(msg)
        if m:
            return float(m.group(1))
    return None

async def eval_videostudio():
    game = "Video Studio Escape"

    # Load prompt from milestone_prompts.json
    with open("milestone_prompts.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)

    data = all_data.get(game)
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    print(f"🎮 Running evaluation for: {game}")

    # 1) Instruction
    if "Instruction" in data:
        _ = await run_milestone(data["Instruction"], f"{game}_Instruction")

    # 2) milestone_prompt1
    if "milestone_prompt1" not in data:
        print(f"❌ No milestone data found for {game} / milestone_prompt1")
        return

    conversation = await run_milestone(data["milestone_prompt1"], f"{game}_milestone_prompt1")
    if conversation is None:
        print("⚠️ No conversation returned from agent.")
        return

    green = extract_green_lights(conversation)
    if green is not None:
        print(f"Green Lights: {green}")

        result_obj = {
            "game": "video_studio_escape",
            "result": f"green_lights: {green}",
            "green_lights": green,
        }

        Path("results").mkdir(exist_ok=True)
        with open("results/result_videostudio.json", "w", encoding="utf-8") as f:
            json.dump(result_obj, f, indent=2, ensure_ascii=False)
        print("📝 Result saved to results/result_videostudio.json")
    else:
        print("⚠️ Couldn't find green_lights in result.")

if __name__ == "__main__":
    asyncio.run(eval_videostudio())