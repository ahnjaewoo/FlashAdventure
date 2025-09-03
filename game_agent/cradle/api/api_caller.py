from api.serving import anthropic_completion, openai_completion, gemini_completion

def api_caller(api_provider, system_prompt, model_name, move_prompts, base64_images=None):
    """
    Unified API caller for multiple model providers.
    
    Parameters:
        - api_provider (str): "anthropic", "openai", or "gemini"
        - system_prompt (str): System-level instruction
        - model_name (str): Model identifier (e.g., "gpt-4", "claude-3")
        - move_prompts (str): Main user prompt for this action
        - base64_images (str | list[str] | None): Single base64 image or list of them
    
    Returns:
        - response (str): Textual result from model
    """

    # --- Normalize image input ---
    if isinstance(base64_images, str):
        base64_images = [base64_images]
    elif base64_images is None:
        base64_images = []
    elif not isinstance(base64_images, list):
        raise TypeError("base64_images must be a base64 string, a list of strings, or None.")

    if not all(isinstance(img, str) for img in base64_images):
        raise ValueError("Each item in base64_images must be a string.")

    # --- Dispatch based on provider ---
    if api_provider == "anthropic":
        return anthropic_completion(system_prompt, model_name, base64_images, move_prompts)

    elif api_provider == "openai":
        return openai_completion(system_prompt, model_name, base64_images, move_prompts)

    elif api_provider == "gemini":
        return gemini_completion(system_prompt, model_name, base64_images, move_prompts)

    else:
        raise NotImplementedError(f"Unsupported API provider: '{api_provider}'")