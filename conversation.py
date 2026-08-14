import logging
from providers.llm import HybridLLM

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a patient calling a doctor's office. Stay in character as a realistic patient.
Be conversational but focused on achieving your goal. Keep responses short (1-3 sentences).
If the agent asks for information you don't have, improvise realistic details.
If the agent makes a mistake (wrong date, time, medication, etc.), politely correct them or note it for later review.
Never break character or mention that you are an AI testing the system.

IMPORTANT: Actively steer the conversation toward your goal. Don't just respond passively - guide the agent to help you with what you need."""

_hybrid_llm = None

def get_llm() -> HybridLLM:
    global _hybrid_llm
    if _hybrid_llm is None:
        _hybrid_llm = HybridLLM()
    return _hybrid_llm

async def get_response(history: list[dict], scenario: dict) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    context = f"\n\nCurrent scenario context: {scenario.get('context', '')}\nYour goal: {scenario.get('goal', 'Have a normal conversation')}\nInitial message: {scenario.get('initial_message', 'Hello?')}"
    messages[0]["content"] += context
    
    for msg in history[-10:]:
        messages.append(msg)
    
    try:
        llm = get_llm()
        response, provider = await llm.generate(messages, max_tokens=150)
        logger.info(f"LLM response from {provider}: {response[:50]}...")
        return response
    except Exception as e:
        logger.error(f"All LLM providers failed: {e}")
        return "I'm sorry, could you repeat that?"
