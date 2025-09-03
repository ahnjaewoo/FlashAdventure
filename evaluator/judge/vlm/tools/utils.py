import os
import base64
import re

def encode_image(image_path):
    """
    Read a file from disk and return its contents as a base64-encoded string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def log_output(thread_id, log_text, game):
    """
    Logs output to `cache/thread_{thread_id}/output.log`
    """
    thread_folder = f"cache/{game}/thread_{thread_id}"
    os.makedirs(thread_folder, exist_ok=True)
    
    log_path = os.path.join(thread_folder, "output.log")
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(log_text + "\n\n")

def extract_python_code(content):
    if not content:
        print("[ERROR] extract_python_code() received empty content")
        return "", ""

    print(f"[DEBUG] Raw content received:\n{content}\n")

    # 🔹 "code" 키 다음에 나오는 Python 코드 부분만 추출
    match = re.search(r'"code"\s*:\s*"""\s*(.*?)\s*"""', content, re.DOTALL)
    action_match = re.search(r'"action":\s*"([^"]+)"', content)  # 🔹 action 값 찾기

    action_text = action_match.group(1) if action_match else ""  # 🔹 문자열 값만 추출

    if match:
        code_content = match.group(1)  # Python 코드 부분만 가져오기

        # 🔹 주석 제거 (멀티라인 """ """ 주석 & 단일 줄 # 주석)
        code_content = re.sub(r'""".*?"""', '', code_content, flags=re.DOTALL).strip()
        code_content = re.sub(r'^\s*#.*$', '', code_content, flags=re.MULTILINE).strip()

        print(f"[DEBUG] Extracted Code:\n{code_content}\n")
        print(f"[DEBUG] Extracted Action:\n{action_text}\n")  # 🔹 action 값 출력
        return code_content, action_text

    print("[ERROR] No Python code found in content.")
    return "", action_text  # 🔹 항상 action_text도 반환

### action 후에 화면 변화했는지 찾기
def extract_action_change(content):  # content = "reason: ... Success_Action: True"
    if not content:
        print("empty content")
        return ""
    
    print(f"[DEBUG] Raw content received:\n{content}\n")
    
    # "Success_Action: True" 또는 "Success_Action: False" 찾기
    match = re.search(r"Success_Action:\s*(True|False)", content, re.IGNORECASE)
    
    if match:
        result_success = match.group(1).lower() == "true"  # 문자열을 boolean으로 변환
        return result_success  # True 또는 False 반환

    print("[WARNING] Success_Action not found in content.")
    return ""
