import os
import base64
import re
import json

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
        print(f"[DEBUG] Extracted Action:\n{action_text}\n")
        return code_content, action_text

    print("[ERROR] No Python code found in content.")
    return "", action_text  # 🔹 Also return the action_text always


def extract_action_change(content: str) -> dict:
    """
    Extracts the success status of an action and the reason from the GPT response.

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

    # Extract explanation (the sentence after Reason:)
    explanation_match = re.search(r"Reason:\s*(.+)", content, re.IGNORECASE | re.DOTALL)
    explanation = explanation_match.group(1).strip() if explanation_match else "No explanation of changes"

    return {
        "success": success,
        "explanation": explanation
    }



def append_to_json_list(file_path, new_data):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(new_data)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_clues_from_text(text):
    """
    Extracts clues from JSON within <Respose>...</Respose>
    """
    match = re.search(r"<Respose>\s*(\{.*?\})\s*</Respose>", text, re.DOTALL)
    if not match:
        return []

    try:
        parsed = json.loads(match.group(1))
        return parsed.get("clues", [])
    except json.JSONDecodeError as e:
        print(f"[❌] JSON parsing failed: {e}")
        return []
    return [{"clue": c, "description": d, "location": l} for c, d, l in matches]


def extract_episodic_memory_from_text(text):
    """
    Extracts all episodic_memory from JSON blocks inside <Respose>...</Respose> tags.
    """
    blocks = re.findall(r"<Respose>\s*(\{.*?\})\s*</Respose>", text, re.DOTALL)
    episodic_memories = []

    for block in blocks:
        try:
            data = json.loads(block)
            episodic = data.get("episodic_memory", [])
            if isinstance(episodic, list):
                episodic_memories.extend(episodic)
        except json.JSONDecodeError as e:
            print(f"[❌] JSON parsing failed: {e}")

    return episodic_memories


def extract_response_json(messages):
    for msg in messages:
        if isinstance(msg, str):
            match = re.search(r"<Respose>\s*(\{.*?\})\s*</Respose>", msg, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    print("[❌] JSON parsing failed")
    return {}


def extract_json_block_from_response(text):
    match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"[❌] JSON parsing failed: {e}")
        return None