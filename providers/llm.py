import os
import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], max_tokens: int = 150) -> str:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def is_free(self) -> bool:
        pass

class GroqProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama-3.1-8b-instant"
        self._last_request_time = 0
        self._min_interval = 2.0  # 30 RPM = 1 request per 2 seconds
        self._daily_count = 0
        self._daily_reset = time.time() + 86400
    
    def get_name(self) -> str:
        return "Groq"
    
    def is_free(self) -> bool:
        return True
    
    async def generate(self, messages: list[dict], max_tokens: int = 150) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set")
        
        now = time.time()
        if now - self._daily_reset > 86400:
            self._daily_count = 0
            self._daily_reset = now + 86400
        
        if self._daily_count >= 14000:
            raise ValueError("Groq daily limit reached (14,400 req/day)")
        
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            self._daily_count += 1
            self._last_request_time = time.time()
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq error: {e}")
            raise

class HuggingFaceProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HF_TOKEN")
        self.model = "meta-llama/Llama-3.1-8B-Instruct"
        self._last_request_time = 0
        self._min_interval = 1.0
        self._monthly_credits = 0.10  # $0.10 free credit
    
    def get_name(self) -> str:
        return "HuggingFace"
    
    def is_free(self) -> bool:
        return True
    
    async def generate(self, messages: list[dict], max_tokens: int = 150) -> str:
        if not self.api_key:
            raise ValueError("HF_TOKEN not set")
        
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        
        try:
            import httpx
            prompt = self._format_messages(messages)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{self.model}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": max_tokens,
                            "temperature": 0.7,
                            "return_full_text": False,
                        }
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
                elif isinstance(result, dict):
                    return result.get("generated_text", "").strip()
                raise ValueError(f"Unexpected HF response: {result}")
        except Exception as e:
            logger.warning(f"HuggingFace error: {e}")
            raise
    
    def _format_messages(self, messages: list[dict]) -> str:
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"<|system|>\n{content}\n")
            elif role == "user":
                parts.append(f"<|user|>\n{content}\n")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}\n")
        parts.append("<|assistant|>\n")
        return "".join(parts)

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
    
    def get_name(self) -> str:
        return "OpenAI"
    
    def is_free(self) -> bool:
        return False
    
    async def generate(self, messages: list[dict], max_tokens: int = 150) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

class HybridLLM:
    def __init__(self):
        self.providers = []
        
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.providers.append(GroqProvider(groq_key))
        
        hf_key = os.getenv("HF_TOKEN")
        if hf_key:
            self.providers.append(HuggingFaceProvider(hf_key))
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.providers.append(OpenAIProvider(openai_key))
        
        if not self.providers:
            raise ValueError("No LLM providers configured. Set at least one of: GROQ_API_KEY, HF_TOKEN, OPENAI_API_KEY")
        
        self.current_index = 0
        self.failures = {p.get_name(): 0 for p in self.providers}
    
    async def generate(self, messages: list[dict], max_tokens: int = 150) -> tuple[str, str]:
        for attempt in range(len(self.providers) * 2):
            provider = self.providers[self.current_index]
            provider_name = provider.get_name()
            
            try:
                logger.info(f"LLM attempt {attempt + 1}: using {provider_name}")
                response = await asyncio.wait_for(provider.generate(messages, max_tokens), timeout=10.0)
                self.failures[provider_name] = 0
                return response, provider_name
            except asyncio.TimeoutError:
                logger.warning(f"{provider_name} timed out")
                self.failures[provider_name] += 1
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                self.failures[provider_name] += 1
            
            self.current_index = (self.current_index + 1) % len(self.providers)
            await asyncio.sleep(0.5)
        
        raise RuntimeError("All LLM providers failed")
