"""Thin wrappers around the Sarvam SDK. Real API calls only — no invented endpoints."""
import base64
import os
from pathlib import Path

from sarvamai import SarvamAI

# Load .env manually (same approach as chat.py, no extra dependency).
_env_path = Path(__file__).with_name(".env")
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k and v and k not in os.environ:
            os.environ[k] = v

_API_KEY = os.environ.get("SARVAM_API_KEY")


def _client() -> SarvamAI:
    if not _API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set. Add it to .env.")
    return SarvamAI(api_subscription_key=_API_KEY)


# Map Sarvam's BCP-47-ish codes to a friendly speaker per language (all real
# speaker names from the SDK's speaker enum).
_DEFAULT_SPEAKER = "priya"


def speech_to_text(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """Transcribe audio, auto-detecting the Indian language spoken."""
    client = _client()
    resp = client.speech_to_text.transcribe(
        file=(filename, audio_bytes),
        model="saaras:v3",
        language_code="unknown",  # auto-detect
    )
    return {"transcript": resp.transcript, "language_code": resp.language_code}


def text_to_speech(text: str, language_code: str = "en-IN") -> bytes:
    """Convert text to speech audio (mp3 bytes) in the given language."""
    client = _client()
    resp = client.text_to_speech.convert(
        text=text,
        language_code=language_code if language_code != "unknown" else "en-IN",
        speaker=_DEFAULT_SPEAKER,
        model="bulbul:v3",
        output_audio_codec="mp3",
    )
    audio_b64 = resp.audios[0]
    return base64.b64decode(audio_b64)


def chat_with_tools(messages: list[dict], tool_schemas: list[dict]) -> "sarvamai.types.create_chat_completion_response.CreateChatCompletionResponse":
    """One chat-completions call with function-calling enabled."""
    client = _client()
    tools = [{"type": "function", "function": s} for s in tool_schemas]
    return client.chat.completions(
        messages=messages,
        model="sarvam-105b-conversations",
        tools=tools,
        tool_choice="auto",
    )
