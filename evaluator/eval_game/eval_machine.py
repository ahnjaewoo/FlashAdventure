from dataclasses import dataclass, asdict
from typing import Dict, Any, Iterable, Optional, Tuple, List
import asyncio
import json
import re
from pathlib import Path

from judge.vlm import main as evaluator_none_cua
from judge.vlm import load_game_prompt_eval

from eval_game.eval_utils import run_milestone


# =========================
# CUA configuration
# =========================
@dataclass
class EvalConfig:
    game: str = "Machine Room Escape"
    api_provider: str = "anthropic"
    model_name: str = "claude-3-7-sonnet-20250219"
    loop_interval: int = 3
    system_prompt: Optional[str] = None
    evaluation_prompt: Optional[str] = None
    example_image_path: Optional[str] = None

    def to_kwargs(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

def prepare_prompts(game: str, image_no: int) -> Tuple[str, str, str]:
    try:
        system_prompt, evaluation_prompt, example_image_path = load_game_prompt_eval(game, image_no)
    except Exception as e:
        raise RuntimeError(f"[prepare_prompts] Fail to load prompt (game='{game}', image_no={image_no}): {e}") from e
    if not all([system_prompt, evaluation_prompt, example_image_path]):
        raise ValueError(f"[prepare_prompts] There is None at load data(image_no={image_no}).")
    return system_prompt, evaluation_prompt, example_image_path

def run_evaluation_for_image(cfg: EvalConfig, image_no: int) -> None:
    system_prompt, evaluation_prompt, example_image_path = prepare_prompts(cfg.game, image_no)
    cfg.system_prompt = system_prompt
    cfg.evaluation_prompt = evaluation_prompt
    cfg.example_image_path = example_image_path
    try:
        evaluator_none_cua(**cfg.to_kwargs())
    except Exception as e:
        raise RuntimeError(f"[run_evaluation_for_image] Executaion Error (image_no={image_no}): {e}") from e

def run_batch(
    cfg: EvalConfig,
    image_numbers: Iterable[int],
    stop_on_error: bool = False,
) -> None:
    for n in image_numbers:
        try:
            run_evaluation_for_image(cfg, n)
        except Exception as e:
            print(e)
            if stop_on_error:
                raise

# =========================
# Milestone evaluate 
# =========================

RESULT_LINE_RE = re.compile(
    r"Result\s*:\s*(\[\s*Milestone\s*:?\s*3\s*\]|Milestone\s*:?\s*3)\b",
    re.IGNORECASE
)

def extract_milestone(conversation: List[str]) -> Optional[str]:
    for msg in reversed(conversation or []):
        m = RESULT_LINE_RE.search(msg)
        if m:
            return f"Result: {m.group(1).strip()}"
    return None

async def eval_machine() -> bool:

    game = "Machine Room Escape"

    with open("milestone_prompts.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)

    data = all_data.get(game, {})
    if not data:
        print(f"❌ No data found for game: {game}")
        return False

    print(f"🎮 Running evaluation for: {game}")

    # 1) Instruction
    if "Instruction" in data:
        _ = await run_milestone(data["Instruction"], f"{game}_Instruction")

    # 2) milestone_prompt1
    prompt_key = "milestone_prompt1"
    if prompt_key not in data:
        print(f"❌ No milestone data found for {game} / {prompt_key}")
        return False

    conversation = await run_milestone(data[prompt_key], f"{game}_{prompt_key}")
    if conversation is None:
        print("⚠️ No conversation returned from agent.")
        return False

    milestone_result = extract_milestone(conversation)
    if milestone_result:
        print(f"🔍 {milestone_result}")
        Path("results").mkdir(exist_ok=True)
        with open("results/result_machine_room_eval_first.json", "w", encoding="utf-8") as f:
            json.dump({"game": "machine_room_escape", "result": milestone_result}, f, indent=2, ensure_ascii=False)
        print("📝 Saved eval-first result -> results/result_machine_room_eval_first.json")
        return True

    print("ℹ️ 'Result: Milestone 3' 미검출 → CUA로 진행")
    return False

# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    # 1) First milestone Evaluation
    achieved = asyncio.run(eval_machine())

    # 2) Milestone -> 3: Finish or Running CUA
    if achieved:
        print(" Milestone 3  → Finish")
    else:
        print(" Not Milestone 3 → Running CUA ")
        base_cfg = EvalConfig(
            game="machine_room_escape",
            api_provider="anthropic",
            model_name="claude-3-7-sonnet-20250219",
            loop_interval=3,
        )
        run_batch(base_cfg, image_numbers=[1, 2, 3], stop_on_error=False)