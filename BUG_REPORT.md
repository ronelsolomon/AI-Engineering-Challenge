# Bug Report

Generated: 2026-08-14

## Summary

| Metric | Value |
|--------|-------|
| Total calls completed | 0 (no actual calls made yet - requires API keys) |
| Total transcripts analyzed | 0 |
| Total bugs found | 0 |

> Note: This is a template bug report. Actual bug findings will be populated after running test calls with valid API keys.

## How to Generate Actual Results

1. Set up API keys in `.env`
2. Start ngrok: `python start_ngrok.py`
3. Start server: `python main.py server --port 8000`
4. Run batch: `python main.py batch --webhook-url https://<your-ngrok-url>`
5. Analyze: `python main.py analyze`

## Expected Bug Categories

Based on the scenarios designed, here are the types of bugs we're testing for:

### 1. Scheduling Errors
- Agent confirms appointment for wrong day/time
- Agent doesn't check availability before confirming
- Agent double-books appointments
- Agent doesn't send confirmation details

### 2. Medication/Pharmacy Errors
- Agent confirms wrong medication or dosage
- Agent doesn't verify refill eligibility
- Agent hallucinates prescription details
- Agent doesn't check for drug interactions

### 3. Insurance/Billing Errors
- Agent provides incorrect insurance information
- Agent doesn't verify coverage before confirming
- Agent gives wrong billing amounts
- Agent misidentifies accepted insurance plans

### 4. Edge Case Handling
- Agent can't handle interruptions or barge-in
- Agent fails to ask clarifying questions for vague requests
- Agent provides incorrect office hours (e.g., says open on weekends when closed)
- Agent doesn't transfer to human when requested
- Agent gets stuck in loops or repeats itself

### 5. Conversation Quality
- Agent uses overly formal or robotic language
- Agent doesn't confirm important details
- Agent hangs up prematurely
- Agent can't understand accents or speech patterns

## Example Bug Report Format

```markdown
### Bug: Agent confirms appointment for Sunday
**Severity**: High
**Call**: transcript-07.txt at turn 5
**Details**: When asked "Can I come in Sunday at 10am?", the agent responded, "I've scheduled you for Sunday at 10 am" without checking office hours. Should have informed the patient the office is closed on weekends and offered the next available weekdays.
```

## Simulation Mode Results

To test conversation logic without making real calls:

```bash
python main.py simulate --scenario appointment_simple
```

This simulates the conversation in the terminal and generates sample transcripts for analysis.
