# FlashAdventure: An Agent for Flash Game Environments
**Coast, FlashAdventure game agent Setup & Execution Guide**

This guide will walk you through setting up and running your game agent using the FlashAdventure framework.



## **1. Environment Setup**

### **1.1 Create a Conda Environment**

To get started, create a new Conda environment with Python 3.11 and install the necessary packages.

```bash
# Create a new Conda environment
conda create -n flashadventure python=3.11 -y

# Activate the new environment
conda activate flashadventure
```

Next, install the project's dependencies from `requirements.txt`.

```bash
pip install -r requirements.txt
```

Your environment is now ready. Let's configure the agent. 🚀

-----

## **2. Configuration**

### **2.1 API Keys (`.env`)**

You must provide your API keys to allow the agent to use various large language models. For your convenience, a .env file has been created. Please add the following content to the file:

```ini
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
ANTHROPIC_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
GEMINI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
```

⚠️ **Warning:** Keep your API keys secure and do not expose them publicly.

### **2.2 Game Prompts (`game_prompts.json`)**

The `game_prompts.json` file is where you define the instructions for how the AI should approach each game.

This file contains two key prompts that give the agent its direction:

  - **System Prompt:** This defines the AI's core identity and fundamental behavior. It's the agent's internal "operating manual," establishing high-level rules like creative problem-solving and general safety guidelines.

  - **Game Prompt:** This is the agent's "game manual." It provides specific details for each game, including the storyline, main character, goals, and conditions for winning.

**Example:** The prompts for `sherlock holmes the tea shop murder mystery`

```json
{
    "system_prompt": "[Instruction]  \nYou’re a game agent solving an adventure game. ...",
    "game_prompt": "[Prompt]\n You are now the lead agent in “Sherlock Holmes: The Tea Shop Murder Mystery” — a point-and-click detective game...."
}
```

*Note: Although the names and terminology for each agent may vary, they all serve a similar purpose.*

-----

## **3. Agent Execution**

### **3.1 The Run Script (`run.bash`)**
This guide focuses on the `coast` model. and we provide dedicated `run.bash` files for each game agent type. 

First, navigate to the `game_agent/coast/` directory. Then, create a `run.bash` file and add this script:

```bash
#!/bin/bash

SCRIPT_NAME="game_agent.py"
CONFIG_FILE="config.yaml"

python "$SCRIPT_NAME" --config "$CONFIG_FILE"
```

This script will launch the `game_agent.py` script, which uses a `config.yaml` file to set its parameters.

### **3.2 Configuration (`config.yaml`)**

The `config.yaml` file, located in the same directory, allows you to fine-tune the agent's behavior. Here are the most important variables:

```yaml
# The total number of actions the agent can take in a single session.
max_action_count: 1000

# The API provider for the large language model.
api_provider: "anthropic"

# The specific model used for high-level reasoning and planning.
reasoning_model: "claude-3-7-sonnet-20250219"

# The model used for low-level GUI control and action execution.
gui_model: "claude_cua"

# The maximum number of actions the SeekerBot can take in a single run.
max_actions_seeker: 15

# The maximum number of actions the SolverBot can take to solve a single problem.
max_actions_solver: 5
```

### **3.3 Run the Agent**

To start the agent, first grant execute permissions and then run the script from your terminal:

```bash
chmod +x run.bash  # (Run this once)
./run.bash
```

-----

## **4. Execution Summary**

1.  **API Keys:** Create a `.env` file and add your API keys.
2.  **Game Prompts:** Define your game instructions in `game_prompts.json`.
3.  **Run Script:** Create and configure `run.bash`.
4.  **Launch:** Execute `./run.bash` to start the agent.
