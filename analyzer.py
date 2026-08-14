import os
import json
import logging
from typing import Optional
from config import TRANSCRIPTS_DIR

logger = logging.getLogger(__name__)

BUG_ANALYSIS_PROMPT = """You are a quality assurance analyst for a doctor's office AI voice agent. 
Analyze the following conversation transcript between an AI agent (Agent) and a patient bot (Patient).
Identify any bugs, errors, or quality issues in the AGENT's responses.

Focus on:
1. Factual errors (wrong dates, times, medications, office hours, insurance info)
2. Hallucinations (inventing information not provided)
3. Poor handling of edge cases
4. Incorrect confirmations
5. Missing verification steps
6. Unprofessional or unclear responses

Do NOT nitpick about minor punctuation or grammar unless it affects understanding.

Return a JSON array of bugs found. Each bug should have:
- "bug": brief description of the issue
- "severity": "High", "Medium", or "Low"
- "turn": approximate turn number where it occurred (1-based)
- "detail": explanation of what happened and why it's a problem

If no bugs are found, return an empty array [].

Transcript:
{transcript}
"""

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set for bug analysis")
        from openai import AsyncOpenAI
        _client = AsyncOpenAI(api_key=api_key)
    return _client

async def analyze_transcript(transcript_path: str) -> list:
    with open(transcript_path, "r") as f:
        transcript = f.read()
    
    if not transcript.strip():
        return []
    
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a QA analyst. Return only valid JSON."},
                {"role": "user", "content": BUG_ANALYSIS_PROMPT.format(transcript=transcript)}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1000,
        )
        
        content = response.choices[0].message.content.strip()
        try:
            result = json.loads(content)
            bugs = result.get("bugs", [])
            if not isinstance(bugs, list):
                bugs = []
            return bugs
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse bug analysis JSON: {content}")
            return []
    except Exception as e:
        print(f"Bug analysis error: {e}")
        return []

async def analyze_all_transcripts() -> list:
    all_bugs = []
    
    for filename in os.listdir(TRANSCRIPTS_DIR):
        if filename.endswith(".txt"):
            path = os.path.join(TRANSCRIPTS_DIR, filename)
            bugs = await analyze_transcript(path)
            for bug in bugs:
                bug["file"] = filename
            all_bugs.extend(bugs)
    
    return all_bugs
