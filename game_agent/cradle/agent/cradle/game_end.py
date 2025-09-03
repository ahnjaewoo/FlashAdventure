from api import api_caller

def game_end(system_prompt, screen, api_provider, model_name):
    prompt = f"""
    Current Screen:\n
    [Image]\n\n

    Please check whether the current screen indicates that the game has been completely and successfully cleared.\n
    If successful, the player either escapes the room or sees a message indicating the game has been completed.\n
    If it has, output [Done].\n
    """
    
    response = api_caller(api_provider, system_prompt, model_name, prompt, screen)
    
    return response