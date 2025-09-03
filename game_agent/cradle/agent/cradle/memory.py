import json
import os
from datetime import datetime

DEFAULT_MEMORY_FILENAMES = {
    "task": "episodic_memory.json",
    "skill": "procedural_memory.json",
    "reflection": "reflection.json"
}

def resolve_path(memory_type, game_name=None, api_model=None, cua=None):
    """
    Returns the file path based on game name, model name, and cua.
    """
    if memory_type not in DEFAULT_MEMORY_FILENAMES:
        raise ValueError("Unsupported memory_type. Must be 'task', 'skill', or 'reflection'.")

    if not game_name:
        raise ValueError("You must provide game_name.")
    if not cua:
        raise ValueError("You must provide cua (e.g., gpt, claude, uground).")

    folder = os.path.join(f"./json/{cua}/{api_model}", game_name)
    os.makedirs(folder, exist_ok=True)

    return os.path.join(folder, DEFAULT_MEMORY_FILENAMES[memory_type])


def load_memory(memory_type="task", game_name=None, api_model=None, cua=None):
    """
    Loads memory data from file. If the file does not exist, creates it with default structure.
    """
    memory_path = resolve_path(memory_type, game_name, api_model, cua)

    if memory_type in ["task", "reflection"]:
        default_data = []
    elif memory_type == "skill":
        default_data = {}
    else:
        raise ValueError("Unsupported memory_type")

    if not os.path.exists(memory_path):
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

    with open(memory_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default_data


def save_memory(data, memory_type="task", game_name=None, api_model=None, cua=None):
    """
    Saves memory data to file.
    """
    memory_path = resolve_path(memory_type, game_name, api_model, cua)

    # Force list if accidentally passed a dict for task/reflection
    if isinstance(data, dict) and memory_type in ["task", "reflection"]:
        data = list(data.values())

    with open(memory_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def add_task_memory(task, result, game_name=None, api_model=None, cua=None):
    """
    Adds a new task and its result to the task memory.
    """
    memory = load_memory("task", game_name, api_model, cua)
    memory.append({
        "task": task,
        "result": result,
    })
    save_memory(memory, "task", game_name, api_model, cua)


def add_reflection_memory(task, result, game_name=None, api_model=None, cua=None):
    """
    Adds a new reflection entry to reflection memory.
    """
    memory = load_memory("reflection", game_name, api_model, cua)
    memory.append({
        "task": f"[Reflection] {task}",
        "result": result,
    })
    save_memory(memory, "reflection", game_name, api_model, cua)


def get_recent_tasks(n=10, game_name=None, api_model=None, cua=None):
    """
    Returns the most recent n task and reflection records.
    """
    memory = load_memory("task", game_name, api_model, cua)
    reflection = load_memory("reflection", game_name, api_model, cua)
    return memory[-n:], reflection[-n:]


def get_recent_image_paths(base_dir="./screenshots/", game_name=None, limit=10, extensions={'.png', '.jpg', '.jpeg'}):
    """
    Returns the most recently modified image files for the given game.
    """
    if not game_name:
        raise ValueError("game_name must be provided.")
    
    directory = os.path.join(base_dir, game_name)
    
    if not os.path.exists(directory):
        print(f"[INFO] No screenshot directory found for game: {game_name}")
        return []

    image_files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.splitext(f)[1].lower() in extensions
    ]

    image_files.sort(key=os.path.getmtime, reverse=True)
    return image_files[:limit]