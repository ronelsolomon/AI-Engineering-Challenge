import os
import io
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def synthesize(text: str, voice: str = "nova") -> bytes:
    if not text.strip():
        return b""
    response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )
    audio_bytes = b""
    async for chunk in response.iter_bytes():
        audio_bytes += chunk
    return audio_bytes
