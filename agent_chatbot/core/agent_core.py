import json
import time
from pprint import pprint

from agent_chatbot.agents.agent1.agent1 import Agent1
from agent_chatbot.agents.agent4.agent4 import agent4_update_user_profile
from agent_chatbot.agents.agent5.agent5 import OrderCheckoutApi
from agent_chatbot.common.deep_merge import deep_merge
from agent_chatbot.common.workflow_definitions import get_workflow_stages, get_workflow
from agent_chatbot.common.yaml_loader.api_manager import get_llms_for_agent
from langchain_core.messages import HumanMessage

from agent_chatbot.core.agent_loader import get_agent_callable
from agent_chatbot.core.utils import format_strategies_for_prompt, compact_feedback_list
from chatwoot.chatwoot_api import update_chatwoot_user, send_typing_indicator
from chatwoot.utils import handle_ai_response
from redis_store.redis_cache import store_payload


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
        print("agent_name", agent_name)
        hint       = action.get("payload", {}).get("hint")
        payload["hints"][agent_name] = hint

        # ─── REPLACE STATIC LOOKUP WITH DYNAMIC LOADER ─────────────────────────────
        # New code:
        try:
            AgentOrFunc = get_agent_callable(agent_name)
            agent_llm_clients = get_llms_for_agent(agent_name)
            print("AgentOrFunc", AgentOrFunc)
            print("agent_llm_clients", agent_llm_clients)
        except KeyError:
            response = f"Error: {agent_name} is not registered in agent_registry.yaml."
        else:
            # If the returned object is a class, instantiate & call .dispatch(...)
            print("inside the dispatch")
            if isinstance(AgentOrFunc, type):
                try:
                    print("if class")
                    agent_instance = AgentOrFunc(agent_llm_clients)              # pass any constructor args if needed
                    response = agent_instance.handle(payload)
                except TypeError as e:
                    response = f"[!] dispatch() failed for {agent_name}: {e}"
            else:
                # It’s a plain function
                try:
                    print("if def")
                    response = AgentOrFunc(agent_llm_clients, payload)
                except TypeError as e:
                    response = f"[!] function call failed for {agent_name}: {e}"
        # ─────────────────────────────────────────────────────────────────────────────

        responses.append({
            "agent": agent_name,
            "task": action["task"],
            "response": response,
        })

        # # ─── (B) Agent2 post-processing ─────────────────────────────────────────────
        # if agent_name == "Agent2":
        #     answer = response.get("answer", {}) if isinstance(response, dict) else {}
        #     json_answer = {}
        #     try:
        #         json_answer = json.loads(answer)
        #     except Exception:
        #         pass
        #
        #     result = json_answer.get("result")
        #     if result:
        #         handle_ai_response(conversation_id, result, payload["chat_history"])
        #
        #     # Merge any “additional_info” from Agent2
        #     if "additional_info" in json_answer:
        #         payload["additional_info"] = deep_merge(
        #             payload.get("additional_info", {}),
        #             json_answer["additional_info"]
        #         )
        #     print("payload after updating additional info")
        #     pprint(payload)
        #
        # # ─── (C) Agent3 post-processing ─────────────────────────────────────────────
        # if agent_name == "Agent3":
        #     followup = None
        #     if isinstance(response, dict):
        #         followup = response.get("followup", None)
        #     if followup and followup.lower() != "none":
        #         handle_ai_response(conversation_id, followup, payload["chat_history"])

        # (D) Turn off typing indicator
        send_typing_indicator(conversation_id, "off")

    return responses


def chatbot_run(user_message,
                user_profile,
                conversation_id,
                contact_id,
                payload=None
                ):
    """
    Simulate the chatbot execution workflow.

    Inputs:
      user_message: A string from the user (e.g. "Tôi muốn mua micro shure")
      chat_history: Optional list of previous conversation messages (default: empty list)

    Returns:
      A dict with agent result keys:
        - "agent1": The full result from Agent 1 (Orchestrator)
        - "agent2": The result from Agent 2 (Product Info Agent)
        - "agent3": The result from Agent 3 (Followup Agent)

      # agent1: Orchestrator output, including query_and_stage with semantic query and workflow stage.
      # agent2: Chatbot answer output (when not in Greeting stage)
      # agent3: Chatbot followup output (when not in Greeting stage)
    """
    chat_history = payload.get("chat_history", [])

    # if chat_history is None:
    #     chat_history = []

    try:
        workflow_stages = get_workflow_stages().keys()
    except Exception:
        workflow_stages = "Greeting, Needs Assessment, Qualification, Product Presentation, Objection Handling, Closing"

    total_start_time = time.time()

    # ---------------------------
    # Step 1: Agent 1 (Orchestrator)
    # ---------------------------

    # print(chat_history)
    predicted_stage = payload.get("predicted_stage", "")
    additional_info = json.dumps(payload.get("additional_info", {}), indent=2)

    # Call Agent1 for Orchestrator
    agent1 = Agent1(llm_clients=get_llms_for_agent("Agent1"))
    agent1_result, time_agent1 = agent1.handle(chat_history, predicted_stage, user_profile, user_message, workflow_stages, additional_info)

    user_message = agent1_result.get("query_and_stage").get("semantic_query")
    chat_history.append(HumanMessage(content=user_message))

    # check Agent 1 answer
    agent1_answer = agent1_result.get("query_and_stage").get("answer")
    # print("agent1_answer:", agent1_answer)
    # return

    if agent1_answer:
        print("Agent 1 answer:", agent1_answer)
        handle_ai_response(conversation_id, agent1_answer, chat_history)
        send_typing_indicator(conversation_id, "off")
        return

    # Move on to other Agents
    actions = agent1_result.get("actions", [])
    query_and_stage = agent1_result.get("query_and_stage", {})
    business_logic = agent1_result.get("retrieval_context", {}).get("business_logic", [])
    optimized_business_logic = format_strategies_for_prompt(business_logic)
    user_feedback = agent1_result.get("retrieval_context", {}).get("user_feedback", [])
    optimized_user_feedback = compact_feedback_list(user_feedback)
    additional_info = agent1_result.get("additional_info", {})
    additional_info["conversation_id"] = conversation_id

    # ---------------------------
    # Step 2: Dispatch actions to Agent 2 and Agent 3
    # ---------------------------
    new_payload = {
        "user_message": query_and_stage.get("semantic_query", ""),
        "workflow_stage": query_and_stage.get("workflow_stage", ""),
        "chat_history": chat_history,
        "business_logic": optimized_business_logic,
        "user_feedback": optimized_user_feedback,
        "user_profile": user_profile,
        "workflow_stages": workflow_stages,
        "instruction": get_workflow(query_and_stage.get("workflow_stage", "")),
        "additional_info": additional_info,
        "actions": actions,
        'apis': {'order_api': OrderCheckoutApi()},
    }

    # payload = deep_merge(previous_payload, new_payload,
    #                      ["user_message", "chat_history"],
    #                      ["additional_info", "mentioned_"])
    # payload.update(new_payload)
    payload = deep_merge(payload, new_payload)
    print("Current Payload")
    pprint(payload)
    # Dispatcher calls the functions registered.
    dispatcher(actions, payload, conversation_id)

    # Update the user profile if needed.
    updated_user_profile, time_agent4 = agent4_update_user_profile(get_llms_for_agent("Agent4"), payload)
    # print("Updated User Profile:", updated_user_profile)
    update_chatwoot_user(contact_id, updated_user_profile)
    total_end_time = time.time()
    print(f"⏱️⏱️⏱️ Total execution time: {total_end_time - total_start_time:.4f} seconds")

    # Store payload into Redis
    store_payload(conversation_id, payload,
                  ["business_logic", "user_feedback", "instruction",
                   "workflow_stages", "user_profile", "user_message", "actions"])

    return
