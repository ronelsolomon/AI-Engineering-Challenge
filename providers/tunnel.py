import os
import subprocess
import time
import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class TunnelProvider(ABC):
    @abstractmethod
    async def start(self, port: int) -> str:
        pass
    
    @abstractmethod
    async def stop(self):
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def is_free(self) -> bool:
        pass

class CloudflareTunnelProvider(TunnelProvider):
    def __init__(self):
        self.process = None
        self.url = None
        self._started = False
    
    def get_name(self) -> str:
        return "Cloudflare Tunnel"
    
    def is_free(self) -> bool:
        return True
    
    async def start(self, port: int) -> str:
        if self._started:
            return self.url
        
        cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            raise RuntimeError("cloudflared not installed. Install from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        
        self.url = await self._wait_for_url()
        self._started = True
        logger.info(f"Cloudflare Tunnel started: {self.url}")
        return self.url
    
    async def stop(self):
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
            self.process = None
            self._started = False
    
    async def _wait_for_url(self, timeout: int = 15) -> str:
        import re
        start = time.time()
        url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
        
        while time.time() - start < timeout:
            if self.process and self.process.stdout:
                line = await self.process.stdout.readline()
                if line:
                    text = line.decode().strip()
                    logger.debug(f"cloudflared: {text}")
                    match = url_pattern.search(text)
                    if match:
                        return match.group(0)
            await asyncio.sleep(0.1)
        raise RuntimeError("Cloudflare Tunnel URL not found in output")

class NgrokTunnelProvider(TunnelProvider):
    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token or os.getenv("NGROK_AUTH_TOKEN")
        self.process = None
        self.url = None
        self._started = False
    
    def get_name(self) -> str:
        return "Ngrok"
    
    def is_free(self) -> bool:
        return True  # Free tier available
    
    async def start(self, port: int) -> str:
        if self._started:
            return self.url
        
        if not self.auth_token:
            raise ValueError("NGROK_AUTH_TOKEN not set")
        
        cmd = ["ngrok", "http", str(port), "--authtoken", self.auth_token, "--log", "stdout"]
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            raise RuntimeError("ngrok not installed. Install from https://ngrok.com/download")
        
        self.url = await self._wait_for_url()
        self._started = True
        logger.info(f"Ngrok started: {self.url}")
        return self.url
    
    async def stop(self):
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
            self.process = None
            self._started = False
    
    async def _wait_for_url(self, timeout: int = 15) -> str:
        import re
        start = time.time()
        url_pattern = re.compile(r'url=(https://[a-zA-Z0-9-]+\.ngrok(-free)?\.io)')
        
        while time.time() - start < timeout:
            if self.process and self.process.stdout:
                line = await self.process.stdout.readline()
                if line:
                    text = line.decode().strip()
                    logger.debug(f"ngrok: {text}")
                    match = url_pattern.search(text)
                    if match:
                        return match.group(1)
            await asyncio.sleep(0.1)
        raise RuntimeError("Ngrok URL not found in output")

class NoTunnelProvider(TunnelProvider):
    def __init__(self):
        self._url = None
    
    def get_name(self) -> str:
        return "No Tunnel (local only)"
    
    def is_free(self) -> bool:
        return True
    
    async def start(self, port: int) -> str:
        self._url = f"http://localhost:{port}"
        return self._url
    
    async def stop(self):
        pass

class HybridTunnel:
    def __init__(self):
        self.providers = []
        
        try:
            self.providers.append(CloudflareTunnelProvider())
        except Exception as e:
            logger.warning(f"Cloudflare Tunnel not available: {e}")
        
        ngrok_token = os.getenv("NGROK_AUTH_TOKEN")
        if ngrok_token:
            try:
                self.providers.append(NgrokTunnelProvider(ngrok_token))
            except Exception as e:
                logger.warning(f"Ngrok not available: {e}")
        
        self.providers.append(NoTunnelProvider())
        self.current_index = 0
        self.active_provider = None
    
    async def start(self, port: int) -> str:
        for attempt in range(len(self.providers)):
            provider = self.providers[self.current_index]
            try:
                logger.info(f"Tunnel attempt {attempt + 1}: using {provider.get_name()}")
                url = await asyncio.wait_for(provider.start(port), timeout=20.0)
                self.active_provider = provider
                return url
            except Exception as e:
                logger.warning(f"{provider.get_name()} failed: {e}")
                self.current_index = (self.current_index + 1) % len(self.providers)
                await asyncio.sleep(0.5)
        
        raise RuntimeError("All tunnel providers failed")
    
    async def stop(self):
        if self.active_provider:
            await self.active_provider.stop()
            self.active_provider = None
