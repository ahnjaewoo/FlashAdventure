from judge.vlm.tools.serving.api_providers import anthropic_completion, openai_completion, gemini_completion
 
def api_caller(api_provider, system_prompt, model_name, move_prompts, base64_image=None, base64_image2=None):    
    base64_images = [img for img in [base64_image, base64_image2] if img] 

    if api_provider == "anthropic":
        response = anthropic_completion(system_prompt, model_name, base64_images, move_prompts)
    elif api_provider == "openai":
        response = openai_completion(system_prompt, model_name, base64_images, move_prompts)
    elif api_provider == "gemini":
        response = gemini_completion(system_prompt, model_name, base64_images, move_prompts)
    else:
        raise NotImplementedError(f"API provider '{api_provider}' is not supported.")
    
    return response



