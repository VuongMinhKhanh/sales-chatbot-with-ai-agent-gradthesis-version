import json
import time
from pprint import pprint

from langchain_core.messages import HumanMessage

from agent_chatbot.core.agent_loader import get_agent_callable
# → REMOVE this line:
# from chatbot.agent_registry import agent_registry

# → ADD these two lines so you can dynamically load any agent:

# You can still keep these if you want to call Agent1/Agent4/Agent5 explicitly—or remove them entirely
# if you prefer to load them via get_agent_callable(...) as well:
# from chatbot.agents.agent1 import agent1_dispatch_agents
# from chatbot.agents.agent4 import agent4_update_user_profile
# from chatbot.agents.agent5 import OrderCheckoutApi

from chatbot.agent_utils import handle_ai_response
from chatbot.utils import format_strategies_for_prompt, compact_feedback_list
from chatbot.workflow_definitions import get_workflow_stages, get_workflow
from chatwoot.chatwoot_api import update_chatwoot_user, send_typing_indicator
from redis_store.redis_cache import store_payload
from tests.test_merge_payload import deep_merge

def dispatcher(actions_list, payload, conversation_id):
    responses = []

    if "chat_history" not in payload or not isinstance(payload["chat_history"], list):
        payload["chat_history"] = []

    # carry a dict of hints per agent
    payload.setdefault("hints", {})

    for action in actions_list:
        # (A) Turn on typing indicator
        send_typing_indicator(conversation_id, "on")

        agent_name = action["agent"]
        hint       = action.get("payload", {}).get("hint")
        payload["hints"][agent_name] = hint

        # ─── REPLACE STATIC LOOKUP WITH DYNAMIC LOADER ─────────────────────────────
        # Old code:
        #     agent_function = agent_registry.get(agent_name)
        #     if agent_function is not None:
        #         response = agent_function(payload)
        #     else:
        #         response = f"Error: {agent_name} is not registered."
        #
        # New code:
        try:
            AgentOrFunc = get_agent_callable(agent_name)
        except KeyError:
            response = f"Error: {agent_name} is not registered in agent_registry.yaml."
        else:
            # If the returned object is a class, instantiate & call .dispatch(...)
            if isinstance(AgentOrFunc, type):
                try:
                    agent_instance = AgentOrFunc()              # pass any constructor args if needed
                    response = agent_instance.dispatch(payload)
                except TypeError as e:
                    response = f"[!] dispatch() failed for {agent_name}: {e}"
            else:
                # It’s a plain function
                try:
                    response = AgentOrFunc(payload)
                except TypeError as e:
                    response = f"[!] function call failed for {agent_name}: {e}"
        # ─────────────────────────────────────────────────────────────────────────────

        responses.append({
            "agent": agent_name,
            "task": action["task"],
            "response": response,
        })

        # ─── (B) Agent2 post-processing ─────────────────────────────────────────────
        if agent_name == "Agent2":
            answer = response.get("answer", {}) if isinstance(response, dict) else {}
            json_answer = {}
            try:
                json_answer = json.loads(answer)
            except Exception:
                pass

            result = json_answer.get("result")
            if result:
                handle_ai_response(conversation_id, result, payload["chat_history"])

            # Merge any “additional_info” from Agent2
            if "additional_info" in json_answer:
                payload["additional_info"] = deep_merge(
                    payload.get("additional_info", {}),
                    json_answer["additional_info"]
                )
            print("payload after updating additional info")
            pprint(payload)

        # ─── (C) Agent3 post-processing ─────────────────────────────────────────────
        if agent_name == "Agent3":
            followup = None
            if isinstance(response, dict):
                followup = response.get("followup", None)
            if followup and followup.lower() != "none":
                handle_ai_response(conversation_id, followup, payload["chat_history"])

        # (D) Turn off typing indicator
        send_typing_indicator(conversation_id, "off")

    return responses

