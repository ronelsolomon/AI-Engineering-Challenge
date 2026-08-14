import os
import time
import asyncio
import logging
import tempfile
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def is_free(self) -> bool:
        pass

class EdgeTTSProvider(TTSProvider):
    def __init__(self):
        self._last_request_time = 0
        self._min_interval = 0.5
        self._voice = "en-US-AriaNeural"
    
    def get_name(self) -> str:
        return "Edge-TTS"
    
    def is_free(self) -> bool:
        return True
    
    async def synthesize(self, text: str) -> bytes:
        if not text.strip():
            return b""
        
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text=text, voice=self._voice)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            
            await communicate.save(tmp_path)
            self._last_request_time = time.time()
            
            with open(tmp_path, "rb") as f:
                data = f.read()
            os.unlink(tmp_path)
            return data
        except Exception as e:
            logger.warning(f"Edge-TTS error: {e}")
            raise

class GTTSProvider(TTSProvider):
    def __init__(self):
        self._last_request_time = 0
        self._min_interval = 1.0
        self._char_count = 0
        self._char_reset = time.time() + 3600
    
    def get_name(self) -> str:
        return "gTTS"
    
    def is_free(self) -> bool:
        return True
    
    async def synthesize(self, text: str) -> bytes:
        if not text.strip():
            return b""
        
        now = time.time()
        if now - self._char_reset > 3600:
            self._char_count = 0
            self._char_reset = now + 3600
        
        if self._char_count > 50000:
            raise ValueError("gTTS hourly character limit reached (~50k/hour)")
        
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            
            tts.save(tmp_path)
            self._last_request_time = time.time()
            self._char_count += len(text)
            
            with open(tmp_path, "rb") as f:
                data = f.read()
            os.unlink(tmp_path)
            return data
        except Exception as e:
            logger.warning(f"gTTS error: {e}")
            raise

class PyttsxProvider(TTSProvider):
    def __init__(self):
        self._engine = None
    
    def get_name(self) -> str:
        return "pyttsx3"
    
    def is_free(self) -> bool:
        return True
    
    async def synthesize(self, text: str) -> bytes:
        if not text.strip():
            return b""
        
        try:
            import pyttsx3
            import tempfile
            
            if self._engine is None:
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', 150)
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_speak, tmp_path, text)
            
            with open(tmp_path, "rb") as f:
                data = f.read()
            os.unlink(tmp_path)
            return data
        except Exception as e:
            logger.warning(f"pyttsx3 error: {e}")
            raise
    
    def _sync_speak(self, path: str, text: str):
        self._engine.save_to_file(text, path)
        self._engine.runAndWait()

class OpenAITTSProvider(TTSProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = "tts-1"
        self.voice = "nova"
    
    def get_name(self) -> str:
        return "OpenAI-TTS"
    
    def is_free(self) -> bool:
        return False
    
    async def synthesize(self, text: str) -> bytes:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        
        response = await client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3",
        )
        
        audio_bytes = b""
        async for chunk in response.iter_bytes():
            audio_bytes += chunk
        return audio_bytes

class HybridTTS:
    def __init__(self):
        self.providers = []
        
        try:
            import edge_tts
            self.providers.append(EdgeTTSProvider())
        except ImportError:
            logger.info("edge-tts not installed, skipping Edge-TTS provider")
        
        try:
            import gtts
            self.providers.append(GTTSProvider())
        except ImportError:
            logger.info("gTTS not installed, skipping gTTS provider")
        
        try:
            import pyttsx3
            self.providers.append(PyttsxProvider())
        except ImportError:
            logger.info("pyttsx3 not installed, skipping pyttsx3 provider")
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.providers.append(OpenAITTSProvider(openai_key))
        
        if not self.providers:
            raise ValueError("No TTS providers available. Install edge-tts, gTTS, or pyttsx3, or set OPENAI_API_KEY")
        
        self.current_index = 0
        self.failures = {p.get_name(): 0 for p in self.providers}
    
    async def synthesize(self, text: str) -> tuple[bytes, str]:
        for attempt in range(len(self.providers) * 2):
            provider = self.providers[self.current_index]
            provider_name = provider.get_name()
            
            try:
                logger.info(f"TTS attempt {attempt + 1}: using {provider_name}")
                audio = await asyncio.wait_for(provider.synthesize(text), timeout=30.0)
                if audio:
                    self.failures[provider_name] = 0
                    return audio, provider_name
                raise ValueError("Empty audio returned")
            except asyncio.TimeoutError:
                logger.warning(f"{provider_name} timed out")
                self.failures[provider_name] += 1
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                self.failures[provider_name] += 1
            
            self.current_index = (self.current_index + 1) % len(self.providers)
            await asyncio.sleep(0.5)
        
        raise RuntimeError("All TTS providers failed")
