import json
from pprint import pprint
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, AIMessage

from agent_chatbot.common.yaml_loader.api_manager import get_api_client

redis_client = get_api_client("redis")

def clear_conversation(conversation_id):
    """Clear conversation from Redis."""
    redis_client.delete(f"conversation:{conversation_id}")
    print(f"Cleared conversation for conversation_id: {conversation_id}")


def serialize_chat_history(chat_history):
    serialized_history = []
    for message in chat_history:
        if isinstance(message, HumanMessage):
            serialized_history.append({
                "type": "HumanMessage",
                "content": message.content
            })
        else:  # For other message types
            serialized_history.append({
                "type": "AiMessage",
                "content": message.content
            })
    return serialized_history


def store_chat_history(conversation_id, chat_history):
    """Store chat history in Redis."""
    chat_history_serialized = serialize_chat_history(chat_history)
    # print("chat_history_serialized", chat_history_serialized)
    redis_client.set(f"chat_history:{conversation_id}", json.dumps(chat_history_serialized))


def get_chat_history(raw_chat_history):
    """Retrieve chat history from Redis."""
    # history = redis_client.get(f"chat_history:{conversation_id}")
    if raw_chat_history:
        deserialized_history = json.loads(raw_chat_history)
        return [
            HumanMessage(content=msg["content"]) if msg["type"] == "human" else AIMessage(content=msg["content"])
            for msg in deserialized_history
        ]
    return []


def _make_jsonable(obj: Any) -> Any:
    """
    Recursively convert an object into something JSON-serializable.
    - dicts/lists get traversed
    - everything else becomes str(obj)
    """
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {k: _make_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_jsonable(v) for v in obj]
    # fallback for non-serializable (e.g. API clients)
    return str(obj)


def store_payload(conversation_id: str, payload: Dict[str, Any], exclude_keys: List[str]=[]):
    """
    Store the entire payload in Redis under key "conversation:{conversation_id}".
    Non-JSONable bits (like API instances) get stringified.
    """
    # 1) Replace the chat_history list of HumanMessage/AIMessage with our JSONable list
    p = payload.copy()

    try:
        for key in exclude_keys:
            p.pop(key, None)
    except KeyError as e:
        print("Key Error when excluding keys:", e)

    if "chat_history" in p:
        p["chat_history"] = serialize_chat_history(p["chat_history"])
    # 2) Remove or stringify any unserializable entries (e.g. your 'apis' dict)
    p = _make_jsonable(p)
    print("Saved payload")
    pprint(p)
    redis_client.set(f"conversation:{conversation_id}", json.dumps(p))


def get_payload(conversation_id: str) -> Dict[str, Any]:
    """
    Retrieve the full payload, rehydrating only chat_history back into
    HumanMessage/AIMessage objects. Everything else remains as plain JSON.
    """
    data = redis_client.get(f"conversation:{conversation_id}")
    if not data:
        return {}
    p = json.loads(data)
    # rebuild chat_history if present
    if "chat_history" in p:
        rebuilt = []
        for msg in p["chat_history"]:
            if msg["type"] == "HumanMessage":
                rebuilt.append(HumanMessage(content=msg["content"]))
            else:
                rebuilt.append(AIMessage(content=msg["content"]))
        p["chat_history"] = rebuilt
    return p


def is_assigned(conversation_id):
    """Check if a conversation is assigned to a consultant."""
    return redis_client.exists(f"assigned_conversation:{conversation_id}")


def mark_assigned(conversation_id, consultant_id):
    """Mark a conversation as assigned in Redis with a TTL of 1 hour."""
    redis_client.setex(f"assigned_conversation:{conversation_id}", 3600, consultant_id)


def remove_assigned(conversation_id):
    """Remove assigned status for a conversation."""
    redis_client.delete(f"assigned_conversation:{conversation_id}")