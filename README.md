# Voice Bot Tester

An automated voice bot that calls a test line and has conversations with an AI agent. The bot simulates realistic patient scenarios, records conversations, and identifies bugs in the agent's responses.

## Hybrid Provider Architecture

This project uses a **free-first, automatic-fallback** approach for all AI services:

| Component | Primary (Free) | Fallback (Free) | Fallback (Paid) |
|-----------|----------------|-----------------|-----------------|
| **LLM** | Groq (30 RPM, 14,400 req/day) | HuggingFace ($0.10/mo credits) | OpenAI GPT-4o-mini |
| **TTS** | Edge-TTS (Microsoft, no key) | gTTS (Google Translate, no key) | pyttsx3 (offline) → OpenAI TTS |
| **Tunnel** | Cloudflare Quick Tunnel (no signup) | Ngrok free tier | Local only |
| **Telephony** | Twilio trial (~$15 credit) | - | - |

**Only Twilio requires payment** (telephony). The challenge reimburses up to $20. Everything else can run completely free.

## Prerequisites

- Python 3.10+
- Twilio account (with a phone number) - **paid, but reimbursable**
- **Optional**: Groq API key (free, no credit card) for LLM
- **Optional**: HuggingFace token (free, $0.10/mo credits) for LLM
- **Optional**: OpenAI API key (paid, best quality)
- `cloudflared` (free tunnel, `brew install cloudflared`) OR `ngrok` (free tier)

## Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials. **At minimum, you need Twilio credentials.** For fully free operation:
- Set `GROQ_API_KEY` (sign up at console.groq.com, no credit card needed)
- Leave `OPENAI_API_KEY` unset to avoid charges

### 3. Verify Providers

```bash
python main.py status
```

This shows which LLM, TTS, and tunnel providers are available and whether they're free or paid.

### 4. Start Server + Tunnel

**Option A: Using Cloudflare Tunnel (recommended, no auth needed)**
```bash
# Terminal 1: Start server
python main.py server --port 8000

# Terminal 2: Start tunnel
python main.py tunnel --port 8000
```

**Option B: Using Ngrok**
```bash
# Terminal 1: Start server
python main.py server --port 8000

# Terminal 2: Start ngrok
python start_ngrok.py
```

## Usage

### Make a Single Call

```bash
python main.py call --scenario appointment_simple --webhook-url https://your-tunnel-url.trycloudflare.com
```

### Run a Batch of Calls

```bash
python main.py batch --webhook-url https://your-tunnel-url.trycloudflare.com
```

### Simulate Conversations (No Phone Calls)

Test the conversation logic without making real calls:

```bash
python main.py simulate --scenario appointment_simple
```

### Analyze Transcripts for Bugs

```bash
python main.py analyze
```

## Scenarios

12 built-in patient scenarios:

| ID | Name |
|----|------|
| `appointment_simple` | Simple appointment scheduling |
| `appointment_reschedule` | Rescheduling an existing appointment |
| `appointment_cancel` | Canceling an appointment |
| `refill_request` | Medication refill request |
| `office_hours` | Office hours and location inquiry |
| `insurance_question` | Insurance verification |
| `prescription_question` | Question about prescription |
| `billing_question` | Billing inquiry |
| `barge_in_test` | Testing interruption handling |
| `unclear_request` | Testing unclear request handling |
| `weekend_appointment` | Weekend appointment edge case |
| `multiple_requests` | Multiple requests in one call |

## Architecture

### Data Flow

1. **Twilio** places outbound call to `+1-805-439-8008`
2. **Twilio `<Gather>`** captures agent speech → sends to `/handle-speech`
3. **Hybrid LLM** (Groq → HuggingFace → OpenAI) generates patient response
4. **Hybrid TTS** (Edge-TTS → gTTS → pyttsx3 → OpenAI) synthesizes audio
5. **Twilio `<Play>`** delivers audio back into the call
6. Loop until conversation ends or max turns reached
7. **Twilio recordings** downloaded automatically; transcripts analyzed by LLM

### Fallback Behavior

If a provider fails (rate limit, timeout, error), the system automatically tries the next provider in the chain. For example:
- If Groq hits its daily limit → falls back to HuggingFace
- If Edge-TTS is blocked → falls back to gTTS
- If Cloudflare Tunnel fails → falls back to Ngrok or local-only mode

## Cost Breakdown

| Service | Free Tier | Paid Fallback | Estimated Cost for 12 Calls |
|---------|-----------|---------------|----------------------------|
| Twilio | Trial ($15 credit) | Pay-as-you-go | ~$1-3 (reimbursable) |
| Groq LLM | 14,400 req/day | - | **$0** |
| HuggingFace | $0.10/mo credits | - | **$0** |
| OpenAI LLM | - | GPT-4o-mini | ~$0.50 (if used) |
| Edge-TTS | Unlimited (unofficial) | - | **$0** |
| gTTS | Unlimited (unofficial) | - | **$0** |
| pyttsx3 | Unlimited (offline) | - | **$0** |
| Cloudflare Tunnel | Quick Tunnels (free) | - | **$0** |
| Ngrok | 20k req/mo | - | **$0** |

**Minimum cost to run: $0** (if you have Twilio trial credit)
**Maximum cost with all paid fallbacks: ~$2-5**

## Troubleshooting

### No LLM Providers Available
Set at least one of: `GROQ_API_KEY`, `HF_TOKEN`, or `OPENAI_API_KEY`

### No TTS Providers Available
Install at least one: `pip install edge-tts`, `pip install gtts`, or `pip install pyttsx3`

### Cloudflare Tunnel Not Starting
- Ensure `cloudflared` is installed: `brew install cloudflared`
- Check that port 8000 is available

### Call Not Connecting
- Verify Twilio credentials and phone number
- Ensure webhook URL is accessible from the internet
- Check Twilio console for error logs

## Project Structure

```
├── server.py              # FastAPI server with Twilio webhooks
├── main.py                # CLI entry point
├── call_manager.py        # Twilio call orchestration
├── conversation.py        # Hybrid LLM conversation logic
├── synthesizer.py         # Hybrid TTS audio generation
├── scenarios.py           # Patient scenario definitions
├── analyzer.py            # LLM-powered bug detection
├── providers/
│   ├── __init__.py
│   ├── llm.py             # Groq → HuggingFace → OpenAI fallbacks
│   ├── tts.py             # Edge-TTS → gTTS → pyttsx3 → OpenAI fallbacks
│   └── tunnel.py          # Cloudflare → Ngrok → local fallbacks
├── config.py              # Environment configuration
├── .env.example           # Environment variable template
├── requirements.txt       # Python dependencies
├── start_ngrok.py         # Ngrok tunnel helper
├── README.md              # This file
├── ARCHITECTURE.md        # Architecture documentation
├── BUG_REPORT.md          # Generated bug report
└── data/
    ├── calls/             # Call recordings and metadata
    ├── transcripts/       # Conversation transcripts
    └── audio/             # TTS audio cache
```
