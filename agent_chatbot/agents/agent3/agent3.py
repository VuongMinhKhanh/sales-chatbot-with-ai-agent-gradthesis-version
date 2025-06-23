import json
import time
from typing import Dict, Any

from langchain.prompts import PromptTemplate

from agent_chatbot.agents.agent3.prompts import agent3_followup_prompt
from agent_chatbot.agents.agent3.utils import extract_intent
from agent_chatbot.common.templates import TEMPLATES
from chatwoot.utils import handle_ai_response


class Agent3:
    def __init__(self, llm_clients: Dict[str, Any], config: Dict[str, Any] = None):
        self.llms = llm_clients
        self.config = config

    # agent3_generate_followup
    def handle(self, payload):
        print("im in the agent3 handle")
        # Extract parameters from the payload dictionary.
        user_message   = payload.get("user_message", "")
        chat_history   = payload.get("chat_history", "")
        business_logic = payload.get("business_logic", "")
        user_profile   = payload.get("user_profile", "")
        workflow_stage = payload.get("workflow_stage", "Needs Assessment")
        instruction    = payload.get("instruction", "")
        workflow_stages = payload.get("workflow_stages", "")
        ai_answer      = payload.get(chat_history[-1].content, "")
        agent3_hint    = payload.get("hints", {}).get("Agent3", "")

        # Classify followup template branches
        generic_json_llm = self.llms["generic_json"]
        extracted_intent = extract_intent(generic_json_llm, user_message, ai_answer)
        print("extracted_intent", extracted_intent)
        followup_template = TEMPLATES.get(extracted_intent.get("intent", ""), "")

        # Create a prompt template.
        prompt_template = PromptTemplate.from_template(agent3_followup_prompt)

        # Create the chain.
        followup_llm = self.llms["followup"]
        print("followup llm", followup_llm)
        chain = prompt_template | followup_llm

        start = time.time()
        # Invoke the chain with the input data.
        result = chain.invoke({
             "user_message": user_message,  # Using the user_message as the query.
             "chat_history": chat_history,
             "business_logic": business_logic,
             "user_profile": user_profile,
             "workflow_stage": workflow_stage,
             "instruction": instruction,
             "workflow_stages": workflow_stages,
             "ai_answer": ai_answer,
             "followup_template": followup_template,
             "agent3_hint": agent3_hint
        })
        end = time.time()
        print(f"⏱️ Time taken - agent 3: {end - start:.4f} seconds")

        content = json.loads(result.content)
        ai_followup = content.get("followup", "")
        print("Agent 3 followup:", ai_followup)

        # send chatwoot
        conversation_id = payload["additional_info"]["conversation_id"]
        handle_ai_response(conversation_id, ai_followup, chat_history)

        return content