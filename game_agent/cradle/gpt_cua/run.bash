#!/bin/bash

PYTHON=python
MAIN_SCRIPT="main.py"
DEFAULT_PROMPT_FILE="tasks.json"

echo "🚀 Agent 자동화 루프 시작 중..."

# prompt.json 파일이 존재하면 자동으로 전달
if [ -f "$DEFAULT_PROMPT_FILE" ]; then
    echo "📝 $DEFAULT_PROMPT_FILE 감지됨, 자동으로 프롬프트 사용"
    $PYTHON $MAIN_SCRIPT "$DEFAULT_PROMPT_FILE"
else
    echo "📄 $DEFAULT_PROMPT_FILE 없음, 기본 프롬프트로 실행"
    $PYTHON $MAIN_SCRIPT
fi