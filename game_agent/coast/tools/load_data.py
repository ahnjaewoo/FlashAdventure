import json
import os
import yaml



def save_chat_log(entry, game_name, api_model, cua):
    """
    Saves game action logs to a JSON file.
    Path: json/{api_model}/{game_name}/{cua}/game_log.json
    """
    log_dir = os.path.join("json", cua, api_model, game_name, )
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"game_log_{game_name}.json")

    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(entry)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
        
def load_config(yaml_path):
    """
    Loads a YAML configuration file and returns it as a dictionary.
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
    

def load_action_prompt(json_path, moduler):
    """ Loads the prompt and action keys for a specific game from a JSON file """
    with open(json_path, "r", encoding="utf-8") as f:
        json_path = json.load(f)

    if moduler in json_path:
        g = json_path[moduler]
        return g["action_prompt"]
    else:
        raise ValueError(f"No prompt exists for game '{moduler}'.")


def load_game_prompt(json_path, game_name, type):
    """ Loads the prompt and action keys for a specific game from a JSON file """
    with open(json_path, "r", encoding="utf-8") as f:
        game_data = json.load(f)

    if game_name in game_data:
        g = game_data[game_name]
        
        if type in ("game_prompt", "system_prompt"):
            return g[type]
        else:
            raise ValueError(f"No {type} exists for game '{game_name}'.")

    else:
        raise ValueError(f"No prompt exists for game '{game_name}'.")


def load_memory(json_dir, type="episodic", n=None):
    """
    type: one of 'episodic', 'clue', 'task', 'reflection'
    n: (Optional) If it's a list, only the last n items are returned
    Returns:
        - List (optionally sliced) for episodic/reflection memory
        - Dict for clue/task memory
    """
    filename = f"{type}_memory.json"
    path = os.path.join(json_dir, filename)

    if not os.path.exists(path):
        return {} if type in ("task") else []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Slice the last n items (for list types only)
    if isinstance(data, list) and n is not None:
        return data[-n:]
    return data