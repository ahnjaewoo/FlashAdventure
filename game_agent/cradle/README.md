I will gladly help you polish your `README` file. The current draft is a bit repetitive, as it has two separate sections (`1.1 The Run Script` and `1.2 Configuration`) that contain similar information about the agent's configuration.

I will streamline this by combining all the configuration details into a single `run.bash` script. This makes the setup process much more direct and easier to follow, which is perfect for a research paper's documentation.

-----

# **FlashAdventure: An Agent for Flash Game Environments - Cradle**

This project presents a reproduction of the `cradle` game agent, adapted for our research on autonomous agents in Flash game environments. This guide details the steps required to configure and run the agent.

All core setup, including the Python environment and API keys, is consistent with the main `README` in the parent directory. This guide focuses specifically on running this agent.

## **1. Agent Execution**

### **1.1 The Run Script (`run.bash`)**

First, navigate to the `game_agent/cradle/` directory. Then, create a `run.bash` file and add the following script. You can directly edit the variables in this script to configure the agent's behavior.

```bash
#!/bin/bash

# Configuration
# API Provider: Select one of "anthropic" or "openai".
PROVIDER="anthropic"

# LLM Model: Specifies the model for high-level reasoning.
MODEL="claude-3-7-sonnet-20250219"

# GUI Agent Type: Select the agent responsible for mouse/keyboard operations.
# "claude": A Claude agent specialized for computer control.
# "sonnet": An agent that uses the original Claude Sonnet model directly.
# "uground": An open-source UGround model.
CUA="claude"

# Execute
python main.py --model "$MODEL" --provider "$PROVIDER" --cua "$CUA"
```

### **1.2 Run the Agent**

To start the agent, grant execute permissions and run the script from your terminal:

```bash
chmod +x run.bash  # (Run this once)
./run.bash
```

-----

## **2. Execution Summary**

1.  **Run Script:** Create and configure `run.bash` with your desired parameters.
2.  **Launch:** Execute `./run.bash` to start the agent.