import time
import os
import sys
import argparse
from datetime import datetime
from collections import deque
from judge.vlm.tools.utils import encode_image, log_output, extract_python_code, extract_action_change
from judge.vlm.load_data import save_chat_log, load_game_prompt_eval
from judge.vlm.screenshot import capture_flash_screenshot
from judge.vlm.api_caller import api_caller


def generate_code(system_prompt, api_provider, model_name, os_interaction_prompt, base64_image):
    """ AI analyzes the game state and generates PyAutoGUI code """

    start_time = time.time()
    response = api_caller(api_provider, system_prompt, model_name, os_interaction_prompt, base64_image=base64_image)
    latency = time.time() - start_time
    print(f"[INFO] LLM for Generate Code Response Latency: {latency:.2f}s")
    
    clean_code, action = extract_python_code(response)   
     
    return clean_code, action

def check_action_success(api_provider, model_name, action, base64_before, base64_after):
    """ Function to check whether the executed action succeeded """

    comparison_system_prompt = f""" 
    You will compare two images caused by action.\n
    Your last action is {action}\n
    """
    
    comparison_prompt1 = """
    Compare the following two images and describe the differences resulting from the action:\n\n
    - Image 1: Before action\n
    - Image 2: After action\n

    ###Output Format###\n\n

    If changes are detected:\n
    Describe: [Describe the differences caused by the action]\n\n

    If no changes are observed:\n
    Describe: Not Changed.\n
    """

    # First, get the action change.
    action_change_response1 = api_caller(api_provider, comparison_system_prompt, model_name, comparison_prompt1, base64_before, base64_after)
    
    # Evaluate whether the obtained action change is appropriate for the result of our action.
    comparison_prompt2 = f"""    
    If an action change is detected at ‘action change response’, please verify whether {action_change_response1} has occurred appropriately. Explain the rationale behind its appropriateness and provide the result.\n
    If response is "Not Changed", set Success_Action to False; otherwise, set it to True.\n

    ###Output Format###\n\n:
    [Reason: Explanation of why this change is appropriate, Success_Action: True/False]
    """
    
    action_change_response2 = api_caller(api_provider, comparison_system_prompt, model_name, comparison_prompt2)
    change_result = extract_action_change(action_change_response2)

    print(f"[INFO] Screen Change Analysis Result: {change_result}")

    return change_result

def eval_success(api_provider, model_name, system_prompt, evaluation_prompt, base64_image, example_base64=None):
    start_time = time.time()
    
    if example_base64:
        # response includes an example image along with the current frame
        response = api_caller(api_provider, system_prompt, model_name, evaluation_prompt, example_base64, base64_image)
    else:
        response = api_caller(api_provider, system_prompt, model_name, evaluation_prompt, None, base64_image)
    
    latency = time.time() - start_time
    print(f"[INFO] LLM for Evaluation Response Latency: {latency:.2f}s")
    
    return response
        

def main(game, api_provider, model_name, loop_interval, system_prompt, evaluation_prompt, example_image_path):
    # parser = argparse.ArgumentParser(description="Flashpoint LLM AI Agent")
    # parser.add_argument("--game", type=str, required=True, help="Game name from JSON file")
    # parser.add_argument("--api_provider", type=str, default="openai", help="API provider to use")
    # parser.add_argument("--model_name", type=str, default="gpt-4-turbo", help="Model name")
    # parser.add_argument("--loop_interval", type=float, default=0.5, help="Time in seconds between moves")
    # args = parser.parse_args()
    
    print(f"Starting Flashpoint AI Agent for {game}...")
    
    # move_history = deque(maxlen=4)  # store the last 4 moves
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/{game}_log_{timestamp}.json"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Encode only if an example image exists
    example_base64 = encode_image(example_image_path) if example_image_path else None
    os_interaction_prompt = None
    if not os_interaction_prompt:
        before_screenshot = capture_flash_screenshot()
        base64_before = encode_image(before_screenshot)

        # If example_base64 exists, send it together; otherwise, do not.
        if example_base64:
            eval_result = eval_success(api_provider, model_name, system_prompt, evaluation_prompt, base64_before, example_base64)
        else:
            eval_result = eval_success(api_provider, model_name, system_prompt, evaluation_prompt, base64_before)

        print(f"[INFO] Evaluation Result: {eval_result}")
        return
    
    action_fail_count = 0  # failure count
    
    while True:
        try:
            # 1. Capture the current screen and encode
            before_screenshot = capture_flash_screenshot()
            base64_before = encode_image(before_screenshot)  
            
            # 2. Generate code and action
            code, action = generate_code(
                system_prompt, api_provider, model_name, os_interaction_prompt, base64_before
            )

            if not code:
                print("[WARNING] No valid action generated. Retrying...")
                action_fail_count += 1
            else:
                try:
                    exec(code)  # execute generated code
                    # move_history.append(code)
                    save_chat_log(
                        {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "prompt": os_interaction_prompt,
                            "action": action,
                            "code": code
                        },
                        log_file
                    )
                except Exception as e:
                    print(f"[ERROR] Code execution failed: {e}")
                    action_fail_count += 1
                    
            time.sleep(loop_interval)
            
            after_screenshot = capture_flash_screenshot()
            base64_after = encode_image(after_screenshot)  # ensure we return the captured image

            # 3. Check whether the action succeeded and obtain `base64_after`
            action_success = check_action_success(api_provider, model_name, action, base64_before, base64_after)
            
            if action_success:
                print("[INFO] Action succeeded, proceeding to next action.")
                action_fail_count = 0  # reset on success
            else:
                print("[WARNING] Action failed. Retrying with a new strategy...")
                action_fail_count += 1

            # 4. Prevent program termination on consecutive failures (can be improved later)
            if action_fail_count >= 3:
                print("[ERROR] Action failed 3 times. Attempting alternative approach...")
                action_fail_count = 0  # reset and try alternative approach
                
            time.sleep(loop_interval)

            # 5. Perform final evaluation (reuse `base64_after` in eval_success)
            if example_base64:
                eval_result = eval_success(api_provider, model_name, system_prompt, evaluation_prompt, base64_after, example_base64)
            else:
                eval_result = eval_success(api_provider, model_name, system_prompt, evaluation_prompt, base64_after)

            print(f"[INFO] Evaluation Result: {eval_result}")

        except KeyboardInterrupt:
            print("[INFO] User terminated the program.")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error occurred: {e}")
            break
      
# if __name__ == "__main__":
#     main()