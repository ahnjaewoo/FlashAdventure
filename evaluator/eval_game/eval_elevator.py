import asyncio
import json
import re
from eval_game.eval_utils import run_milestone

def parse_continue_flag(msg: str) -> str:
    """
    Returns:
      - "continue" if the message contains 'Continue: True'
      - "final"    if the message contains 'Continue: Final'
      - "stop"     otherwise (includes 'Continue: False' or missing)
    """
    if not msg:
        return "stop"
    msg = msg.strip()
    if "Continue: True" in msg:
        return "continue"
    if "Continue: Final" in msg:
        return "final"
    return "stop"

def extract_result(conversation: list[str]) -> str | None:
    """
    Find the last line in the conversation that contains 'Result:'.
    Returns the full line, or None if not found.
    """
    for msg in reversed(conversation):
        if "Result:" in msg:
            return msg
    return None

def extract_final_stage(msg: str) -> str | None:
    """
    Extract the numeric 'Final Stage' value from a result string.
    Example:
        'Result: [Final Stage: 2, Continue: True]' -> '2'
    Returns None if not found.
    """
    if not msg:
        return None
    m = re.search(r"Final Stage:\s*(\d+)", msg)
    return m.group(1) if m else None

async def eval_elevator():
    game = "Elevator Room Escape"

    # Load prompts
    with open("milestone_prompts.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return

    print(f"🎮 Starting evaluation for: {game}")

    # Run milestones 1..4 if present (works fine even if only 1..3 exist)
    for i in range(1, 4 + 1):
        prompt_key = f"milestone_prompt{i}"
        prompt = data.get(prompt_key)
        if not prompt:
            # Skip if this milestone is not defined
            continue

        print(f"\n🏁 {game} - {prompt_key}")
        conversation = await run_milestone(prompt, f"{game}_{prompt_key}")

        # Extract and print ONLY the Final Stage
        result_line = extract_result(conversation)
        final_stage = extract_final_stage(result_line or "")
        print(f"🎯 Final Stage: {final_stage if final_stage is not None else 'N/A'}")

        # Control flow based on Continue flag
        status = parse_continue_flag(result_line or "")
        if status == "continue":
            continue  # proceed to next milestone
        elif status == "final":
            print(f"🏁 Final milestone reached at {prompt_key}. Evaluation ends.")
            return
        else:
            print(f"🛑 Evaluation stopped after {prompt_key}")
            return

    print("✅ All available milestones completed.")

if __name__ == "__main__":
    asyncio.run(eval_elevator())