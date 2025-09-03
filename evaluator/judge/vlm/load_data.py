import json
import os 

def save_chat_log(entry, LOG_FILE):
    """ Save game move log to a JSON file """
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

    
def load_game_prompt_eval(game_name, image_num = 1):
    json_path = "./milestone_prompts.json"
    """ Load prompt and control keys for a specific game from JSON """
    with open(json_path, "r") as f:
        game_data = json.load(f)

    if game_name in game_data:
        prompt = game_data[game_name].get("prompt")
        eval_prompt = game_data[game_name].get("evaluation_prompt")
        example_image_path = game_data[game_name].get(f"example_image_path{image_num}", None)

        return prompt, eval_prompt, example_image_path
    else:
        raise ValueError(f"No prompt found for game '{game_name}'.")