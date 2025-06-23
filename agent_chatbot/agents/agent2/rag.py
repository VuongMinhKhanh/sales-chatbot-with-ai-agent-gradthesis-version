import json
from typing import Dict, Any

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent_chatbot.agents.agent2.prompts import agent2_response_prompt, information_replacement, \
    negativity_avoiding_prompt, agent2_contextualizing_prompt
from agent_chatbot.common.yaml_loader.api_manager import get_api_client
from agent_chatbot.common.yaml_loader.setting_manager import get_setting
from agent_chatbot.services.vectorstore import retrieve_and_combine_documents, get_retriever

_rag_chain = None

def initialize_rag(llm_clients: Dict[str, Any]):
    global _rag_chain
    if _rag_chain is None:
        def wrapped_retriever(input_data):
            input_query = input_data.content
            # print("input_query:", input_query)
            input_query = json.loads(input_query)
            primary_query = input_query["primary"]
            secondary_query = input_query["secondary"]
            full_contextualized_query = input_query["full_contextualized_query"]

            global _contextualized_query
            _contextualized_query = full_contextualized_query

            return retrieve_and_combine_documents(
                primary_query,
                secondary_query,
                get_retriever(),
                get_api_client("docsearch"),
                get_setting("weaviate_vectorstore")["class_name"]
            )

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", agent2_contextualizing_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                ("ai", "📊 Nghiệp vụ doanh nghiệp: {business_logic}"),
                ("ai", "📊 Phản hồi người dùng: {user_feedback}"),
                ("ai", "🧑‍💼 Mô tả khách hàng: {user_profile}")
            ]
        )

        # Create a history-aware retriever using the custom wrapped retriever
        history_aware_retriever = contextualize_q_prompt | llm_clients["contextualization"] | wrapped_retriever

        # Define the data structure.
        # class MentionedProducts(BaseModel):
        #     product_id: int = Field(description="ID")
        #     product_name: str =  Field(description="Tên sản phẩm")
        #     product_price: float = Field(description="Giá")
        #
        # class Agent2ResponseFormat(BaseModel):
        #     result: str = Field(description="Here is your answer")
        #     mentioned_products: List[MentionedProducts] = Field(description="")
        #
        # parser = JsonOutputParser(pydantic_object=Agent2ResponseFormat)

        qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", agent2_response_prompt +  "\n\n" +
                     information_replacement + "\n\n" +
                    #  + feedback_content +    "\n\n"
                     negativity_avoiding_prompt + "\n\n"
                    # + contextualized_query_usage + "\n\n"
                    #  "Context: \n" + "{context}"
                     ),
                    # ("system", fmt),
                    MessagesPlaceholder("chat_history"),
                    ("ai", "Context: \n{context}"),
                    ("human", "User message: {input}"),
                    # ("ai", "Contextualized query: {contextualized_query}"),
                    ("ai", "User profile: {user_profile}"),
                    ("ai", "Business Logic to follow:\n{business_logic}"),
                    ("ai", "Current Workflow Stage: {workflow_stage}"),
                    ("ai", "Workflow Instruction:\n{instruction}"),
                    ("ai", "User Feedback:\n{user_feedback}"),
                    ("ai", "This is a hint for your response:\n{agent2_hint}"),
                ],
            )

        # Initialize memory and QA system
        question_answer_chain = create_stuff_documents_chain(llm_clients["response"], qa_prompt)

        # Create and return the RAG chain
        _rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return _rag_chain