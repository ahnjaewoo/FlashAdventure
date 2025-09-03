# simple_cua_loop.py or gpt_cua/runner.py
from gpt_cua.computers import LocalDesktopComputer
from gpt_cua.utils import create_response, check_blocklisted_url

def acknowledge_safety_check_callback(message: str) -> bool:
    response = input(f"Safety Check Warning: {message}\nProceed? (y/n): ").lower()
    return response.strip() == "y"

def handle_item(item, computer: LocalDesktopComputer):
    if item["type"] == "message":
        print(item["content"][0]["text"])

    if item["type"] == "computer_call":
        action = item["action"]
        action_type = action["type"]
        action_args = {k: v for k, v in action.items() if k != "type"}
        print(f"🖱️ {action_type}({action_args})")

        getattr(computer, action_type)(**action_args)

        print(f"🎯 액션 카운트: {computer.action_count}/{computer.max_actions}")

        screenshot_base64 = computer.screenshot()

        checks = item.get("pending_safety_checks", [])
        for check in checks:
            if not acknowledge_safety_check_callback(check["message"]):
                raise ValueError(f"Safety check failed: {check['message']}")

        output = {
            "type": "computer_call_output",
            "call_id": item["call_id"],
            "acknowledged_safety_checks": checks,
            "output": {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}",
            },
        }

        if computer.environment == "browser":
            current_url = computer.get_current_url()
            output["output"]["current_url"] = current_url
            check_blocklisted_url(current_url)

        return [output]

    return []

import time

def main_gpt_cua(prompt_text=None, max_retries=300):
    computer = LocalDesktopComputer(max_actions=300)
    tools = [{
        "type": "computer-preview",
        "display_width": computer.dimensions[0],
        "display_height": computer.dimensions[1],
        "environment": computer.environment,
    }]

    items = []
    if prompt_text:
        items.append({"role": "user", "content": prompt_text})
    else:
        user_input = input("> ")
        items.append({"role": "user", "content": user_input})

    while True:
        for attempt in range(max_retries):
            response = create_response(
                model="computer-use-preview",
                input=items,
                tools=tools,
                truncation="auto",
            )

            if "output" in response:
                break  # 성공했으면 루프 탈출
            else:
                print(f"[Retry {attempt+1}/{max_retries}] No output from model. Retrying...")
                time.sleep(1)  # 잠깐 대기 후 재시도

        else:
            # max_retries번 모두 실패한 경우
            raise ValueError("No output from model after multiple retries")

        items += response["output"]

        for item in response["output"]:
            items += handle_item(item, computer)

        if items[-1].get("role") == "assistant":
            break

    return computer.action_count