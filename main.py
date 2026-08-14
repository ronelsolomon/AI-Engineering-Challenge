import asyncio
import argparse
import os
import sys
from datetime import datetime
from config import BASE_URL, CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR, SERVER_PORT
from scenarios import SCENARIOS
from providers.llm import HybridLLM
from providers.tts import HybridTTS
from providers.tunnel import HybridTunnel

def ensure_dirs():
    for d in [CALLS_DIR, TRANSCRIPTS_DIR, AUDIO_DIR]:
        os.makedirs(d, exist_ok=True)

def print_status():
    print("=" * 60)
    print("VOICE BOT TESTER - PROVIDER STATUS")
    print("=" * 60)
    
    print("\n[LLM Providers]")
    try:
        llm = HybridLLM()
        for p in llm.providers:
            print(f"  [{'FREE' if p.is_free() else 'PAID'}] {p.get_name()}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print("\n[TTS Providers]")
    try:
        tts = HybridTTS()
        for p in tts.providers:
            print(f"  [{'FREE' if p.is_free() else 'PAID'}] {p.get_name()}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print("\n[Tunnel Providers]")
    tunnel = HybridTunnel()
    for p in tunnel.providers:
        print(f"  [{'FREE' if p.is_free() else 'PAID'}] {p.get_name()}")
    
    print("\n" + "=" * 60)

async def run_validate(webhook_url: str):
    print("=" * 60)
    print("PRE-CALL VALIDATION")
    print("=" * 60)
    errors = []
    
    print("\n[1/5] Checking Twilio credentials...")
    from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    if not TWILIO_ACCOUNT_SID or TWILIO_ACCOUNT_SID == "your_account_sid":
        errors.append("TWILIO_ACCOUNT_SID not set")
    if not TWILIO_AUTH_TOKEN or TWILIO_AUTH_TOKEN == "your_auth_token":
        errors.append("TWILIO_AUTH_TOKEN not set")
    if not TWILIO_PHONE_NUMBER or TWILIO_PHONE_NUMBER == "your_twilio_number":
        errors.append("TWILIO_PHONE_NUMBER not set")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print(f"  OK - Account: {TWILIO_ACCOUNT_SID[:6]}... Number: {TWILIO_PHONE_NUMBER}")
    
    print("\n[2/5] Checking LLM providers...")
    try:
        llm = HybridLLM()
        if not llm.providers:
            errors.append("No LLM providers configured")
            print("  ERROR: No LLM providers configured")
        else:
            for p in llm.providers:
                print(f"  OK - {p.get_name()} ({'FREE' if p.is_free() else 'PAID'})")
    except Exception as e:
        errors.append(f"LLM error: {e}")
        print(f"  ERROR: {e}")
    
    print("\n[3/5] Checking TTS providers...")
    try:
        tts = HybridTTS()
        if not tts.providers:
            errors.append("No TTS providers available")
            print("  ERROR: No TTS providers available")
        else:
            for p in tts.providers:
                print(f"  OK - {p.get_name()} ({'FREE' if p.is_free() else 'PAID'})")
    except Exception as e:
        errors.append(f"TTS error: {e}")
        print(f"  ERROR: {e}")
    
    print("\n[4/5] Checking server accessibility...")
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{webhook_url}/", timeout=5)
            if resp.status_code == 200:
                print(f"  OK - Server reachable at {webhook_url}")
            else:
                errors.append(f"Server returned status {resp.status_code}")
                print(f"  ERROR: Server returned {resp.status_code}")
    except Exception as e:
        errors.append(f"Cannot reach server: {e}")
        print(f"  ERROR: {e}")
    
    print("\n[5/5] Checking Twilio phone number...")
    try:
        from twilio.rest import Client
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        number = client.incoming_phone_numbers.list(phone_number=TWILIO_PHONE_NUMBER)
        if number:
            print(f"  OK - {TWILIO_PHONE_NUMBER} is active in your Twilio account")
        else:
            errors.append(f"{TWILIO_PHONE_NUMBER} not found in Twilio account")
            print(f"  ERROR: {TWILIO_PHONE_NUMBER} not found")
    except ImportError:
        errors.append("twilio package not installed. Run: pip install twilio")
        print("  ERROR: twilio package not installed")
    except Exception as e:
        errors.append(f"Twilio auth error: {e}")
        print(f"  ERROR: {e}")
    
    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED - {len(errors)} error(s) found:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("ALL CHECKS PASSED - Ready to make calls!")
        return True

async def run_dry_run(scenario_id: str, webhook_url: str):
    print("=" * 60)
    print(f"DRY RUN - Scenario: {scenario_id}")
    print("=" * 60)
    
    from scenarios import SCENARIOS
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), SCENARIOS[0])
    
    print(f"\nScenario: {scenario['name']}")
    print(f"Goal: {scenario['goal']}")
    print(f"Context: {scenario['context']}")
    
    print("\n--- Simulating conversation ---")
    history = []
    turn = 0
    max_turns = 5
    
    agent_opening = "Thank you for calling Dr. Smith's office. How can I help you today?"
    print(f"\nAgent: {agent_opening}")
    history.append({"role": "user", "content": agent_opening})
    
    while turn < max_turns:
        turn += 1
        try:
            from conversation import SYSTEM_PROMPT, get_llm
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            context = f"\n\nCurrent scenario context: {scenario.get('context', '')}\nYour goal: {scenario.get('goal', 'Have a normal conversation')}\nInitial message: {scenario.get('initial_message', 'Hello?')}"
            messages[0]["content"] += context
            for msg in history[-10:]:
                messages.append(msg)
            
            response, provider = await get_llm().generate(messages, max_tokens=150)
            print(f"\nPatient (via {provider}): {response}")
            history.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"\nPatient: [ERROR - all LLM providers failed: {e}]")
            break
        
        agent_response = input("\nAgent response (or 'quit' to end): ").strip()
        if agent_response.lower() in ['quit', 'exit', 'end']:
            print("Ending dry run.")
            break
        print(f"Agent: {agent_response}")
        history.append({"role": "user", "content": agent_response})
    
    print(f"\n--- Dry run complete ({turn} turns) ---")
    print("No Twilio charges were incurred.")
    return history

async def run_tunnel(port: int):
    tunnel = HybridTunnel()
    print("Starting tunnel...")
    url = await tunnel.start(port)
    print(f"\nTunnel URL: {url}")
    print(f"Server URL: http://localhost:{port}")
    print("\nPress Ctrl+C to stop the tunnel")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping tunnel...")
        await tunnel.stop()
        print("Tunnel stopped.")

async def run_scenario(scenario_id: str, webhook_url: str):
    from call_manager import start_call as do_start_call, get_call_status, get_recordings, download_recording
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
    
    print("Waiting for recordings to process...")
    recordings = []
    for i in range(12):
        recordings = get_recordings(call_sid)
        if recordings:
            break
        await asyncio.sleep(5)
        print(f"  Checking recordings... ({i+1}/12)")
    
    if recordings:
        rec_dir = os.path.join(CALLS_DIR, scenario_id, call_sid)
        os.makedirs(rec_dir, exist_ok=True)
        for i, rec in enumerate(recordings):
            dest = os.path.join(rec_dir, f"recording_{i}.mp3")
            success = download_recording(rec["sid"], dest)
            if success:
                print(f"Recording saved: {dest} ({rec.get('duration', '?')}s)")
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
    parser.add_argument("command", choices=["call", "batch", "analyze", "server", "simulate", "sim-batch", "tunnel", "status", "validate", "dry-run"], help="Command to run")
    parser.add_argument("--scenario", default="appointment_simple", help="Scenario ID for single call")
    parser.add_argument("--scenarios", nargs="*", help="Scenario IDs for batch run")
    parser.add_argument("--webhook-url", default=BASE_URL, help="Public webhook URL")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    if args.command == "status":
        print_status()
    
    elif args.command == "validate":
        asyncio.run(run_validate(args.webhook_url))
    
    elif args.command == "dry-run":
        asyncio.run(run_dry_run(args.scenario, args.webhook_url))
    
    elif args.command == "server":
        import uvicorn
        from server import app
        print(f"Starting server on port {args.port}")
        print(f"Webhook URL: {BASE_URL}")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    
    elif args.command == "tunnel":
        asyncio.run(run_tunnel(args.port))
    
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
