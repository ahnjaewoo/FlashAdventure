import json
import sys
import re
import asyncio
from pathlib import Path
from judge.computer_use.main import main as run_main

TEMP_TASK_FILE = "temp_task.json"

async def run_milestone(prompt_text: str, task_name: str) -> list[str]:
    task_data = {
        task_name: {
            "milestone_prompt": prompt_text
        }
    }
    with open(TEMP_TASK_FILE, "w") as f:
        json.dump(task_data, f)

    sys.argv = [
        "main.py",
        "--task-file", TEMP_TASK_FILE,
        "--task-name", task_name,
        "--prompt-type", "milestone_prompt"
    ]

    return await run_main()  # returns conversation