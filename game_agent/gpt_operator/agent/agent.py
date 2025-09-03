from computers import Computer
from utils import (
    create_response,
    show_image,
    pp,
    sanitize_message,
    check_blocklisted_url,
)
import json
from typing import Callable, List, Dict, Any
import os
import time
import base64
import datetime
from io import BytesIO
from PIL import Image
import re


class Agent:
    def __init__(
        self,
        model="computer-use-preview",
        computer: Computer = None,
        tools: list[dict] = [],
        acknowledge_safety_check_callback: Callable = lambda: False,
        save_screenshots=True,
        screenshots_folder="screenshots",
        gpt_log_enabled=True,
        gpt_log_folder="gpt_logs"
    ):
        self.model = model
        self.computer = computer
        self.tools = tools
        self.print_steps = True
        self.debug = False
        self.show_images = False
        self.acknowledge_safety_check_callback = acknowledge_safety_check_callback
        self.save_screenshots = save_screenshots
        self.screenshots_folder = screenshots_folder
        self.gpt_log_enabled = gpt_log_enabled
        self.gpt_log_folder = gpt_log_folder
        self.gpt_log_file = None

        if self.save_screenshots and not os.path.exists(self.screenshots_folder):
            os.makedirs(self.screenshots_folder)

        if self.gpt_log_enabled and not os.path.exists(self.gpt_log_folder):
            os.makedirs(self.gpt_log_folder)

        if self.gpt_log_enabled:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.gpt_log_file = f"{self.gpt_log_folder}/gpt_responses_{timestamp}.txt"
            with open(self.gpt_log_file, "w", encoding="utf-8") as f:
                f.write(f"=== GPT Response Log - Start Time: {datetime.datetime.now()} ===\n\n")
            print(f"📝 GPT response log file created: {self.gpt_log_file}")

        if computer:
            self.tools += [
                {
                    "type": "computer-preview",
                    "display_width": computer.dimensions[0],
                    "display_height": computer.dimensions[1],
                    "environment": computer.environment,
                },
            ]

    def debug_print(self, *args):
        if self.debug:
            pp(*args)

    def save_screenshot(self, screenshot_base64):
        try:
            timestamp = int(time.time())
            filename = f"{self.screenshots_folder}/screenshot_{timestamp}.png"
            img_data = base64.b64decode(screenshot_base64)
            with open(filename, "wb") as f:
                f.write(img_data)
            print(f"📸 Screenshot saved: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error while saving screenshot: {str(e)}")
            return None

    def _truncate_base64_image(self, json_str):
        def replace_base64(match):
            prefix = match.group(1)
            base64_data = match.group(2)
            return f'{prefix}[length: {len(base64_data)} bytes]'
        pattern = r'("data:image\/[^;]+;base64,)([A-Za-z0-9+/=]+)'
        return re.sub(pattern, replace_base64, json_str)

    def log_gpt_response(self, response, input_items=None):
        if not self.gpt_log_enabled or not self.gpt_log_file:
            return
        try:
            with open(self.gpt_log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n\n{'='*50}\n")
                f.write(f"===== Timestamp: {timestamp} =====\n")
                f.write(f"{'='*50}\n\n")
                if input_items:
                    f.write(f"----- All input items (Total {len(input_items)}) -----\n")
                    for i, item in enumerate(input_items):
                        f.write(f"\n[Input item {i+1}]\n")
                        try:
                            json_str = json.dumps(item, indent=2, ensure_ascii=False)
                            truncated_json = self._truncate_base64_image(json_str)
                            f.write(truncated_json)
                        except Exception as e:
                            f.write(f"JSON serialization error: {str(e)}")
                        f.write("\n")
                    total_size = sum(len(json.dumps(item)) for item in input_items)
                    f.write(f"\n----- History size analysis -----\n")
                    f.write(f"Total input data size: approx. {total_size / 1024:.2f} KB\n")
                    user_messages = [i for i, item in enumerate(input_items) if item.get("role") == "user"]
                    if user_messages:
                        f.write(f"Number of user messages: {len(user_messages)} (= number of conversation turns)\n")
                        f.write(f"User message positions: {user_messages}\n")
                f.write(f"\n----- Full response JSON -----\n")
                try:
                    json_str = json.dumps(response, indent=2, ensure_ascii=False)
                    truncated_json = self._truncate_base64_image(json_str)
                    f.write(truncated_json)
                except Exception as e:
                    f.write(f"JSON serialization error: {str(e)}")
                if "output" in response:
                    text_outputs = []
                    for item in response["output"]:
                        if item["type"] == "message" and "content" in item:
                            for content in item["content"]:
                                if content.get("type") == "text":
                                    text_outputs.append(content.get("text", ""))
                    if text_outputs:
                        f.write("\n\n----- Text output -----\n")
                        for i, text in enumerate(text_outputs):
                            f.write(f"[{i+1}] {text}\n")
                if "output" in response:
                    actions = []
                    for item in response["output"]:
                        if item["type"] == "computer_call":
                            actions.append(item["action"])
                    if actions:
                        f.write("\n\n----- Action list -----\n")
                        for i, action in enumerate(actions):
                            f.write(f"[{i+1}] {json.dumps(action, ensure_ascii=False)}\n")
                f.write("\n\n----- Token usage -----\n")
                if "usage" in response:
                    usage = response["usage"]
                    f.write(f"Input tokens: {usage.get('input_tokens', '?')}\n")
                    f.write(f"Output tokens: {usage.get('output_tokens', '?')}\n")
                    f.write(f"Total tokens: {usage.get('total_tokens', '?')}\n")
                else:
                    f.write("No token information\n")
                f.write("\n" + "="*50 + "\n")
        except Exception as e:
            print(f"❌ Error while logging GPT response: {str(e)}")

    def handle_item(self, item):
        if item["type"] == "message":
            if self.print_steps:
                if "content" in item and len(item["content"]) > 0 and "text" in item["content"][0]:
                    print("📝 Output message::", item["content"][0]["text"])
                else:
                    print("📝 Output message:: [No content]")
            return []

        if item["type"] == "function_call":
            name, args = item["name"], json.loads(item["arguments"])
            if self.print_steps:
                print(f"{name}({args})")
            if hasattr(self.computer, name):
                method = getattr(self.computer, name)
                method(**args)
            return [
                {
                    "type": "function_call_output",
                    "call_id": item["call_id"],
                    "output": "success",
                }
            ]

        if item["type"] == "computer_call":
            action = item["action"]
            action_type = action["type"]
            action_args = {k: v for k, v in action.items() if k != "type"}
            if self.print_steps:
                print(f"{action_type}({action_args})")
            method = getattr(self.computer, action_type)
            method(**action_args)
            screenshot_base64 = self.computer.screenshot()
            if self.save_screenshots:
                screenshot_path = self.save_screenshot(screenshot_base64)
            if self.show_images:
                show_image(screenshot_base64)
            pending_checks = item.get("pending_safety_checks", [])
            for check in pending_checks:
                message = check["message"]
                if not self.acknowledge_safety_check_callback(message):
                    raise ValueError(f"Safety check failed: {message}. Cannot continue with unacknowledged safety checks.")
            call_output = {
                "type": "computer_call_output",
                "call_id": item["call_id"],
                "acknowledged_safety_checks": pending_checks,
                "output": {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screenshot_base64}",
                },
            }
            if self.computer.environment == "browser":
                current_url = self.computer.get_current_url()
                check_blocklisted_url(current_url)
                call_output["output"]["current_url"] = current_url
            return [call_output]

        if self.print_steps:
            print(f"📝 Other response:: {item['type']} type response (content omitted)")
        return []

    def run_full_turn(self, input_items, print_steps=True, debug=False, show_images=False):
        self.print_steps = print_steps
        self.debug = debug
        self.show_images = show_images

        for item in input_items:
            if item.get("role") == "user" and "content" in item:
                for content in item.get("content", []):
                    if content.get("type") == "input_text":
                        text = content.get("text", "")
                        first_line = text.split('\n')[0]
                        print(f"📝 Input message: {first_line[:100]}" if len(first_line) > 100 else f"📝 Input message: {first_line}")
                        break

        input_size = sum(len(json.dumps(item)) for item in input_items)
        print(f"🔄 Request data size: approx. {input_size / 1024:.2f} KB")

        max_retries = 1
        for attempt in range(max_retries):
            try:
                response = create_response(
                    model=self.model,
                    input=input_items,
                    tools=self.tools,
                    truncation="auto",
                )

                if self.gpt_log_enabled:
                    self.log_gpt_response(response, input_items)

                if "usage" in response:
                    usage = response["usage"]
                    print(f"🧮 Token usage → Input: {usage.get('input_tokens', '?')} / Output: {usage.get('output_tokens', '?')} / Total: {usage.get('total_tokens', '?')}")

                if "output" not in response:
                    print("❌ Model response has no 'output' field.")
                    return []

                output_items = response["output"]
                if not output_items:
                    print("📝 Output message:: [No response]")
                    return []

                new_items = []
                has_message = False
                for item in output_items:
                    new_items.append(item)
                    if item["type"] == "message":
                        has_message = True
                    new_items += self.handle_item(item)

                if not has_message and self.print_steps:
                    print("📝 Output message:: [No text response, only performing action]")

                return new_items

            except Exception as e:
                print(f"❌ Error occurred: {str(e)}. Retrying... ({attempt + 1}/{max_retries})")
                if self.gpt_log_enabled and self.gpt_log_file:
                    try:
                        with open(self.gpt_log_file, "a", encoding="utf-8") as f:
                            f.write(f"\n[Error occurred] {str(e)}\n")
                    except:
                        pass
                time.sleep(1)

        print("❌ Failed even after repeated attempts.")
        return []