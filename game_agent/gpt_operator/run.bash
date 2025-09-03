#!/bin/bash

PYTHON=python
MAIN_SCRIPT="main.py"
DEFAULT_PROMPT_FILE="game_prompts.json"
HISTORY=10

echo "🚀 Starting agent automation loop..."

# Automatically pass the prompt.json file if it exists
if [ -f "$DEFAULT_PROMPT_FILE" ]; then
    echo "📝 $DEFAULT_PROMPT_FILE detected, using prompt automatically"
    $PYTHON $MAIN_SCRIPT "$DEFAULT_PROMPT_FILE" --history $HISTORY
else
    echo "📄 $DEFAULT_PROMPT_FILE not found, running with default prompt"
    $PYTHON $MAIN_SCRIPT --history $HISTORY
fi