import json
import re
from datetime import datetime
from api import api_caller
from agent.cradle.memory import load_memory, save_memory


def parse_gpt_skill_match_response(response_text: str, fallback_result: str) -> dict:
    """
    Manually parses a text response from GPT and returns it in JSON format
    """
    print("🔍 GPT response original text:\n", response_text)

    match_found = re.search(r'"match_found"\s*:\s*(true|false)', response_text, re.IGNORECASE)
    matched_trigger = re.search(r'"matched_trigger"\s*:\s*"(.+?)"', response_text)
    decision = re.search(r'"decision"\s*:\s*"(.+?)"', response_text)
    reason = re.search(r'"reason"\s*:\s*"(.+?)"', response_text, re.DOTALL)
    final_result = re.search(r'"final_result"\s*:\s*"(.+?)"', response_text, re.DOTALL)

    return {
        "match_found": match_found.group(1).lower() == "true" if match_found else False,
        "matched_trigger": matched_trigger.group(1) if matched_trigger else None,
        "decision": decision.group(1).strip() if decision else "add_new",
        "reason": reason.group(1).strip() if reason else "No reason provided.",
        "final_result": final_result.group(1).strip() if final_result else fallback_result
    }


def ask_gpt_for_skill_matching(trigger, new_result, existing_skills, api_provider, system_prompt, model_name):
    """
    Requests GPT to determine if a new skill is similar to any existing ones
    """
    prompt = f"""
    You're managing a memory of in-game actions (skills).\n\n

    A new skill is observed:\n
    - Trigger: {trigger}\n
    - Result: {new_result}\n\n

    Here are the current stored skills:\n
    {json.dumps(existing_skills, indent=2, ensure_ascii=False)}\n

    Determine if this new skill is similar to any existing ones.\n\n

    Return a JSON in this format:\n
    {{
    "match_found": true | false,
    "matched_trigger": "existing_trigger" | null,
    "decision": "keep_old" | "update_result" | "add_new",
    "reason": "...",
    "final_result": "..."
    }}
    """

    response = api_caller(api_provider, system_prompt, model_name, prompt)
    return parse_gpt_skill_match_response(response, fallback_result=new_result)


def update_or_add_verified_skill(trigger, new_result, system_prompt, game_name, api_provider, model_name, cua):
    """
    Compares new skill with existing memory and then updates or adds it
    """
    skills = load_memory(memory_type="skill", game_name=game_name, api_model=model_name, cua=cua)
    if not isinstance(skills, list):
        print("⚠️ skill memory is not a list → Initializing")
        skills = []

    gpt_result = ask_gpt_for_skill_matching(
        trigger=trigger,
        new_result=new_result,
        existing_skills=skills,
        api_provider=api_provider,
        system_prompt=system_prompt,
        model_name=model_name
    )

    print(f"🤖 GPT judgment result: {gpt_result}")

    if gpt_result["match_found"]:
        for skill in skills:
            if skill["trigger"] == gpt_result["matched_trigger"]:
                if gpt_result["decision"] == "update_result":
                    skill["result"] = gpt_result["final_result"]
                    print(f"🔁 Updating existing skill result: {skill['trigger']}")
                else:
                    print(f"📌 Keeping existing skill: {skill['trigger']}")
                break
    else:
        skills.append({
            "trigger": trigger,
            "result": gpt_result["final_result"],
            "timestamp": datetime.now().isoformat()
        })
        print(f"🆕 New skill added: {trigger}")

    save_memory(skills, memory_type="skill", game_name=game_name, api_model=model_name, cua=cua)
    print(f"✅ Skill saved successfully: {trigger}")