import asyncio
import argparse
import os
import sys
from datetime import datetime
from config import BASE_URL, CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR
from call_manager import start_call, get_recordings, download_recording
from analyzer import analyze_all_transcripts
from scenarios import SCENARIOS

def ensure_dirs():
    for d in [CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR]:
        os.makedirs(d, exist_ok=True)

async def run_scenario(scenario_id: str, webhook_url: str):
    from call_manager import start_call as do_start_call
    ensure_dirs()
    
    print(f"Starting call for scenario: {scenario_id}")
    result = do_start_call(scenario_id, webhook_url)
    call_sid = result["call_sid"]
    print(f"Call started: {call_sid}")
    
    print("Waiting for call to complete (up to 5 minutes)...")
    for i in range(60):
        await asyncio.sleep(5)
        status = get_call_status(call_sid)
        print(f"  Status: {status['status']}")
        if status["status"] in ["completed", "failed", "busy", "no-answer", "canceled"]:
            break
    
    recordings = get_recordings(call_sid)
    if recordings:
        rec_dir = os.path.join(CALLS_DIR, scenario_id, call_sid)
        os.makedirs(rec_dir, exist_ok=True)
        for i, rec in enumerate(recordings):
            dest = os.path.join(rec_dir, f"recording_{i}.mp3")
            success = download_recording(rec["sid"], dest)
            if success:
                print(f"Recording saved: {dest}")
            else:
                print(f"Failed to download recording {rec['sid']}")
    else:
        print("No recordings found for this call.")
    
    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{scenario_id}_{call_sid}.txt")
    if os.path.exists(transcript_path):
        print(f"Transcript saved: {transcript_path}")
    else:
        print(f"No transcript found at {transcript_path}")
    
    return call_sid

async def run_batch(scenario_ids: list, webhook_url: str):
    ensure_dirs()
    results = []
    for sid in scenario_ids:
        try:
            call_sid = await run_scenario(sid, webhook_url)
            results.append({"scenario_id": sid, "call_sid": call_sid, "status": "completed"})
        except Exception as e:
            print(f"Error running scenario {sid}: {e}")
            results.append({"scenario_id": sid, "call_sid": None, "status": "error", "error": str(e)})
        await asyncio.sleep(10)
    
    print("\n=== Batch Run Summary ===")
    for r in results:
        print(f"  {r['scenario_id']}: {r['status']}")
    
    return results

async def run_analysis():
    ensure_dirs()
    print("Analyzing transcripts for bugs...")
    bugs = await analyze_all_transcripts()
    print(f"Found {len(bugs)} potential bugs.")
    
    report_path = os.path.join(os.path.dirname(__file__), "BUG_REPORT.md")
    with open(report_path, "w") as f:
        f.write("# Bug Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("## Summary\n\n")
        f.write(f"Total calls analyzed: {len(os.listdir(TRANSCRIPTS_DIR))}\n")
        f.write(f"Total bugs found: {len(bugs)}\n\n")
        f.write("## Bugs Found\n\n")
        
        for i, bug in enumerate(bugs, 1):
            f.write(f"### Bug {i}\n")
            f.write(f"- **Bug**: {bug.get('bug', 'Unknown')}\n")
            f.write(f"- **Severity**: {bug.get('severity', 'Unknown')}\n")
            f.write(f"- **Call/Transcript**: {bug.get('file', 'Unknown')}\n")
            f.write(f"- **Detail**: {bug.get('detail', 'No details')}\n\n")
    
    print(f"Bug report saved to {report_path}")
    return bugs

def main():
    parser = argparse.ArgumentParser(description="Voice Bot Tester")
    parser.add_argument("command", choices=["call", "batch", "analyze", "server", "simulate", "sim-batch"], help="Command to run")
    parser.add_argument("--scenario", default="appointment_simple", help="Scenario ID for single call")
    parser.add_argument("--scenarios", nargs="*", help="Scenario IDs for batch run")
    parser.add_argument("--webhook-url", default=BASE_URL, help="Public webhook URL")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    if args.command == "server":
        import uvicorn
        from server import app
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    
    elif args.command == "call":
        asyncio.run(run_scenario(args.scenario, args.webhook_url))
    
    elif args.command == "batch":
        sids = args.scenarios or [s["id"] for s in SCENARIOS]
        asyncio.run(run_batch(sids, args.webhook_url))
    
    elif args.command == "analyze":
        asyncio.run(run_analysis())
    
    elif args.command == "simulate":
        from simulate import simulate_scenario
        asyncio.run(simulate_scenario(args.scenario))
    
    elif args.command == "sim-batch":
        from simulate import run_simulation
        sids = args.scenarios or [s["id"] for s in SCENARIOS]
        asyncio.run(run_simulation(sids))

if __name__ == "__main__":
    main()
