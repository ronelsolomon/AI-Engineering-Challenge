# Architecture Documentation

## System Overview

The Voice Bot Tester is an automated system that places outbound calls to a test AI voice agent, simulates realistic patient conversations, and evaluates the agent's responses for bugs and quality issues. The system uses a **hybrid, free-first provider architecture** with automatic fallbacks to minimize cost while maintaining reliability.

## Hybrid Provider Architecture

### Design Philosophy

Instead of hard-coding a single provider for each function (LLM, TTS, tunnel), the system implements a provider abstraction layer. Each component tries providers in priority order, falling back automatically on failure. This ensures:
- **Maximum free usage**: Primary providers are free whenever possible
- **Reliability**: If one provider fails, the next takes over seamlessly
- **Flexibility**: Users can configure any combination of providers via `.env`

### LLM Providers (Priority Order)

1. **Groq** (FREE) - 30 RPM, 14,400 requests/day, no credit card required
   - Model: `llama-3.1-8b-instant`
   - Best for: High-volume, fast inference
   - Fallback trigger: Rate limit (429), timeout, server error

2. **HuggingFace** (FREE) - $0.10/month free credits
   - Model: `meta-llama/Llama-3.1-8B-Instruct`
   - Best for: Backup when Groq limits are hit
   - Fallback trigger: Rate limit, queue timeout

3. **OpenAI** (PAID) - GPT-4o-mini
   - Best for: Highest quality, last resort
   - Fallback trigger: All free providers exhausted

### TTS Providers (Priority Order)

1. **Edge-TTS** (FREE) - Microsoft Edge browser TTS, no API key needed
   - Voice: `en-US-AriaNeural`
   - Best for: High-quality, zero-cost synthesis
   - Fallback trigger: Network error, rate limit

2. **gTTS** (FREE) - Google Translate TTS, no API key needed
   - Best for: Backup when Edge-TTS fails
   - Fallback trigger: HTTP 403/429, IP block
   - Limit: ~50k characters/hour (unofficial)

3. **pyttsx3** (FREE) - Offline system TTS
   - Best for: Guaranteed offline availability
   - Fallback trigger: All cloud providers fail
   - Tradeoff: Robotic voice quality

4. **OpenAI TTS** (PAID) - TTS-1 model
   - Best for: Best voice quality, last resort
   - Fallback trigger: All free providers exhausted

### Tunnel Providers (Priority Order)

1. **Cloudflare Quick Tunnel** (FREE) - No account, no auth token needed
   - Command: `cloudflared tunnel --url http://localhost:8000`
   - Best for: Instant, zero-config tunneling
   - Tradeoff: Random URL, no SLA, dev/testing only

2. **Ngrok** (FREE tier) - Requires auth token
   - Best for: Stable free tier with request inspection
   - Tradeoff: URL changes on restart, 20k req/month limit

3. **Local only** (FREE) - No tunnel
   - Best for: Testing without exposing to internet
   - Tradeoff: Twilio cannot reach localhost

### Telephony

**Twilio** (PAID, ~$1-3 for 12 calls) - The only paid component
- Required for actual phone calls to +1-805-439-8008
- Challenge reimburses up to $20
- No free alternative exists for outbound PSTN calls

## Architecture Decisions

### 1. Telephony: Twilio with TwiML `<Gather>` and `<Play>`

I chose Twilio for telephony because it's the most reliable cloud telephony platform. For the voice loop, I use TwiML `<Gather>` for speech recognition and `<Play>` for audio playback rather than WebSocket streaming.

**Tradeoffs:**
- **TwiML approach**: Higher latency (~4-6s round-trip), no barge-in, but simpler, more reliable, and provides sensible turn-taking behavior (explicitly requested in the challenge).
- **WebSocket approach**: Lower latency, barge-in support, but requires complex audio format conversion and has more failure points.

### 2. Conversation State Management

The system maintains state through:
- **Transcript files**: One text file per call, appended with each exchange
- **In-memory history**: Passed to the LLM for context-aware responses
- **Scenario context**: Each scenario defines goals and persona for the LLM

### 3. Bug Detection

After calls complete, transcripts are analyzed by an LLM to identify:
- Factual errors (wrong dates, times, medications)
- Hallucinations
- Poor edge case handling
- Incorrect confirmations

## Data Flow

1. **Call Initiation**: User triggers `/start-call` → Twilio REST API creates outbound call
2. **Call Connection**: Twilio calls target → Twilio requests `/twiml` → Server returns TwiML with `<Gather>`
3. **Agent Speaks**: Twilio STT captures speech → POSTs to `/handle-speech`
4. **Response Generation**: Hybrid LLM generates patient response → Hybrid TTS synthesizes audio
5. **Response Playback**: TwiML with `<Play>` delivers audio → Twilio plays into call
6. **Loop**: Repeat from step 3 until conversation ends
7. **Call End**: Twilio status callback → recordings downloaded → transcripts analyzed

## Cost Optimization Strategy

The system is designed to run **completely free except for Twilio telephony**:

1. **Always try free first**: Groq, Edge-TTS, Cloudflare Tunnel are tried before any paid alternative
2. **Graceful degradation**: If a free provider fails, the next provider takes over without user intervention
3. **No hard dependencies on paid services**: The only required payment is Twilio for the actual phone call
4. **Caching**: TTS audio is cached to avoid redundant synthesis calls

## Future Improvements

1. **WebSocket streaming**: Implement Twilio Media Streams with Deepgram for lower latency and barge-in
2. **Local LLM**: Add Ollama as a fallback for completely offline operation
3. **Provider health monitoring**: Track success rates and automatically reorder providers based on reliability
4. **Batch processing**: Use Groq's Batch API for analyzing multiple transcripts simultaneously
