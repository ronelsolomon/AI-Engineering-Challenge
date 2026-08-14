# Voice Bot Tester

An automated voice bot that calls a test line and has conversations with an AI agent. The bot simulates realistic patient scenarios, records conversations, and identifies bugs in the agent's responses.

## Prerequisites

- Python 3.10+
- Twilio account (with a phone number)
- OpenAI API key
- Deepgram API key (optional, for enhanced STT)
- ngrok (for exposing local server to Twilio webhooks)

## Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd voice-bot-tester
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Required environment variables:
   - `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER` - Your Twilio phone number (E.164 format)
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `DEEPGRAM_API_KEY` - Your Deepgram API key (optional)
   - `NGROK_AUTH_TOKEN` - Your ngrok authtoken

5. Start ngrok in a separate terminal:
   ```bash
   python start_ngrok.py
   ```
   Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

## Usage

### Start the Server

In one terminal:
```bash
python main.py server --port 8000
```

### Make a Single Call

In another terminal:
```bash
python main.py call --scenario appointment_simple --webhook-url https://abc123.ngrok-free.app
```

### Run a Batch of Calls

```bash
python main.py batch --scenarios appointment_simple refill_request office_hours --webhook-url https://abc123.ngrok-free.app
```

### Analyze Transcripts for Bugs

```bash
python main.py analyze
```

## Scenarios

The bot comes with 12 built-in scenarios:

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

## Project Structure

```
voice-bot-tester/
├── server.py              # FastAPI server with Twilio webhooks
├── main.py                # CLI entry point
├── call_manager.py        # Twilio call orchestration
├── conversation.py        # LLM conversation logic
├── synthesizer.py         # Text-to-speech (OpenAI)
├── transcriber.py         # Speech-to-text (Deepgram/OpenAI)
├── scenarios.py           # Patient scenario definitions
├── analyzer.py            # Bug detection from transcripts
├── audio_utils.py         # Audio format conversion utilities
├── config.py              # Configuration management
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

## Troubleshooting

### Ngrok URL Changed
If your ngrok URL changes, update the webhook URLs in your Twilio console or restart ngrok with a reserved domain.

### Call Not Connecting
- Verify your Twilio phone number is correct
- Check that the test number (+1-805-439-8008) is reachable
- Ensure your Twilio account has sufficient balance

### Audio Not Playing
- Verify the server is accessible via the ngrok URL
- Check that audio files are being generated in `data/audio/`
- Ensure Twilio can access the `/static/` endpoint

### Transcripts Empty
- Check Twilio's speech recognition settings
- Verify the `/handle-speech` endpoint is receiving POST requests
- Check server logs for errors

## Cost Estimate

- Twilio: ~$0.01-0.05 per outbound call (US numbers)
- OpenAI GPT-4o-mini: ~$0.10-0.30 per call (LLM + TTS)
- Total for 12 calls: ~$2-5
