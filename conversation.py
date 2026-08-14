from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a patient calling a doctor's office. Stay in character as a realistic patient.
Be conversational but focused on achieving your goal. Keep responses short (1-3 sentences).
If the agent asks for information you don't have, improvise realistic details.
If the agent makes a mistake (wrong date, time, medication, etc.), politely correct them or note it for later review.
Never break character or mention that you are an AI testing the system.

IMPORTANT: Actively steer the conversation toward your goal. Don't just respond passively - guide the agent to help you with what you need."""

async def get_response(history: list[dict], scenario: dict) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    context = f"\n\nCurrent scenario context: {scenario.get('context', '')}\nYour goal: {scenario.get('goal', 'Have a normal conversation')}\nInitial message: {scenario.get('initial_message', 'Hello?')}"
    messages[0]["content"] += context
    
    for msg in history[-10:]:
        messages.append(msg)
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM error: {e}")
        return "I'm sorry, could you repeat that?"
