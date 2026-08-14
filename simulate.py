import os
import argparse
import asyncio
import uuid
from datetime import datetime
from config import CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR
from conversation import get_response
from synthesizer import synthesize
from scenarios import SCENARIOS

def ensure_dirs():
    for d in [CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR]:
        os.makedirs(d, exist_ok=True)

async def simulate_scenario(scenario_id: str):
    ensure_dirs()
    from scenarios import SCENARIOS
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), SCENARIOS[0])
    
    print(f"=== Simulating: {scenario['name']} ===")
    print(f"Goal: {scenario['goal']}")
    print(f"Context: {scenario['context']}")
    print()
    
    call_sid = f"SIM-{uuid.uuid4().hex[:8]}"
    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"sim_{scenario_id}_{call_sid}.txt")
    
    with open(transcript_path, "w") as f:
        f.write(f"Scenario: {scenario_id}\n")
        f.write(f"Call SID: {call_sid}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write("=" * 50 + "\n")
    
    history = []
    turn = 0
    max_turns = 10
    
    agent_opening = "Thank you for calling Dr. Smith's office. How can I help you today?"
    print(f"Agent: {agent_opening}")
    with open(transcript_path, "a") as f:
        f.write(f"Agent: {agent_opening}\n")
    history.append({"role": "user", "content": agent_opening})
    
    while turn < max_turns:
        turn += 1
        response = await get_response(history, scenario)
        print(f"Patient: {response}")
        with open(transcript_path, "a") as f:
            f.write(f"Patient: {response}\n")
        history.append({"role": "assistant", "content": response})
        
        audio_filename = f"sim_{scenario_id}_{call_sid}_{turn}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        try:
            audio_bytes = await synthesize(response)
            if audio_bytes:
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)
                print(f"  [Audio saved: {audio_path} ({len(audio_bytes)} bytes)]")
        except Exception as e:
            print(f"  [TTS error: {e}]")
        
        agent_response = input("Agent response (or 'quit' to end): ").strip()
        if agent_response.lower() in ['quit', 'exit', 'end']:
            print("Ending simulation.")
            break
        
        print(f"Agent: {agent_response}")
        with open(transcript_path, "a") as f:
            f.write(f"Agent: {agent_response}\n")
        history.append({"role": "user", "content": agent_response})
    
    print(f"\nSimulation complete. Transcript saved to: {transcript_path}")
    return transcript_path

async def run_simulation(scenario_ids: list):
    ensure_dirs()
    results = []
    for sid in scenario_ids:
        try:
            path = await simulate_scenario(sid)
            results.append({"scenario_id": sid, "status": "completed", "transcript": path})
        except Exception as e:
            print(f"Error simulating {sid}: {e}")
            results.append({"scenario_id": sid, "status": "error", "error": str(e)})
        print()
    
    print("=== Simulation Summary ===")
    for r in results:
        print(f"  {r['scenario_id']}: {r['status']}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Voice Bot Tester - Simulation Mode")
    parser.add_argument("command", choices=["simulate", "sim-batch"], help="Command to run")
    parser.add_argument("--scenario", default="appointment_simple", help="Scenario ID")
    parser.add_argument("--scenarios", nargs="*", help="Scenario IDs for batch simulation")
    
    args = parser.parse_args()
    
    if args.command == "simulate":
        asyncio.run(simulate_scenario(args.scenario))
    elif args.command == "sim-batch":
        sids = args.scenarios or [s["id"] for s in SCENARIOS]
        asyncio.run(run_simulation(sids))

if __name__ == "__main__":
    main()
