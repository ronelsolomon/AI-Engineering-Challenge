# Architecture Documentation

## System Overview

The Voice Bot Tester is an automated system that places outbound calls to a test AI voice agent, simulates realistic patient conversations, and evaluates the agent's responses for bugs and quality issues. The system is built in Python and uses Twilio for telephony, OpenAI for LLM and TTS, and FastAPI for the webhook server.

## Architecture Decisions

### 1. Telephony: Twilio with TwiML `<Gather>` and `<Play>`

I chose Twilio for telephony because it's the most reliable and widely-used cloud telephony platform with excellent Python SDK support. For the voice conversation loop, I initially considered Twilio Media Streams with bidirectional WebSockets for real-time audio streaming. However, after evaluating the complexity of audio format conversion (μ-law ↔ PCM), WebSocket lifecycle management, and potential audio overlap issues, I opted for a simpler TwiML-based approach using `<Gather>` for speech recognition and `<Play>` for audio playback.

**Tradeoffs:**
- **WebSocket approach**: Lower latency (~2s round-trip), supports barge-in, more control over audio. But requires complex audio format conversion, WebSocket state management, and has more failure points.
- **TwiML approach**: Higher latency (~4-6s round-trip), no barge-in support, but much simpler to implement and debug. Reliable turn-taking behavior which aligns with the challenge requirements for "sensible turn-taking behavior."

The TwiML approach provides a robust foundation that can be extended to WebSockets later if lower latency becomes critical.

### 2. LLM: OpenAI GPT-4o-mini

I chose OpenAI GPT-4o-mini for conversation logic because it's fast, cost-effective, and produces natural conversational responses. The LLM acts as the "patient brain," generating contextually appropriate responses based on the conversation history and scenario goals.

**Tradeoffs:**
- **GPT-4o-mini**: Fast, cheap, good quality. Ideal for this use case.
- **GPT-4o**: Higher quality but 3-5x more expensive and slightly slower.
- **Claude/Anthropic**: Good quality but higher latency and different pricing model.

The system prompt constrains the LLM to stay in character as a patient, keep responses short (1-3 sentences), and focus on achieving scenario goals. This minimizes token usage and keeps conversations natural.

### 3. TTS: OpenAI TTS-1

I chose OpenAI's TTS-1 model for speech synthesis because it produces highly natural-sounding audio with low latency. The audio is cached by content hash to avoid regenerating identical responses.

**Tradeoffs:**
- **OpenAI TTS-1**: Natural voice, low latency, simple REST API. Good for this use case.
- **Deepgram Aura**: Also natural, but requires WebSocket connection for streaming.
- **ElevenLabs**: Highest quality but higher cost and more complex API.

The TTS audio is served statically from the FastAPI server and played into the call via Twilio's `<Play>` verb.

### 4. STT: Twilio Built-in Speech Recognition

I'm using Twilio's built-in speech recognition via the `<Gather>` verb instead of Deepgram or OpenAI Whisper. This eliminates the need for a separate transcription service and reduces API calls.

**Tradeoffs:**
- **Twilio STT**: Integrated with telephony, no separate API needed, good for short utterances. Accuracy is slightly lower than Deepgram for medical terminology.
- **Deepgram STT**: Higher accuracy, real-time streaming, but requires WebSocket integration.
- **OpenAI Whisper**: Highest accuracy but not real-time and requires audio file processing.

For this challenge, Twilio STT is sufficient and simplifies the architecture.

### 5. Server: FastAPI

FastAPI was chosen for its async support, automatic OpenAPI documentation, and easy integration with Twilio webhooks. The server handles inbound webhooks from Twilio, manages conversation state, and serves static audio files.

## Data Flow

1. **Call Initiation**: User triggers `/start-call` endpoint → Twilio REST API creates outbound call
2. **Call Connection**: Twilio calls the target number → Twilio requests `/twiml` → Server returns TwiML with `<Gather>`
3. **Agent Speaks**: Agent's speech is captured by Twilio's speech recognition → Twilio POSTs transcript to `/handle-speech`
4. **Response Generation**: Server saves transcript → LLM generates patient response → TTS synthesizes audio
5. **Response Playback**: Server returns TwiML with `<Play>` → Twilio plays audio into the call
6. **Loop**: Twilio executes `<Gather>` again → Agent responds → Repeat from step 3
7. **Call End**: Twilio sends status callback → Server downloads recordings → Transcripts are saved

## Conversation State Management

The system maintains conversation state through:
- **Transcript files**: One text file per call, appended with each exchange
- **In-memory history**: Passed to the LLM for context-aware responses
- **Scenario context**: Each scenario defines goals and initial context for the LLM

## Bug Detection

After calls complete, the system analyzes transcripts using an LLM to identify:
- Factual errors (wrong dates, times, medications)
- Hallucinations
- Poor edge case handling
- Incorrect confirmations
- Missing verification steps

The analysis is automated via the `/analyze` command which processes all transcripts and generates a structured bug report.

## Future Improvements

If extending the system, the most impactful upgrade would be implementing Twilio Media Streams with Deepgram for:
- Lower latency (~2s vs ~4-6s round-trip)
- Higher STT accuracy
- Barge-in support
- Real-time conversation monitoring
