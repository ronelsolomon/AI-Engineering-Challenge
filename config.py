import os
from dotenv import load_dotenv

load_dotenv()

# Twilio (paid - required for telephony)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# LLM Providers (try free first, fallback to paid)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# TTS Providers (free-first, fallback to paid)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Tunnel Providers (free-first)
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")

# Server
SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
TEST_TARGET_NUMBER = os.getenv("TEST_TARGET_NUMBER", "+18054398008")

BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CALLS_DIR = os.path.join(DATA_DIR, "calls")
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")

for d in [DATA_DIR, CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)
