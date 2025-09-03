# **FlashAdventure: An Agent for Flash Game Environments - GPT Operator**

This guide covers the execution of the GPT Operator game agent developed for research on autonomous agents in Flash game environments.

All core setup, including the Python environment and API keys, is consistent with the main `README` in the parent directory. This guide focuses specifically on running this agent.

-----

### **1. Agent Execution**

#### **1.1 The Run Script (`run.bash`)**

First, navigate to the `game_agent/gpt_operator/` directory. Then, create a file named `run.bash` and add the following script. This script automatically handles loading game prompts and setting history parameters.

```bash
#!/bin/bash

PYTHON=python
MAIN_SCRIPT="main.py"
DEFAULT_PROMPT_FILE="game_prompts.json"
HISTORY=10

echo "🚀 Starting agent automation loop..."

# Automatically use the tasks.json file if it exists
if [ -f "$DEFAULT_PROMPT_FILE" ]; then
    echo "📝 $DEFAULT_PROMPT_FILE detected, using prompt automatically"
    $PYTHON $MAIN_SCRIPT "$DEFAULT_PROMPT_FILE" --history $HISTORY
else
    echo "📄 $DEFAULT_PROMPT_FILE not found, running with default prompt"
    $PYTHON $MAIN_SCRIPT --history $HISTORY
fi
```

#### **1.2 Run the Agent**

To start the agent, first grant execution permissions to the script and then run it from your terminal:

```bash
chmod +x run.bash  # (Run this once to grant permissions)
./run.bash
```

-----

### **2. Execution Summary**

1.  **Run Script:** Create and configure the `run.bash` script with your desired parameters.
2.  **Launch:** Execute `./run.bash` to start the agent.