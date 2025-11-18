from fastapi.responses import StreamingResponse
import io

@app.get("/speak")
async def speak(text: str):
    """Generate and stream TTS audio (MP3)"""
    try:
        audio_bytes = await text_to_speech(text)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        return {"error": str(e)}
