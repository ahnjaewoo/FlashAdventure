import os
import json
from datetime import datetime
import asyncio

from agent.cradle.skill_curation import update_or_add_verified_skill
from agent.cradle.action_planning import plan_actions
from agent.cradle.info_gathering import info_gather
from agent.cradle.self_reflection import check_action_success, self_reflect
from agent.cradle.game_end import game_end
from agent.cradle.memory import add_task_memory, add_reflection_memory
from tools import load_game_prompt, load_system_prompt, capture_flash_screenshot, encode_image
from gpt_cua import main_gpt_cua
from claude_cua import run_agent as main_claude_cua
from gui_grounding import agent_step as main_uground
from gui_grounding import run_claude_gui_agent as main_claude


def save_chat_log(log, game_name, api_model, cua):
    """
    Accumulatively saves logs to a single JSON file.
    Path: logs/{game_name}/{cua}/{api_model}/game_log.json
    """
    dir_path = os.path.join("logs", game_name, cua, api_model)
    os.makedirs(dir_path, exist_ok=True)

    log_path = os.path.join(dir_path, "game_log.json")

    # Load existing logs
    logs = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    # Add new log
    logs.append(log)

    # Save everything again
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def run_game_agent(api_provider, model_name, game_name, cua, max_actions=100):
    print(f"🎮 Game execution requested: {game_name}")
    total_actions = 0
    success_count = 0
    game_done_response = {"done": False}

    try:
        while total_actions < max_actions:
            # 0. Load game prompt
            try:
                system_prompt = load_system_prompt(game_name)
                print(f"\n'{game_name}' system prompt loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load system prompt: {e}")
                break

            # 1. Gather current screen information
            print("\n📸 Capturing screen before action...")
            screenshot_path = capture_flash_screenshot(game_name=game_name, cua=cua, model_name=model_name)
            print(screenshot_path)
            before_encoded = encode_image(screenshot_path)

            # 2. Task Inference
            env_summary = info_gather(system_prompt, api_provider, model_name, before_encoded)
            print(env_summary)

            # 3. Plan actions
            planned = plan_actions(system_prompt, env_summary, before_encoded, api_provider, model_name, game_name, cua)
            print("\n📝 Best Action:\n", planned)

            # 4. Execute action
            prompt_text = f"""
            You are a GUI agent controlling the mouse and keyboard.

            Your goal is to achieve the following task in the Flash game:
            [Goal]: {planned}

            Use visible elements on the screen such as buttons, panels, or objects to perform the action. Do not explain—just act.

            Perform only one single action.

            If the action you perform does **not cause any visible change** on the screen (e.g., no transition, movement, or popup), assume it was an invalid or non-interactive action. Do not repeat the same action again.

            If nothing is clickable or interactive, respond with "[Skip]".

            If your action causes any visible change on the screen, such as a scene transition, a popup appearing, or an object moving, STOP immediately and do not perform any further actions.

            If repeated attempts result in **no visible change**, consider the task unachievable and STOP trying further actions.
            """

            used_actions = 0
            if cua == "gpt":
                used_actions = main_gpt_cua(prompt_text=prompt_text)

            elif cua == "claude":
                used_actions = asyncio.run(main_claude_cua(initial_prompt=prompt_text))

            elif cua == "uground":
                used_actions = asyncio.run(main_uground(
                    user_description=prompt_text,
                    encoded_image=before_encoded,
                    provider=api_provider,
                    model=model_name
                ))

            elif cua == "sonnet":
                used_actions = asyncio.run(main_claude(
                    description=prompt_text,
                    encoded_image=before_encoded
                ))

            total_actions += used_actions
            print(f"🎮 Actions this turn: {used_actions}, cumulative: {total_actions}/{max_actions}")

            # 5. Judge success
            success_result = check_action_success(
                api_provider=api_provider,
                game_name=game_name,
                model_name=model_name,
                action=planned,
                base64_before=before_encoded,
                cua=cua
            )
            success_flag = success_result["success"]
            if success_flag:
                success_count += 1

            # 6. Record memory
            print("🧠 Saving Episodic memory...")
            add_task_memory(
                task=planned,
                result=success_result,
                game_name=game_name,
                api_model=model_name,
                cua=cua
            )

            # 7. Save skill if successful
            if success_flag:
                update_or_add_verified_skill(
                    trigger=planned,
                    new_result=success_result["explanation"],
                    system_prompt=system_prompt,
                    game_name=game_name,
                    api_provider=api_provider,
                    model_name=model_name,
                    cua=cua
                )
                print("🏆 Skill updated after success")

            # 8. Record reflection and evaluation
            reflection = self_reflect(
                previous_action=planned,
                system_prompt=system_prompt,
                api_provider=api_provider,
                model_name=model_name,
                game_name=game_name,
                cua=cua,
                action_success=success_flag
            )
            print("\n🪞 Self-evaluation result:\n", reflection)

            print("📘 Saving Reflection memory...")
            add_reflection_memory(
                task=planned,
                result=reflection,
                game_name=game_name,
                api_model=model_name,
                cua=cua
            )

            print("\n✅ Task complete and logs saved.")

            # 9. Judge game end
            final_path = capture_flash_screenshot(game_name=game_name, cua=cua, model_name=model_name, time="final")
            game_done_response = game_end(system_prompt, encode_image(final_path), api_provider, model_name)

            # 10. Save log
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "game": game_name,
                "turn": total_actions,
                "success_count": success_count,
                "user_prompt": system_prompt,
                "planned_action": planned,
                "reflection": reflection,
                "done_check": game_done_response
            }
            save_chat_log(log_entry, game_name=game_name, api_model=model_name, cua=cua)

    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user.")
    except Exception as e:
        print(f"\n❌ Interrupted due to exception: {e}")
    finally:
        print(f"\n🎯 Game over - Total attempts {total_actions} / Successes {success_count}")
        return {
            "game": game_name,
            "done": game_done_response,
            "action_count": total_actions,
            "success_count": success_count
        }