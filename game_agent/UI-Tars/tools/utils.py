import os
import base64
import re

def encode_image(image_path):
    """
    Read a file from disk and return its contents as a base64-encoded string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
    
def encode_images_to_base64(image_paths):
    encoded = []
    for path in image_paths:
        try:
            with open(path, "rb") as f:
                encoded_str = base64.b64encode(f.read()).decode("utf-8")
                encoded.append(encoded_str)
        except Exception as e:
            print(f"[WARN] Failed to encode image {path}: {e}")
    return encoded

def extract_python_code(content):
    if not content:
        print("[ERROR] extract_python_code() received empty content")
        return "", ""

    print(f"[DEBUG] Raw content received:\n{content}\n")

    # 🔹 Extract only the Python code part that follows the "code" key
    match = re.search(r'"code"\s*:\s*"""\s*(.*?)\s*"""', content, re.DOTALL)
    action_match = re.search(r'"action":\s*"([^"]+)"', content)  # 🔹 Find the action value

    action_text = action_match.group(1) if action_match else ""  # 🔹 Extract only the string value

    if match:
        code_content = match.group(1)  # Get only the Python code part

        # 🔹 Remove comments (multi-line """ """ comments & single-line # comments)
        code_content = re.sub(r'""".*?"""', '', code_content, flags=re.DOTALL).strip()
        code_content = re.sub(r'^\s*#.*$', '', code_content, flags=re.MULTILINE).strip()

        print(f"[DEBUG] Extracted Code:\n{code_content}\n")
        print(f"[DEBUG] Extracted Action:\n{action_text}\n")  # 🔹 Print the action value
        return code_content, action_text

    print("[ERROR] No Python code found in content.")
    return "", action_text  # 🔹 Always return action_text as well

### Find if the screen changed after the action
# def extract_action_change(content):  # content = "reason: ... Success_Action: True"
#     if not content:
#         print("empty content")
#         return ""
    
#     print(f"[DEBUG] Raw content received:\n{content}\n")
    
#     # Find "Success_Action: True" or "Success_Action: False"
#     match = re.search(r"Success_Action:\s*(True|False)", content, re.IGNORECASE)
    
#     if match:
#         result_success = match.group(1).lower() == "true"  # Convert string to boolean
#         return result_success  # Return True or False

#     print("[WARNING] Success_Action not found in content.")
#     return ""


def extract_action_change(content: str) -> dict:
    """
    Extracts the success status and reason for an action from the GPT response.

    Args:
        content (str): GPT's response

    Returns:
        dict: {
            "success": True/False,
            "explanation": "Explanation of changes due to the action"
        }
    """
    if not content:
        print("⚠️ content is empty.")
        return {"success": False, "explanation": "No content"}

    print(f"[DEBUG] GPT response original text:\n{content}\n")

    # Extract success status
    match = re.search(r"Success_Action:\s*(True|False)", content, re.IGNORECASE)
    success = match.group(1).lower() == "true" if match else False

    # Extract explanation (sentence after Reason:)
    explanation_match = re.search(r"Reason:\s*(.+)", content, re.IGNORECASE | re.DOTALL)
    explanation = explanation_match.group(1).strip() if explanation_match else "No explanation of changes"

    return {
        "success": success,
        "explanation": explanation
    }