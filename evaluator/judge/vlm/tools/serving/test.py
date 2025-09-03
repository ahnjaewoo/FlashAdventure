import anthropic
import dotenv
import os
import anthropic

# .env 파일 로드
dotenv.load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.beta.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=[
        {
          "type": "computer_20250124",
          "name": "computer",
          "display_width_px": 1024,
          "display_height_px": 768,
          "display_number": 1,
        },
        {
          "type": "text_editor_20241022",
          "name": "str_replace_editor"
        },
        {
          "type": "bash_20241022",
          "name": "bash"
        }
    ],
    messages=[{"role": "user", "content": "Save a picture of a cat to my desktop."}],
    betas=["computer-use-2025-01-24"],
    thinking={"type": "enabled", "budget_tokens": 1024}
)
print(response)
