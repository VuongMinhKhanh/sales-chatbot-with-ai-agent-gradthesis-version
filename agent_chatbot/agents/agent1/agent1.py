import json, time
from pprint import pprint
from typing import Dict, Any

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent_chatbot.agents.agent1.prompts import agent1_prompt
from agent_chatbot.common.workflow_definitions import get_workflow_identify
from agent_chatbot.services.vectorstore import retrieve_context_sync
from chatbot.utils import render_agent_list_and_prompt


class Agent1:
    def __init__(self, llm_clients: Dict[str, Any], config: Dict[str, Any] = None):
        self.llms = llm_clients
        self.config = config

    # agent1_dispatch_agents
    def handle(self,
               chat_history,
               predicted_stage: str,
               user_profile: str,
               user_query: str,
               workflow_identify: str = None,
               additional_info: dict = {},
               top_k=3):
        """
        Chạy Agent 1:
        - Gọi LLM sinh JSON kết quả
        - Truy vấn context bổ sung
        - Trả về JSON hoàn chỉnh
        """

        if workflow_identify is None:
            "Greeting, Needs Assessment, Qualification, Presentation, Objection Handling, Closing, Follow-Up"

        workflow_identify = get_workflow_identify()
        workflow_identify = "\n".join([
            f"- {stage}: {info['identify']}"
            for stage, info in workflow_identify.items()
        ])

        # 1. Build prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", agent1_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "User Message: {user_query}"),
            ("human", "Customer Profile: {user_profile}"),
            ("ai", "Workflow Stages: {workflow_identify}"),
            ("ai", "Predicted Stage: {predicted_stage}"),
            ("ai", "Specialist Agents: {agent_list_block}"),
            ("ai", "Additional Info as JSON: ```json\n{additional_info}")
        ])

        # 2. Create LLM instance
        llm_agent1_dispatch = self.llms["generic_json"]

        chain = prompt_template | llm_agent1_dispatch

        # 3. Invoke LLM
        start = time.time()
        response_text = chain.invoke({
            "user_query": user_query,
            "predicted_stage": predicted_stage,
            "user_profile": user_profile,
            "chat_history": chat_history,
            "workflow_identify": workflow_identify,
            "agent_list_block": render_agent_list_and_prompt(),
            "additional_info": additional_info,
        })

        # print("response_text:", response_text)

        # 4. Parse JSON
        parsed_json = json.loads(response_text.content)
        # print("parsed_json", parsed_json)

        # 5. Đồng bộ truy vấn retrieval context
        semantic_query = parsed_json.get('query_and_stage', {}).get('semantic_query')
        workflow_stage = parsed_json.get('query_and_stage', {}).get('workflow_stage')
        retrieval_context = retrieve_context_sync(semantic_query, workflow_stage, top_k)

        # 6. Gắn thêm vào kết quả
        parsed_json['retrieval_context'] = retrieval_context

        end = time.time()
        print(f"⏱️ Time taken Agent 1: {end - start:.4f}s")
        return parsed_json, float(f"{end - start:.4f}")


if __name__ == "__main__":
    pass
    # chat_history = []
    # predicted_stage = ""
    # user_profile = ""
    # user_query = "Tôi muốn mua loa bose nghe nhạc này, đặt hàng loa này cho tôi đi. Tên khánh, sdt: 0909090909",
    # workflow_identify = None,
    # additional_info: dict = {
    #     'additional_info': {
    #                 'mentioned_products': [
    #                     {'product_id': 3, 'product_name': 'Loa Nghe nhạc bose 301', 'product_price': 1000000},
    #                     {'product_id': 2, 'product_name': 'Loa Micro suhyoung 909', 'product_price': 1000000},
    #                     {'product_id': 1, 'product_name': 'Loa kẹo kéo partybox', 'product_price': 1000000},
    #                 ],
    #             }
    # }
    #
    # agent1_result, _ = agent1_dispatch_agents(
    #     chat_history,
    #     predicted_stage,
    #     user_profile,
    #     user_query,
    #     None,
    #     additional_info
    # )
    #
    # pprint(agent1_result)
