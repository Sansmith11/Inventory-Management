import os
import sys
from pathlib import Path

from sarvamai import SarvamAI

# Load SARVAM_API_KEY from .env (no extra dependency needed for this).
env_path = Path(__file__).with_name(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and value and key not in os.environ:
            os.environ[key] = value

api_key = os.environ.get("SARVAM_API_KEY")
if not api_key:
    sys.exit("SARVAM_API_KEY is not set. Add it to .env and run again.")

client = SarvamAI(api_subscription_key=api_key)

response = client.chat.completions(
    messages=[{"role": "user", "content": "Hello! In one sentence, who are you?"}],
    model="sarvam-105b-conversations",
)

print(response.choices[0].message.content)
