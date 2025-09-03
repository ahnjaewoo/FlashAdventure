# **FlashAdventure: An Agent for Flash Game Environments - Claude Computer Use**

This guide covers the execution of the Claude Computer Use game agent developed for research on autonomous agents in Flash game environments.

All core setup, including creating the Python environment and configuring API keys, is consistent with the main `README` in the parent directory. This guide focuses specifically on running this agent.

-----

### **1. Agent Execution**

#### **1.1 The Run Script (`run.bash`)**

First, navigate to the `game_agent/claude_computer_use/` directory. Create a file named `run.bash` and add the following script. This script defines key execution parameters and then launches the agent.

```bash
#!/bin/bash

# Ensure Python can find the agent modules in the parent directory
export PYTHONPATH=$(pwd)/..

# Configuration for the agent
# The file containing game-specific prompts
TASK_FILE="./json/game_prompt.json"
# The type of prompt to use from the file (e.g., "prompt")
PROMPT_TYPE="prompt"
# The maximum number of actions the agent will take in a single session
MAX_ACTIONS=1000

# Execute the main agent script with the defined parameters
python main.py \
  --task-file "$TASK_FILE" \
  --prompt-type "$PROMPT_TYPE" \
  --max-actions "$MAX_ACTIONS"
```

#### **1.2 Run the Agent**

To start the agent, first grant execute permissions to the script and then run it from your terminal:

```bash
chmod +x run.bash  # (Run this once to grant permissions)
./run.bash
```

-----

### **2. Execution Summary**

1.  **Run Script:** Create and configure the `run.bash` script with your desired parameters.
2.  **Launch:** Execute `./run.bash` to start the agent.