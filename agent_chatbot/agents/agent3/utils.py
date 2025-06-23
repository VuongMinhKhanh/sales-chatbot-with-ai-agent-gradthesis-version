import json

from langchain_core.prompts import PromptTemplate

from agent_chatbot.agents.agent3.prompts import extract_intent_prompt
from agent_chatbot.common.templates import TEMPLATES


def extract_intent(llm ,user_message: str, ai_answer: str) -> str:
    """
    Classify the user message into an archetype (called 'intent') and extract needed slots,
    then assign a confidence (0.0–1.0). Return EXACTLY JSON with keys:
      - intent: one of our archetypes
      - confidence: float

    Example output:
    {
      "intent": "technical_fit",
      "confidence": 0.87
    }
    """
    prompt_template = PromptTemplate.from_template(extract_intent_prompt)

    # Create the chain.
    chain = prompt_template | llm

    response = chain.invoke({
        "user_message": user_message,
        "ai_answer": ai_answer,
        "template_keys": ", ".join(TEMPLATES.keys())
    })
    # debug print to verify
    # print("⏺ extractor raw:", response.content)
    return json.loads(response.content)