import json
import time
from pprint import pprint
from typing import Dict, Any

from agent_chatbot.agents.agent2.rag import initialize_rag
from agent_chatbot.common.deep_merge import deep_merge
from chatwoot.utils import handle_ai_response


class Agent2:
    def __init__(self, llm_clients: Dict[str, Any], config: Dict[str, Any] = None):
        self.llms = llm_clients
        self.config = config

        # # 1) Ask PromptManager for compiled templates for "Agent2"
        # prompts = PromptManager.get_prompts_for("agent2")
        # self.system_tmpl   = prompts["system_tmpl"]
        # self.few_shot_pairs= prompts["few_shot_pairs"]
        # self.response_tmpl = prompts["response_tmpl"]

    # agent2_retrieve_product_info
    def handle(self, payload):
        # Extract parameters from the payload dictionary.
        user_message = payload.get("user_message", "")
        chat_history = payload.get("chat_history", [])
        business_logic = payload.get("business_logic", [])
        user_profile = payload.get("user_profile", "")
        workflow_stage = payload.get("workflow_stage", "Needs Assessment")
        user_feedback = payload.get("user_feedback", "")
        instruction = payload.get("instruction", "")
        agent2_hint = payload.get("hints", {}).get("Agent2", "")
        contextualized_query = payload.get("contextualized_query", "")
        # print("agent2_hint", agent2_hint)

        start = time.time()
        # Invoke the RAG system using the extracted parameters.
        # Note: Replace 'rag.invoke' with your actual RAG system call.
        rag = initialize_rag(self.llms)
        result = rag.invoke({
            "input": user_message,
            "chat_history": chat_history,
            "business_logic": business_logic,
            "user_profile": user_profile,
            "workflow_stage": workflow_stage,
            "instruction": instruction,
            "user_feedback": user_feedback,
            "agent2_hint": agent2_hint,
            "contextualized_query": contextualized_query
        })
        end = time.time()
        print(f"⏱️ Time taken - agent 2: {end - start:.4f} seconds")
        print("agent 2 answer:", result["answer"])

        # send chatwoot
        conversation_id = payload["additional_info"]["conversation_id"]
        json_answer = json.loads(result["answer"])
        ai_response = json_answer.get("result")

        handle_ai_response(conversation_id, ai_response, chat_history)

        # Merge any “additional_info” from Agent2
        if "additional_info" in json_answer:
            payload["additional_info"] = deep_merge(
                payload.get("additional_info", {}),
                json_answer["additional_info"]
            )
        print("payload after updating additional info")
        pprint(payload)

        return (result
                # , float(f"{end - start:.4f}")
                )

# if __name__ == "__main__":
#     workflow_stages = "Greeting, Needs Assessment, Qualification, Product Presentation, Objection Handling, Closing"
#
#     payload = {'cart': ['loa này'], 'customer_info': {'customer_name': 'Khánh', 'customer_phone': '0909933916'},
#                'user_message': 'Tư vấn cho tôi loa nghe nhạc dưới 3tr',
#                'workflow_stage': 'Needs Assessment', 'chat_history': [],
#                'business_logic': '1. rule-004:\n   When a user mentions or asks about a product with a specific price (X), any alternative or upsell recommendation should fall within a reasonable price range around X, based on customer intent.\n\n2. rule-001:\n   If user asks about a product, recommend discounted items and ask about intended usage.',
#                'user_feedback': '🧾 tôi muốn mua loa bose 101 mexico\n❌ Xin lỗi, tôi không thể cung cấp thông tin vì context không nói rõ về nơi bạn có thể mua loa Bose 101 Mexico.\n🛠 Khi khách hàng nói muốn mua, bạn ko cần phải xem xét khả năng thực sự mua ở đâu, mà là những thông tin cần thiết để mua, như giá, thời gian bảo hàng.\n✅ Vâng, bên chúng tôi có bán loa bose 101 mexico, với giá là <giá> và thời gian bảo hành là <thời gian bảo hành> tháng <và các thông tin cần thiết khác nếu bạn thấy chúng phù hợp>\n\n---\n\n🧾 Anh đã mua loa JBL Eon 712 Loa liền công suất, Thấy quảng cáo khuyến mãi amplifiers, Tư vấn đầu tư thêm gì để có bộ Karaoke tốt hơn không ?\n❌ Tôi không biết\n🛠 Bạn tuyệt đối không được trả lời "Tôi không biết" hay các câu trả lời cụt ngủn như vậy được.\n✅ Dạ, tôi không biết phải hỗ trợ bạn như thế nào. Bạn có thể tư vấn nhân viên kỹ thuật của 769audio tại SĐT: <SĐT>\n\n---\n\n🧾 tôi muốn mua loa bose 101 mexico\n❌ Loa Bose 101 Mexico bạn muốn mua là hàng cũ đã qua sử dụng vì hiện nay hãng Bose không còn sản xuất model này nữa. Giá của loa Bose 101 Mexico là 2,900,000 VND và sản phẩm bảo hành trong 02 tháng.\n🛠 Khi bạn báo giá, bạn nên hỏi là "giá bên chúng tôi" hãy "giá bán của cửa hàng 769audio".\n✅ Vâng, Loa Bose 101 chúng tôi có giá là <giá sản phẩm>',
#                'user_profile': '', 'workflow_stages': workflow_stages,
#                'instruction': 'Đặt câu hỏi trọng tâm để khám phá nhu cầu...',
#                "hints": {}
#                }
#
#     agent2_result = agent2_retrieve_product_info(payload)
#     pprint(agent2_result)
