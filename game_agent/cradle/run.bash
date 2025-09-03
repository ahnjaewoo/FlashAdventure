#!/bin/bash

MODEL="claude-3-7-sonnet-20250219"
PROVIDER="anthropic"
CUA="claude"

## other_options
# MODEL="gpt-4o"
# PROVIDER="openai"
# CUA="gpt"
# CUA="sonnet"
# CUA="uground"

## Execute
python main.py --model "$MODEL" --provider "$PROVIDER" --cua "$CUA"