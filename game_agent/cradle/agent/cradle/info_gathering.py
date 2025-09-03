from api import api_caller
 
def info_gather(system_prompt, api_provider, model_name, before_encoded):
    """
    현재 화면을 캡처하고 AI로 분석하여 화면 정보를 수집합니다.
    capture this screen and gather information
    """
    
    
    prompt = """
    The following image is a screenshot of the current computer screen.\n
    Carefully observe the screen and identify all **key visual elements**, such as:\n\n

    - Visible text (e.g., labels, instructions, titles, tooltips)\n
    - Interactive elements (e.g., buttons, icons, menus, input fields, sliders)\n
    - Status indicators or feedback messages\n
    - Any notable layout structures or visual groupings\n\n

    Objectives:\n
    1. **Summarize** the most important information presented on the screen.\n
    - What is the screen showing? What appears to be the current context or purpose?\n
    - Is there any indication of user progress, task status, or instructions?\n

    2. **List all possible user actions** based on what's visible.\n
    - Describe the actions in a clear and specific way (e.g., “Click the ‘Submit’ button”, “Type text into the search field”).\n
    - Include both obvious and subtle affordances, such as hovering, scrolling, or expanding menus.\n\n

    Be as detailed and comprehensive as possible. Your analysis should help another agent understand what this screen is about and what can be done on it.\n
    """
    
    
    # API caller
    response = api_caller(api_provider, system_prompt, model_name, prompt, before_encoded)
    
    return response


if __name__ == "__main__":
    result = info_gather()
    print(result)