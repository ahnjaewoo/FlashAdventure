from api import api_caller
from agent.cradle.memory import load_memory, get_recent_tasks, get_recent_image_paths
from tools import encode_images_to_base64

def plan_actions(system_prompt, env_summary, screen, api_provider, model_name, game_name, cua):
    # 1. Load memory with cua-based paths
    verified_skills = load_memory("skill", game_name, api_model=model_name, cua=cua)
    history, _ = get_recent_tasks(n=10, game_name=game_name, api_model=model_name, cua=cua)
    _, reflection = get_recent_tasks(n=10, game_name=game_name, api_model=model_name, cua=cua)

    # 2. Load recent screenshots from cua/model-specific directory
    image_history_path = get_recent_image_paths(
        base_dir=f'screenshots/{cua}/{model_name}',
        game_name=game_name,
        limit=10,
        extensions=['.png']
    )
    image_history_base64 = encode_images_to_base64(image_history_path)
    all_images = image_history_base64 + [screen]

    # 3. Compose prompt
    prompt = f"""
    Available Skills:\n
    {verified_skills}\n\n

    Task Episodic History:\n
    {history}\n\n

    Task Reflection History:\n
    {reflection}\n\n

    History Screens:\n
    [Attached images: 1~10]\n\n

    Current Screen:\n
    [Attached image: 11 (latest)]\n\n

    Screen Analysis Summary:\n
    {env_summary}\n\n

    Based on the information above, suggest the **most appropriate single action** to take on the current screen.\n\n

    [Important]\n
    Please follow these guidelines:\n

    - Clearly suggest **only one specific behavior or interaction**.\n
    - Your action should be based on the **current screen**, **past task history**, and especially the **latest reflection**.\n
    - Prioritize **actions that haven’t been recently attempted**. However, if there is a clear reason to revisit a previous action based on new context, it can be reconsidered.\n  
    - Actively incorporate any **suggestions, questions, or hypotheses** mentioned in the reflection history.\n  
    - Focus on actions that help with **advancing in the game**, not just aiming for the final goal.\n  
    - Sometimes, **navigating the current situation**—like closing a popup, switching screens, or resetting the view—is necessary and meaningful. These actions are valid and often crucial.\n  
    - Do not attempt to solve pattern-based puzzles or item combinations through random guessing or brute force.\n 
    - If the current puzzle or situation requires prior knowledge (e.g., codes, patterns, item usage), make sure to **refer to relevant past clues** or interactions in the task history.\n
    - Avoid naive trial-and-error approaches. Intelligent reasoning based on memory, reflection, and context is expected.\n  
    - **Avoid repeating actions** that have already been tried and shown to be ineffective.\n  
    - This game involves **many variables** and may not always follow straightforward logic. It requires **lateral thinking** and a **creative mindset**.\n 
    Don’t just chase the end goal — instead, explore alternative possibilities using **common sense and creativity**.\n  
    - Your suggested action should be **fine-grained and appropriate to the current situation**.\n  
    → Start with **simple, clear interactions** that can be executed immediately on the current screen, rather than complex or abstract moves.\n\n

    *Note:* Just because an action was technically “successful” (e.g., opening an item or triggering a response) doesn’t mean it was helpful. Focus on what truly contributes to **advancing in the game**.\n

    “If you find yourself repeating the same action, try a different approach. Even a successful action might not help you solve the problem.”\n\n

    [Examples]\n
    - Click on the bookshelf to examine the books.\n  
    - Press the arrow to move to the next screen.\n  
    - Pick up the item lying on the floor.\n  
    - Close the popup window that's blocking the view.\n  
    - Open the drawer to check what's inside.\n  
    - Talk to the character standing nearby.\n  
    - Use the key from your inventory on the locked door.\n
    """

    # 4. Call API with all images
    response = api_caller(api_provider, system_prompt, model_name, prompt, base64_images=all_images)


    return response