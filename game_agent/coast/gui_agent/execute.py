import asyncio
from gui_agent.gpt_cua import main_gpt_operator
from gui_agent.claude_cua import main as main_claude_cua
from gui_agent.gui_grounding import agent_step as main_uground
from gui_agent.gui_grounding import run_claude_gui_agent as main_claude_sonnet

def execute_action(action_prompt, system_prompt=None, encoded_image=None, gui_model="gpt_operator", reasoning_model="gpt-4o", type=None):
    if gui_model == "gpt_operator":
        return main_gpt_operator(
            user_prompt=action_prompt
        )
    
    elif gui_model == "claude_cua":
        return asyncio.run(main_claude_cua(
            user_prompt=action_prompt,
            system_prompt=system_prompt,
            type=type
        ))
    
    elif gui_model == "uground":
        api_provider = "openai" if reasoning_model == "gpt-4o" else "anthropic"
        return asyncio.run(main_uground(
            user_prompt=action_prompt,
            encoded_image=encoded_image,
            provider=api_provider,
            model=reasoning_model
        ))
        
    elif gui_model == "claude_sonnet":
        return asyncio.run(main_claude_sonnet(
            user_prompt=action_prompt,
            encoded_image=encoded_image
        ))
    else:
        print(f"[ERROR] Unknown gui_model: {gui_model}")
        return 0