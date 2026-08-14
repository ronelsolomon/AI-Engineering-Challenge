import os
import requests
from twilio.rest import Client
from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    BASE_URL, TEST_TARGET_NUMBER, CALLS_DIR
)
from datetime import datetime

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def start_call(scenario_id: str, webhook_url: str) -> dict:
    from scenarios import SCENARIOS
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), SCENARIOS[0])
    
    call = client.calls.create(
        to=TEST_TARGET_NUMBER,
        from_=TWILIO_PHONE_NUMBER,
        url=f"{webhook_url}/twiml?scenario_id={scenario_id}",
        record=True,
        recording_status_callback=f"{webhook_url}/recording",
        recording_status_callback_event=["completed"],
        status_callback=f"{webhook_url}/call-status",
        status_callback_event=["completed"],
        timeout=30,
        method="POST"
    )
    
    call_dir = os.path.join(CALLS_DIR, scenario_id, call.sid)
    os.makedirs(call_dir, exist_ok=True)
    
    meta_path = os.path.join(call_dir, "meta.txt")
    with open(meta_path, "w") as f:
        f.write(f"Call SID: {call.sid}\n")
        f.write(f"Scenario: {scenario_id}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write(f"To: {TEST_TARGET_NUMBER}\n")
        f.write(f"From: {TWILIO_PHONE_NUMBER}\n")
    
    return {
        "call_sid": call.sid,
        "scenario_id": scenario_id,
        "scenario_name": scenario["name"],
        "started_at": datetime.now().isoformat()
    }

def get_call_status(call_sid: str) -> dict:
    call = client.calls(call_sid).fetch()
    return {
        "sid": call.sid,
        "status": call.status,
        "duration": call.duration,
        "direction": call.direction,
    }

def get_recordings(call_sid: str):
    recordings = client.recordings.list(call_sid=call_sid)
    return [
        {
            "sid": r.sid,
            "url": f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{r.sid}.mp3",
            "duration": r.duration,
            "date_created": r.date_created.isoformat() if r.date_created else None,
        }
        for r in recordings
    ]

def download_recording(recording_sid: str, dest_path: str):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{recording_sid}.mp3"
    resp = requests.get(url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
    if resp.status_code == 200:
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
    return False
