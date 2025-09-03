import os
import dotenv
from openai import OpenAI
import anthropic
import google.generativeai as genai

# .env load
dotenv.load_dotenv()

## Use Image
def openai_completion(system_prompt, model_name, base64_images, prompt):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Message
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": []}]

    # #image > 1
    if base64_images:
        for base64_image in base64_images:
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            })
    
    # adding text prompt
    messages[1]["content"].append({"type": "text", "text": prompt})
    
    if model_name == "o4-mini-2025-04-16":
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=3000,
        )
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
            max_tokens=1024,
        )
        
    return response.choices[0].message.content

def anthropic_completion(system_prompt, model_name, base64_images, prompt):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    user_content = []
    
    # adding aditional image
    if base64_images:
        for base64_image in base64_images:
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_image,
                }
            })
    
    # adding text prompt
    user_content.append({
        "type": "text",
        "text": prompt
    })

    with client.messages.stream(
        max_tokens=2048,
        system=system_prompt, 
        messages=[
            {
                "role": "user",
                "content": user_content
            }
        ],
        temperature=0,
        model=model_name,
    ) as stream:
        partial_chunks = []
        for chunk in stream.text_stream:
            partial_chunks.append(chunk)
    
    return "".join(partial_chunks)

def gemini_completion(system_prompt, model_name, base64_images, prompt):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name=model_name)

    # message
    messages = [
        {"role": "system", "text": system_prompt}
    ]

    # adding aditional image
    if base64_images:
        for base64_image in base64_images:
            messages.append({
                "mime_type": "image/png",
                "data": base64_image,
            })
    
    # adding text prompt
    messages.append(prompt)
    
    try:
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return None
