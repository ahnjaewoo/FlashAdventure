import importlib.util
import asyncio
import os

AVAILABLE_EVALS = {
    "sherlock": "eval_sherlock",
    "sherlock2": "eval_sherlock2",
    "small town detective": "eval_smalltown",
    "nick bounty a case of the crabs": "eval_nickbounty",
    "gamecafe": "eval_gamecafe",
    "paint room escape": "eval_paint",
    "video studio escape": "eval_videostudio",
    "vortex1": "eval_vortex",
    "vortex2": "eval_vortex2",
    "vortex3": "eval_vortex3",
    "pierre": "eval_pierre",
    "dakota": "eval_dakota",
    "saucy": "eval_saucy",
    "ray and cooper2": "eval_ray2",
    "design house escape": "eval_design",
    "mirror room escape": "eval_mirror",
    "pico sim date": "eval_pico",
    "festival days sim date": "eval_festival",
    "kingdom days": "eval_kingdom",
    "idol days sim date": "eval_idol",
    "community college sim": "eval_college",
    "grim tales the bride": "eval_grim1",
    "grim tales the legacy collectors edition": "eval_grim2",
    "chemical room escape": "eval_chemical",
    "computer office escape": "eval_computer",
    "crimson room": "eval_crimson",
    "geometric room escape": "eval_geometric",
    "machine room escape": "eval_machine",
    "sort the court": "eval_sort",
    "space museum escape": "eval_space",
    "camping room escape" : "eval_camping",
    "vending machine room escape": "eval_vending",
    "wood workshop escape": "eval_wood",
    "elevator room escape" : "eval_elevator"
}

def choose_game():
    print("Available evaluations:")
    for i, name in enumerate(AVAILABLE_EVALS, 1):
        print(f"{i}. {name}")
    idx = int(input("Select game to evaluate: ")) - 1
    return list(AVAILABLE_EVALS.values())[idx]

async def main():
    module_path = "./eval_game" 
    module_name = choose_game()
    file_path = os.path.join(module_path, f"{module_name}.py")  

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func_name = f"eval_{module_name.split('_')[-1]}"
    await module.__dict__[func_name]()

if __name__ == "__main__":
    asyncio.run(main())