import asyncio
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from eval_game.eval_utils import run_milestone


COLOR_LINE_RE = re.compile(r"Color\s*:\s*([A-Za-z\- ]+)", re.IGNORECASE)

CANONICAL_COLORS = {
    "red": "Red",
    "yellow": "Yellow",
    "green": "Green",
    "sky-blue": "Sky-Blue", 
    "blue": "Blue",
    "pink": "Pink",
}

def normalize_color_name(raw: str) -> Tuple[str, Optional[str]]:

    raw_trimmed = (raw or "").strip()


    s = raw_trimmed.lower().strip()


    s = re.sub(r"\s+", " ", s)         
    s = s.replace(" ", "-")             

    s = re.sub(r"[^a-z\-]", "", s)

    canonical = CANONICAL_COLORS.get(s)
    return raw_trimmed, canonical

def extract_color(conversation: List[str]) -> Optional[str]:

    for msg in reversed(conversation or []):
        m = COLOR_LINE_RE.search(msg)
        if m:
            raw = m.group(1)
            _raw_trimmed, canonical = normalize_color_name(raw)
            if canonical:
                return canonical

    return None

# =========================
# Evalutator
# =========================
async def eval_space():
    game = "Space Museum Escape"

    # milestone_prompts.json
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

    color = extract_color(conversation)

    if color is not None:
        print(f"Color: {color}")

        result_obj = {
            "game": "space_museum_escape",
            "result": f"color: {color}",
            "color": color,
        }

        Path("results").mkdir(exist_ok=True)
        with open("results/result_space_museum.json", "w", encoding="utf-8") as f:
            json.dump(result_obj, f, indent=2, ensure_ascii=False)
        print("📝 Result saved to results/result_space_museum.json")
    else:
        print("⚠️ Couldn't find Color in result.")

if __name__ == "__main__":
    asyncio.run(eval_space())