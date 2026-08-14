import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
TEST_TARGET_NUMBER = os.getenv("TEST_TARGET_NUMBER", "+18054398008")

BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CALLS_DIR = os.path.join(DATA_DIR, "calls")
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")

for d in [DATA_DIR, CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)
