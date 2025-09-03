import time
from api import api_caller
from tools import capture_flash_screenshot, encode_image, extract_action_change
from agent.cradle.memory import get_recent_tasks


def self_reflect(previous_action, system_prompt, api_provider, model_name, game_name, cua, action_success=None):
    """
    Evaluates whether the previous action was appropriate based on the current screen and past behavior history.
    """
    # Capture current screen (after action)
    screenshot_path = capture_flash_screenshot(game_name=game_name, cua=cua, model_name=model_name, time="after")
    current_screen = encode_image(screenshot_path)

    # Load recent task history
    recent_memory, _ = get_recent_tasks(n=10, game_name=game_name, api_model=model_name, cua=cua)
    memory_text = "\n".join(
        [f"- {m['task']} → {m['result']}" for m in recent_memory]
    )

    # Add success info
    success_text = f"\n[Previous Action Success] {'Succeeded ✅' if action_success else 'Failed ❌'}" if action_success is not None else ""

    # Prompt
    prompt = f"""
    [Recent Task History]\n

    {memory_text}\n\n

    [Previous Action]\n
    {previous_action}\n\n

    [Current Screen]\n
    [Image]\n\n

    {success_text}\n\n


    [Important]\n
    Based on the above information, assess whether the previous action was strategically appropriate:\n

    - Consider the flow and sequence of previous actions.\n
    - If the screen hasn't changed, it may indicate a misclick or that some conditions were not met.\n
    - Check if the same mistake is being repeated.\n
    - Don’t just evaluate whether the action moved you toward the ultimate goal — consider whether a more **basic yet necessary interaction** was actually required.\n
    - If applicable, suggest a more realistic or context-appropriate alternative.\n\n

    [Examples]\n
    - "The action didn’t change the screen. A message window was likely still open. I should have closed it first."\n
    - "I used the same item again, even though it failed previously. I should try a different object or explore another path."\n
    - "I tried to interact with a locked drawer, but I haven't found the key yet. I should look around before retrying."\n
    - "I skipped reading a note that might contain clues. That could’ve helped me solve the puzzle more efficiently."\n
    """

    response = api_caller(api_provider, system_prompt, model_name, prompt, current_screen)
    return response


def check_action_success(api_provider, game_name, model_name, action, base64_before, cua):
    """
    행동 전후의 화면을 비교하여 행동이 성공적으로 수행되었는지 판단합니다.
    변화가 없다면 실패로 간주합니다.
    """
    time.sleep(1)  
    after_screenshot = capture_flash_screenshot(game_name=game_name, cua=cua, model_name=model_name, time="after")
    base64_after = encode_image(after_screenshot)

    comparison_system_prompt = f""" 
    You will compare two images caused by an action.
    Last action: {action}
    """

    comparison_prompt1 = """
    Compare the following two images and describe the differences caused by the action:\n

    - Image 1: Before action\n
    - Image 2: After action\n\n

    ### Output Format ###\n

    If changes are detected:\n
    Describe: [Describe the differences caused by the action]\n

    If no changes are observed:\n
    Describe: Not Changed.\n
    """

    # 1. detect change
    action_change_response1 = api_caller(
        api_provider,
        comparison_system_prompt,
        model_name,
        comparison_prompt1,
        [base64_before, base64_after]
    )

    # 2. evaluate change
    comparison_prompt2 = f"""    
    Evaluate whether the following change is appropriate based on the action '{action}'.\n

    Action Change Response:\n
    {action_change_response1}

    If response is "Not Changed", set Success_Action to False; otherwise, set it to True.\n\n

    ### Output Format ###\n

    [Reason: Explanation of why this change is appropriate or not, Success_Action: True/False]\n\n
    """

    action_change_response2 = api_caller(
        api_provider,
        comparison_system_prompt,
        model_name,
        comparison_prompt2
    )

    change_result = extract_action_change(action_change_response2)
    print(f"[INFO] Screen Change Analysis Result: {change_result}")
    return change_result