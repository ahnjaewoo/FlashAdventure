# **FlashAdventure: Cua-as-a-Judge for evaluating milestones**

This guide provides instructions for setting up and running the FlashAdventure Cua-as-a-Judge evaluation system.

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


## **2. Configuration**

### **2.1 API Keys (`.env`)**

You must provide your API keys to allow the agent to use various large language models. For your convenience, a `.env` file has been created. Please add the following content to the file:

```ini
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
ANTHROPIC_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
GEMINI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
```

⚠️ **Warning:** Keep your API keys secure and do not expose them publicly.

### **2.2 Evaluation Prompts (`milestone_prompts.json`)**

The `milestone_prompts.json` file defines the instructions for how the AI should approach each evaluation task. We use two primary evaluation methods:

  - **Cua-as-a-Judge**: This method uses an LLM (such as Claude or GPT) to visually analyze a screenshot and evaluate the game state based on a detailed prompt. This is typically done using the **`milestone_prompt`** key.

  - **None-Cua (Image Comparison)**: This method uses predefined reference images and prompts for a direct comparison. It relies on the **`prompt`**, **`evaluation_prompt`**, and **`example_image_path`** keys to guide the comparison process.

### **2.3 Key Fields Explained**

Based on your JSON object's structure, the prompts are divided into two main categories, each with a distinct purpose for guiding the AI.

**High-Level Agent Instructions**

These prompts are designed to give an AI agent a general overview of its role and the task it needs to accomplish.

- **prompt:** This defines the AI's core mission for the entire game session. It sets the agent's persona and primary objective, such as "escape the room" or "solve the murder mystery." This prompt is meant to be a high-level guide rather than a step-by-step command.

- **Instruction:** This provides a series of explicit, sequential actions for the agent to follow to complete a specific task. It's a precise, procedural guide meant to be executed step-by-step, such as "navigate to a door and click it." This is typically used for a single, focused sub-task.

**Task and Evaluation Prompts**

These prompts are used for evaluating the agent's progress or for guiding a single, specific action or milestone.

- **milestone_prompt:** A comprehensive, step-by-step set of instructions for an AI evaluator. It's used to check if a specific condition in the game has been met. The prompt often includes a series of navigation steps and a precise output format, such as counting items or reporting a True/False value.

- **evaluation_prompt:** This is a detailed prompt for a milestone-checking task, often used in conjunction with a visual reference. It instructs the AI to analyze a screenshot and compare it against a specific set of criteria, like counting items in an inventory or identifying a specific pattern.

- **example_image_path:** This provides a file path to a reference image. The image is used as a visual aid for the evaluation_prompt, allowing the AI to perform visual tasks that would be difficult with text alone. It offers crucial context for the evaluation process.

**Note:** Some games may use a combination of both methods.

**Example:** The prompt for `sherlock_holmes_the_tea_shop_murder_mystery`

```json
{
    "sherlock_holmes_the_tea_shop_murder_mystery": {
        "milestone_prompt1":"You are an AI agent specializing in the Sherlock Holmes detective game. Your task is to locate and click the blue notebook icon in the game interface (usually found at the far right of the inventory bar). Once the notebook is opened, do not perform any additional actions. Carefully read the displayed text (do not scroll) and count how many times the phrase 'New Suspect' appears in the note. If there is nothing written in the note, it means there is no new suspect. Once counted, output the result in the following format: ### Output Format #### New Suspect: [Number of occurrences]Do not perform any further interactions after counting. Your task ends once the count is provided."
    }
}
```


## **3. Agent Execution**

### **3.1 The Run Script (`run.bash`)**

The evaluation script, `evaluate_game.py`, is the main entry point for running the agent. This file is designed to execute various `eval_{game_name}.py` files, allowing for easy and scalable evaluation of different games. By adding your own milestone-based files to the `eval_game` directory, you can quickly evaluate new games.

First, navigate to the `evaluator/` directory. Then, create a `run.bash` file and add the following script:

```bash
#!/bin/bash
# at AdventureBench_final/evaluator/.
python evaluate_game.py
```

### **3.2 Run the Agent**

To start the agent, first grant execute permissions and then run the script from your terminal:

```bash
chmod +x run.bash  # (Run this once)
./run.bash
```


## **4. Execution Summary**

1.  **API Keys:** Create a `.env` file and add your API keys.
2.  **Evaluation Prompts:** If you want, refine your evaluation instructions in `milestone_prompts.json`.
3.  **Run Script:** Create the `run.bash` file.
4.  **Launch:** Execute `./run.bash` to start the agent.