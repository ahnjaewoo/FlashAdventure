from judge.vlm import main as evaluator_none_cua
from judge.vlm import load_game_prompt_eval


## Configuration Dictionary


config = {
    "game": "Crimson Room",
    "api_provider": "anthropic", 
    "model_name": "claude-3-7-sonnet-20250219",
    "loop_interval": 3
}

system_prompt, evaluation_prompt, example_image_path = load_game_prompt_eval(config["game"])

    
config["system_prompt"] = system_prompt
config["evaluation_prompt"] = evaluation_prompt
config["example_image_path"] = example_image_path


## Running 
evaluator_none_cua(**config)


