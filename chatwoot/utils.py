from langchain_core.messages import AIMessage

from chatwoot.chatwoot_api import send_message_to_chatwoot


def handle_ai_response(conversation_id, ai_response, chat_history):
    """
    Send a follow-up message to Chatwoot, update local chat history, and store it.

    Args:
        conversation_id (str): Chatwoot conversation ID.
        ai_response (string): The AI message.
        chat_history (List[BaseMessage]): LangChain message list (e.g., [HumanMessage, AIMessage...])
    """

    # 1. Send to Chatwoot
    send_message_to_chatwoot(conversation_id, ai_response)

    # 2. Append to local history
    chat_history.append(AIMessage(content=ai_response))
