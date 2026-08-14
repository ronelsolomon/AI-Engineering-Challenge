import os
import json
import logging
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse, Play, Gather, Say
from config import BASE_URL, PUBLIC_URL, CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR
from scenarios import SCENARIOS
from conversation import get_response
from synthesizer import synthesize
from call_manager import start_call, get_call_status, get_recordings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="data/audio"), name="static")

@app.api_route("/twiml", methods=["GET", "POST"])
async def get_twiml(request: Request, scenario_id: str = "appointment_simple"):
    call_sid = request.query_params.get("CallSid", "unknown")
    if call_sid == "unknown" and request.method == "POST":
        try:
            form = await request.form()
            call_sid = form.get("CallSid", "unknown")
        except Exception:
            pass
    
    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{scenario_id}_{call_sid}.txt")
    if not os.path.exists(transcript_path):
        with open(transcript_path, "w") as f:
            f.write(f"Scenario: {scenario_id}\n")
            f.write(f"Call SID: {call_sid}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n")
    
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"/handle-speech?scenario_id={scenario_id}",
        speechTimeout="auto",
        timeout=30,
        method="POST"
    )
    response.append(gather)
    return PlainTextResponse(str(response), media_type="application/xml")

@app.post("/handle-speech")
async def handle_speech(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    scenario_id = request.query_params.get("scenario_id", form.get("scenario_id", "appointment_simple"))
    speech_result = form.get("SpeechResult", "")
    confidence = form.get("Confidence", "0")
    
    logger.info(f"Speech received: '{speech_result}' (confidence: {confidence})")
    
    from scenarios import SCENARIOS
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), SCENARIOS[0])
    
    response = VoiceResponse()
    
    if not speech_result:
        response.say("I'm sorry, I didn't catch that. Could you please repeat?", voice="alice")
        gather = Gather(
            input="speech",
            action=f"/handle-speech?scenario_id={scenario_id}",
            speechTimeout="auto",
            timeout=30,
            method="POST"
        )
        response.append(gather)
        return PlainTextResponse(str(response), media_type="application/xml")
    
    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{scenario_id}_{call_sid}.txt")
    
    timeout_count = 0
    patient_turn_count = 0
    if os.path.exists(transcript_path):
        with open(transcript_path, "r") as f:
            content = f.read()
            timeout_count = content.count("I'm sorry, I didn't catch that")
            patient_turn_count = content.count("Patient:")
    
    if timeout_count >= 3:
        response.say("I'm having trouble hearing you. Goodbye.", voice="alice")
        response.hangup()
        return PlainTextResponse(str(response), media_type="application/xml")
    
    if patient_turn_count >= 15:
        response.say("Thank you for your help. I think I have all the information I need. Goodbye.", voice="alice")
        response.hangup()
        return PlainTextResponse(str(response), media_type="application/xml")
    
    with open(transcript_path, "a") as f:
        f.write(f"Agent: {speech_result}\n")
    
    history = []
    if os.path.exists(transcript_path):
        with open(transcript_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Agent:"):
                    history.append({"role": "user", "content": line[6:].strip()})
                elif line.startswith("Patient:"):
                    history.append({"role": "assistant", "content": line[8:].strip()})
    
    llm_response = await get_response(history, scenario)
    logger.info(f"LLM response: {llm_response}")
    
    with open(transcript_path, "a") as f:
        f.write(f"Patient: {llm_response}\n")
    
    audio_filename = f"{scenario_id}_{call_sid}_{uuid.uuid4().hex[:8]}.mp3"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)
    
    try:
        if not os.path.exists(audio_path):
            audio_bytes = await synthesize(llm_response)
            if audio_bytes:
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)
            else:
                response.say(llm_response, voice="alice")
                gather = Gather(
                    input="speech",
                    action=f"/handle-speech?scenario_id={scenario_id}",
                    speechTimeout="auto",
                    timeout=30,
                    method="POST"
                )
                response.append(gather)
                return PlainTextResponse(str(response), media_type="application/xml")
        
        play_url = f"{PUBLIC_URL}/static/{audio_filename}"
        response.play(play_url, voice="alice")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        response.say(llm_response, voice="alice")
    
    gather = Gather(
        input="speech",
        action=f"/handle-speech?scenario_id={scenario_id}",
        speechTimeout="auto",
        timeout=30,
        method="POST"
    )
    response.append(gather)
    return PlainTextResponse(str(response), media_type="application/xml")

@app.post("/recording")
async def recording_callback(request: Request):
    form = await request.form()
    logger.info(f"Recording callback: {dict(form)}")
    return Response(status_code=200)

@app.post("/call-status")
async def call_status_callback(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    logger.info(f"Call {call_sid} status: {call_status}")
    
    if call_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
        call_dir = os.path.join(CALLS_DIR, "unsorted")
        os.makedirs(call_dir, exist_ok=True)
        meta_path = os.path.join(call_dir, f"{call_sid}_meta.txt")
        with open(meta_path, "w") as f:
            f.write(f"Call SID: {call_sid}\n")
            f.write(f"Status: {call_status}\n")
            f.write(f"Ended: {datetime.now().isoformat()}\n")
    
    return Response(status_code=200)

@app.get("/")
async def root():
    return {
        "status": "running",
        "endpoints": ["/twiml", "/handle-speech", "/start-call", "/static/{filename}"]
    }

@app.post("/start-call")
async def start_call_endpoint(request: Request):
    form = await request.form()
    scenario_id = form.get("scenario_id", "appointment_simple")
    webhook_url = str(request.base_url).rstrip("/")
    
    try:
        result = start_call(scenario_id, webhook_url)
        return result
    except Exception as e:
        logger.error(f"Failed to start call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
