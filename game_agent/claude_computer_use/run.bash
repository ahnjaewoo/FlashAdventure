#!/bin/bash

export PYTHONPATH=$(pwd)/..

# Choose task by number (1-based index from tasks.json)

TASK_FILE="./json/game_prompt.json"
PROMPT_TYPE="prompt"
MAX_ACTIONS=1000

python main.py \
  --task-file "$TASK_FILE" \
  --prompt-type "$PROMPT_TYPE" \
  --max-actions "$MAX_ACTIONS"