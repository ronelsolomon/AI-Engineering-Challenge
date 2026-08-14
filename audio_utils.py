import base64
import io
import os
import tempfile
from pydub import AudioSegment

def mulaw_to_pcm(mulaw_bytes: bytes) -> bytes:
    audio = AudioSegment(
        data=mulaw_bytes,
        sample_width=1,
        frame_rate=8000,
        channels=1,
        format="mulaw"
    )
    audio = audio.set_frame_rate(16000).set_sample_width(2)
    buffer = io.BytesIO()
    audio.export(buffer, format="wav")
    return buffer.getvalue()

def pcm_to_mulaw(pcm_bytes: bytes) -> bytes:
    audio = AudioSegment.from_wav(io.BytesIO(pcm_bytes))
    audio = audio.set_frame_rate(8000).set_sample_width(1).set_channels(1)
    buffer = io.BytesIO()
    audio.export(buffer, format="mulaw", bitrate="64k")
    return buffer.getvalue()

def mp3_to_mulaw(mp3_bytes: bytes) -> bytes:
    audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
    audio = audio.set_frame_rate(8000).set_sample_width(1).set_channels(1)
    buffer = io.BytesIO()
    audio.export(buffer, format="mulaw", bitrate="64k")
    return buffer.getvalue()

def encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")

def decode_base64(data: str) -> bytes:
    return base64.b64decode(data)
