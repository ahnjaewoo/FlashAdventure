import json
import os


def save_chat_log(entry, game_name, api_model, cua):
    """
    Save game action logs to a JSON file.
    Path: json/{api_model}/{game_name}/{cua}/game_log.json
    """
    log_dir = os.path.join("json", api_model, game_name, cua)
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "game_log.json")

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


def load_game_prompt(game_name):
    """ Load the prompt and control keys for a specific game from JSON """
    json_path = "./json/game_prompts.json"
    with open(json_path, "r", encoding="utf-8") as f:
        game_data = json.load(f)

    if game_name in game_data:
        g = game_data[game_name]
        return g["prompt"]
    else:
        raise ValueError(f"No prompt found for game '{game_name}'.")


def load_system_prompt(game_name):
    """ Load the system prompt for a specific game from JSON """
    json_path = "./json/game_prompts.json"
    with open(json_path, "r", encoding="utf-8") as f:
        game_data = json.load(f)

    if game_name in game_data:
        g = game_data[game_name]
        return g["system_prompt"]
    else:
        raise ValueError(f"No system prompt found for game '{game_name}'.")


def load_memory_prompt(game_name, memory_type="task", path_map=None):
    """
    Load memory files from JSON depending on the memory type.
    memory_type: "task" | "skill"
    path_map: optional dict to customize paths
    """
    default_paths = {
        "task": f"./{game_name}/task_memory.json",
        "skill": f"./{game_name}/skills.json"
    }

    if path_map:
        default_paths.update(path_map)
    if memory_type not in default_paths:
        raise ValueError("memory_type must be either 'task' or 'skill'.")

    json_path = default_paths[memory_type]

    if not os.path.exists(json_path):
        return {} if memory_type == "skill" else []
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)