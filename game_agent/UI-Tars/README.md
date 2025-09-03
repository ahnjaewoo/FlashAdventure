# **FlashAdventure: An Agent for Flash Game Environments - UI-TARS**

This guide covers the execution of the UI-TARS game agent, which is based on the OSWorld source code. Developed for our research on autonomous agents in Flash game environments, this guide details the steps required to configure and run the agent.

The core setup, including the Python environment and API keys, is consistent with the main `README` in the parent directory. This guide focuses specifically on the UI-TARS agent.

## **1. Agent Execution**

### **1.1 Launch the VLLM Model Server**

The UI-TARS agent requires a VLLM model server to be running. First, launch the model server on a remote GPU machine using the following command:

```bash
python -m vllm.entrypoints.openai.api_server --served-model-name ui-tars --model "ByteDance-Seed/UI-TARS-1.5-7B" --limit-mm-per-prompt image=10 --port 8000
```

### **1.2 Configure the Agent's API Endpoint**

Next, you must configure the agent to connect to your running server. Open the `mm_agents/uitars_agent.py` file and modify the `base_url` to point to your server's address.

```python
## Line 574
self.vlm = OpenAI(
    base_url="http://your_server_url:8000/v1", api_key="empty"
)
```

### **1.3 The Run Script (`run.bash`)**

Now, create a `run.bash` file in the `game_agent/UI-Tars/` directory with the following content. This simple script will execute the main entry point for the agent.

```bash
#!/bin/bash

# Execute the main agent script
python run_uitars.py
```

### **1.4 Run the Agent**

To start the agent, first grant execution permissions to the script and then run it from your terminal:

```bash
chmod +x run.bash  # (Run this once to grant permissions)
./run.bash
```

-----

### **2. Execution Summary**

1.  **Load Model:** Launch the UI-Tars model server on your remote GPU.
2.  **Configure Agent:** Update the `base_url` in `mm_agents/uitars_agent.py` to point to your server's address.
3.  **Run Script:** Create and configure the `run.bash` script with your desired parameters.
4.  **Launch:** Execute `./run.bash` to start the agent.