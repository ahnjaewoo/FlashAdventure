import asyncio
import json
from eval_game.eval_utils import run_milestone

def parse_continue_flag(msg: str) -> str:
    if "Continue: True" in msg:
        return "continue"
    if "Continue: Final" in msg:
        return "final"
    return "stop"

def extract_result(conversation: list[str]) -> str | None:
    for msg in reversed(conversation):
        if "Result:" in msg:
            return msg
    return None

async def eval_gamecafe():
    game = "Game Cafe Escape"

    # Prompt Load
    with open("milestone_prompts.json", "r") as f:
        all_data = json.load(f)
    
    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    print(f"🎮 Starting evaluation for: {game}")

    # === milestone_prompt1 ===
    prompt_key = "milestone_prompt1"
    if prompt_key in data:
        print(f"\n🏁 {game} - {prompt_key}")
        conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")
        result = extract_result(conversation)
        print("🔍 Result:", result)

        status = parse_continue_flag(result or "")
        if status != "continue":
            print("🛑 Evaluation stopped after milestone 1")
            return

    # === milestone_prompt2 ===
    prompt_key = "milestone_prompt2"
    if prompt_key in data:
        print(f"\n🏁 {game} - {prompt_key}")
        conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")
        result = extract_result(conversation)
        print("🔍 Result:", result)

        status = parse_continue_flag(result or "")
        if status != "continue":
            print("🛑 Evaluation stopped after milestone 2")
            return

    # === milestone_prompt3 ===
    prompt_key = "milestone_prompt3"
    if prompt_key in data:
        print(f"\n🏁 {game} - {prompt_key}")
        conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")
        result = extract_result(conversation)
        print("🔍 Result:", result)

        status = parse_continue_flag(result or "")
        if status != "continue":
            print("🛑 Evaluation stopped after milestone 3")
            return

    # === milestone_prompt4 ===
    prompt_key = "milestone_prompt4"
    if prompt_key in data:
        print(f"\n🏁 {game} - {prompt_key}")
        conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")
        result = extract_result(conversation)
        print("🔍 Result:", result)

        status = parse_continue_flag(result or "")
        if status != "continue":
            print("🛑 Evaluation stopped after milestone 4")
            return

    # === milestone_prompt5 ===
    prompt_key = "milestone_prompt5"
    if prompt_key in data:
        print(f"\n🏁 {game} - {prompt_key}")
        conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")
        result = extract_result(conversation)
        print("🔍 Result:", result)

        status = parse_continue_flag(result or "")
        if status != "continue":
            print("🏁 Final milestone reached or evaluation ends.")
            return

    print("✅ All available milestones completed.")

if __name__ == "__main__":
    asyncio.run(eval_gamecafe())