import os
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" – change as needed

async def text_to_speech(text: str) -> bytes:
    """Generate speech from text using ElevenLabs"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.content  # Raw audio (MP3)
    else:
        raise Exception(f"TTS failed: {response.text}")
