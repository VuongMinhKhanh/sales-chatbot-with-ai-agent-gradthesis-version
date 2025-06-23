import time
# from bootstrap import initialize_system
from chatbot.agent_registry import agent_registry, load_all_agents_and_controller
from chatbot.agents.agent1 import agent1_dispatch_agents
from chatbot.agents.agent5 import DummyOrderApi
from chatbot.agent_utils import handle_ai_response
from chatbot.utils import format_strategies_for_prompt, compact_feedback_list
from chatbot.workflow_definitions import get_workflow_stages, get_workflow
from chatwoot.chatwoot_api import send_typing_indicator
from tests.test_yaml import force_load_services


def dispatcher(actions_list, payload, conversation_id):
    responses = []
    load_all_agents_and_controller()

    if "chat_history" not in payload or not isinstance(payload["chat_history"], list):
        payload["chat_history"] = []

    # carry a dict of hints per agent
    payload.setdefault("hints", {})

    # Loop through each action and dynamically call the corresponding function
    for action in actions_list:
        # time_consumed = None
        agent_name = action["agent"]
        hint = action.get("payload", {}).get("hint")

        # stash this action’s hint under payload["hints"]
        payload["hints"][agent_name] = hint

        # Retrieve the agent function from the registry
        agent_function = agent_registry.get(agent_name)
        if agent_function is not None:
            (response
                 # , time_consumed
             ) = agent_function(payload)
        else:
            response = f"Error: {agent_name} is not registered."
        responses.append({
            "agent": agent_name,
            "task": action["task"],
            "response": response,
            # "time_consumed": time_consumed
        })
        print("response", response)
        # get answers from each agent, will fix for more dynamic
        answer = response.get("answer", None)
        if answer:
            handle_ai_response(conversation_id, answer, payload["chat_history"])

        followup = response.get("followup", None)
        if followup and followup.lower() != "none":
            handle_ai_response(conversation_id, followup, payload["chat_history"])

        # ❌ Disable Typing Indicator
        send_typing_indicator(conversation_id, "off")

    return responses

# %%

import importlib
import tests.test_yaml as ty

# importlib.reload(ty)
# importlib.reload(agent_registry)
# initialize_system()
# register_agents_config()
# %%
def chatbot_run(user_message,
                user_profile,
                predicted_stage,
                conversation_id,
                contact_id,
                chat_history=None
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
    if chat_history is None:
        chat_history = []

    try:
        workflow_stages = get_workflow_stages().keys()
    except Exception:
        workflow_stages = "Greeting, Needs Assessment, Qualification, Product Presentation, Objection Handling, Closing"

    total_start_time = time.time()

    # ---------------------------
    # Step 1: Agent 1 (Orchestrator)
    # ---------------------------

    # load_all_agents()
    # print(chat_history)
    agent1_result, time_agent1 = agent1_dispatch_agents(chat_history, predicted_stage, user_profile, user_message, workflow_stages)

    # check Agent 1 answer
    agent1_answer = agent1_result.get("query_and_stage").get("answer")
    # print("agent1_answer:", agent1_answer)
    # return

    if agent1_answer:
        print("Agent 1 answer:", agent1_answer)
        handle_ai_response(conversation_id, agent1_answer, chat_history)
        return

    # Move on to other Agents
    actions = agent1_result.get("actions", [])
    query_and_stage = agent1_result.get("query_and_stage", {})
    business_logic = agent1_result.get("retrieval_context", {}).get("business_logic", [])
    optimized_business_logic = format_strategies_for_prompt(business_logic)
    user_feedback = agent1_result.get("retrieval_context", {}).get("user_feedback", [])
    optimized_user_feedback = compact_feedback_list(user_feedback)
    additional_info = agent1_result.get("additional_info", {})

    # ---------------------------
    # Step 2: Dispatch actions to Agents
    # ---------------------------
    payload = {
        "user_message": query_and_stage.get("semantic_query", ""),
        "workflow_stage": query_and_stage.get("workflow_stage", ""), "chat_history": chat_history,
        "business_logic": optimized_business_logic, "user_feedback": optimized_user_feedback,
        "user_profile": user_profile, "workflow_stages": workflow_stages,
        "instruction": get_workflow(query_and_stage.get("workflow_stage", "")), "apis": {
            "order_api": DummyOrderApi()  # matches manifest client key
        },
        "additional_info": additional_info,
        "actions": actions,
    }

    print("payload", payload)
    # payload = {'cart': ['loa này'], 'customer_info': {'customer_name': 'Khánh', 'customer_phone': '0909933916'},
    #            'user_message': 'Tôi muốn đặt mua loa này, tên Khánh, số điện thoại: 0909933916',
    #            'workflow_stage': 'Needs Assessment', 'chat_history': [],
    #            'business_logic': '1. rule-004:\n   When a user mentions or asks about a product with a specific price (X), any alternative or upsell recommendation should fall within a reasonable price range around X, based on customer intent.\n\n2. rule-001:\n   If user asks about a product, recommend discounted items and ask about intended usage.',
    #            'user_feedback': '🧾 tôi muốn mua loa bose 101 mexico\n❌ Xin lỗi, tôi không thể cung cấp thông tin vì context không nói rõ về nơi bạn có thể mua loa Bose 101 Mexico.\n🛠 Khi khách hàng nói muốn mua, bạn ko cần phải xem xét khả năng thực sự mua ở đâu, mà là những thông tin cần thiết để mua, như giá, thời gian bảo hàng.\n✅ Vâng, bên chúng tôi có bán loa bose 101 mexico, với giá là <giá> và thời gian bảo hành là <thời gian bảo hành> tháng <và các thông tin cần thiết khác nếu bạn thấy chúng phù hợp>\n\n---\n\n🧾 Anh đã mua loa JBL Eon 712 Loa liền công suất, Thấy quảng cáo khuyến mãi amplifiers, Tư vấn đầu tư thêm gì để có bộ Karaoke tốt hơn không ?\n❌ Tôi không biết\n🛠 Bạn tuyệt đối không được trả lời "Tôi không biết" hay các câu trả lời cụt ngủn như vậy được.\n✅ Dạ, tôi không biết phải hỗ trợ bạn như thế nào. Bạn có thể tư vấn nhân viên kỹ thuật của 769audio tại SĐT: <SĐT>\n\n---\n\n🧾 tôi muốn mua loa bose 101 mexico\n❌ Loa Bose 101 Mexico bạn muốn mua là hàng cũ đã qua sử dụng vì hiện nay hãng Bose không còn sản xuất model này nữa. Giá của loa Bose 101 Mexico là 2,900,000 VND và sản phẩm bảo hành trong 02 tháng.\n🛠 Khi bạn báo giá, bạn nên hỏi là "giá bên chúng tôi" hãy "giá bán của cửa hàng 769audio".\n✅ Vâng, Loa Bose 101 chúng tôi có giá là <giá sản phẩm>',
    #            'user_profile': '', 'workflow_stages': workflow_stages,
    #            'instruction': 'Đặt câu hỏi trọng tâm để khám phá nhu cầu...',
    #            'apis': {'order_api': DummyOrderApi()  }}
    # actions = [
    #     {
    #         "agent": "Agent5",
    #         "task": "process_task",
    #         "payload": {
    #             "hint": "<nội dung để Agent2 hoặc Agent3 hoặc Agent5 xử lý>"
    #         }
    #     }
    # ]
    # import importlib
    # import chatbot.agents.agent5 as agent5
    #
    # importlib.reload(agent5)
    # load_all_agents()

    # Dispatcher calls the functions registered.
    dispatcher(actions, payload, conversation_id)
    #
    # # Update the user profile if needed.
    # updated_user_profile, time_agent4 = agent4_update_user_profile(payload)
    # print("Updated User Profile:", updated_user_profile)
    # update_chatwoot_user(contact_id, updated_user_profile)
    # total_end_time = time.time()
    # print(f"⏱️⏱️⏱️ Total execution time: {total_end_time - total_start_time:.4f} seconds")
    print("actions:", actions)
    return


chatbot_result = chatbot_run("Tôi muốn đặt mua loa này, tên Khánh, số điện thoại: 0909933916",
                             "", "", 0, 0, [])
