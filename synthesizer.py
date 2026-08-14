import logging
from providers.tts import HybridTTS

logger = logging.getLogger(__name__)

_hybrid_tts = None

def get_tts() -> HybridTTS:
    global _hybrid_tts
    if _hybrid_tts is None:
        _hybrid_tts = HybridTTS()
    return _hybrid_tts

async def synthesize(text: str) -> bytes:
    if not text.strip():
        return b""
    
    try:
        tts = get_tts()
        audio, provider = await tts.synthesize(text)
        logger.info(f"TTS synthesized using {provider}: {len(audio)} bytes")
        return audio
    except Exception as e:
        logger.error(f"All TTS providers failed: {e}")
        return b""
