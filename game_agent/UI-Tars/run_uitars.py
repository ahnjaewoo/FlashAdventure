import argparse
import datetime
import json
import logging
import os
import sys

from tqdm import tqdm

os.makedirs("logs", exist_ok=True)


import lib_run_single
from desktop_env.desktop_env import LocalDesktopEnv  
from mm_agents.uitars_agent import UITARSAgent


# Logger setup
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
datetime_str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")

file_handler = logging.FileHandler(os.path.join("logs", f"normal-{datetime_str}.log"), encoding="utf-8")
debug_handler = logging.FileHandler(os.path.join("logs", f"debug-{datetime_str}.log"), encoding="utf-8")
stdout_handler = logging.StreamHandler(sys.stdout)
sdebug_handler = logging.FileHandler(os.path.join("logs", f"sdebug-{datetime_str}.log"), encoding="utf-8")

file_handler.setLevel(logging.INFO)
debug_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(logging.INFO)
sdebug_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt="\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s \x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] \x1b[0m%(message)s"
)

for h in [file_handler, debug_handler, stdout_handler, sdebug_handler]:
    h.setFormatter(formatter)

stdout_handler.addFilter(logging.Filter("desktopenv"))
sdebug_handler.addFilter(logging.Filter("desktopenv"))

logger.addHandler(file_handler)
logger.addHandler(debug_handler)
logger.addHandler(stdout_handler)
logger.addHandler(sdebug_handler)

logger = logging.getLogger("desktopenv.experiment")


def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run UITARS in local desktop environment")
    parser.add_argument("--action_space", type=str, default="pyautogui")
    parser.add_argument("--observation_type", choices=["screenshot", "a11y_tree", "screenshot_a11y_tree", "som"], default="screenshot")
    parser.add_argument("--screen_width", type=int, default=1920)
    parser.add_argument("--screen_height", type=int, default=1080)
    parser.add_argument("--sleep_after_execution", type=float, default=0.0)
    parser.add_argument("--max_steps", type=int, default=10000)
    parser.add_argument("--max_trajectory_length", type=int, default=10)
    parser.add_argument("--model_type", type=str, default="qwen25vl")
    parser.add_argument("--infer_mode", type=str, default="qwen25vl_normal")
    parser.add_argument("--prompt_style", type=str, default="qwen25vl_normal")
    parser.add_argument("--input_swap", action="store_true")
    parser.add_argument("--language", type=str, default="English")
    parser.add_argument("--max_pixels", type=float, default=16384 * 28 * 28)
    parser.add_argument("--min_pixels", type=float, default=100 * 28 * 28)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--top_k", type=int, default=-1)
    parser.add_argument("--history_n", type=int, default=10)
    parser.add_argument("--callusr_tolerance", type=int, default=3)
    parser.add_argument("--max_tokens", type=int, default=1000)
    parser.add_argument("--stop_token", type=str, default=None)
    parser.add_argument("--result_dir", type=str, default="./results")
    return parser.parse_args()


def Game_Agent(args: argparse.Namespace, example):
    agent = UITARSAgent(
        action_space=args.action_space,
        observation_type=args.observation_type,
        max_trajectory_length=args.max_trajectory_length,
        model_type=args.model_type,
        runtime_conf={
            "infer_mode": args.infer_mode,
            "prompt_style": args.prompt_style,
            "input_swap": args.input_swap,
            "language": args.language,
            "history_n": args.history_n,
            "max_pixels": args.max_pixels,
            "min_pixels": args.min_pixels,
            "callusr_tolerance": args.callusr_tolerance,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "top_k": args.top_k,
            "max_tokens": args.max_tokens,
        },
    )

    env = LocalDesktopEnv(
        game_name=selected_game,
        action_space=agent.action_space,
        screen_size=(args.screen_width, args.screen_height),
        require_a11y_tree=args.observation_type in ["a11y_tree", "screenshot_a11y_tree", "som"],
    )

    example_result_dir = os.path.join(args.result_dir, "custom_prompt")
    os.makedirs(example_result_dir, exist_ok=True)

    try:
        lib_run_single.run_single_example(
            agent,
            env,
            example,
            args.max_steps,
            example["instruction"],
            args,
            example_result_dir,
            [],
        )
    except Exception as e:
        logger.error(f"Exception: {e}")
        with open(os.path.join(example_result_dir, "traj.jsonl"), "a") as f:
            f.write(json.dumps({"Error": f"Run failed: {e}"}) + "\n")

    env.close()


if __name__ == "__main__":
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    args = config()

    with open("game_prompts.json", "r", encoding="utf-8") as f:
        game_prompts = json.load(f)

    print("\n[게임 선택]")
    keys = list(game_prompts.keys())
    for idx, key in enumerate(keys):
        print(f"{idx + 1}. {key}")
    choice = int(input("게임 번호 입력 (ex: 1): ")) - 1
    selected_game = keys[choice]
    selected_prompt = game_prompts[selected_game]

    example = {
        "instruction": selected_prompt["system_prompt"] + "\n" + selected_prompt["game_prompt"],
        "game_name": selected_game,
        "id": "custom_prompt"
    }

    logger.info(f"Selected game: {selected_game}")
    Game_Agent(args, example)