import asyncio
import threading
import queue
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from config import DEEPGRAM_API_KEY

class Transcriber:
    def __init__(self):
        self.client = DeepgramClient(access_token=DEEPGRAM_API_KEY)
        self.audio_queue = queue.Queue()
        self.transcript_queue = asyncio.Queue()
        self.thread = None
        self.running = False
        self.final_transcript = ""
        self.interim_transcript = ""

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            with self.client.listen.v1.connect(
                model="nova-3",
                encoding="linear16",
                sample_rate=16000,
                channels=1,
                punctuate=True,
                interim_results=True,
                endpointing=300,
                smart_format=True,
            ) as socket:
                socket.on(EventType.MESSAGE, self._on_message)
                
                while self.running:
                    try:
                        audio = self.audio_queue.get(timeout=0.1)
                        socket.send_media(audio)
                    except queue.Empty:
                        continue
                    except Exception:
                        break
        except Exception as e:
            print(f"Deepgram STT error: {e}")

    def _on_message(self, message):
        try:
            if hasattr(message, 'channel'):
                transcript = message.channel.alternatives[0].transcript
                if transcript:
                    if message.is_final:
                        self.final_transcript = transcript
                        try:
                            asyncio.get_event_loop().call_soon_threadsafe(
                                self.transcript_queue.put_nowait, transcript.strip()
                            )
                        except RuntimeError:
                            pass
                    else:
                        self.interim_transcript = transcript
        except Exception as e:
            print(f"Transcript parse error: {e}")

    async def send_audio(self, mulaw_bytes: bytes):
        import audioop
        pcm = audioop.ulaw2lin(mulaw_bytes, 2)
        self.audio_queue.put(pcm)

    async def get_final_transcript(self, timeout: float = 5.0) -> str:
        try:
            return await asyncio.wait_for(self.transcript_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return ""

    def get_interim(self) -> str:
        return self.interim_transcript

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
