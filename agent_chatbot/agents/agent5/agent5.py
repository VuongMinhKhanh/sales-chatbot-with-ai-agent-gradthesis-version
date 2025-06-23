import os
import random
from types import SimpleNamespace
from typing import List, Dict, Any

import yaml
from langchain_core.messages import HumanMessage, AIMessage

from agent_chatbot.agents.agent5.utils import build_card_items_from_cart
from agent_chatbot.common.yaml_loader.api_manager import get_api_client
from agent_chatbot.common.yaml_loader.setting_manager import get_setting
from agent_chatbot.core.agent_loader import get_agent_config
from chatwoot.chatwoot_api import send_message_to_chatwoot, send_card_as_interactive_message, \
    send_form_as_interactive_message


def agent5_simulated_checkout(llm_clients: Dict[str, Any],
                              payload: Dict[str, Any]) -> Dict[str, str]:
    """
    1) Validate that 'actions' and 'apis' exist in payload.
    2) Extract Agent5 block and ensure 'conversation_id', 'name', 'phone' are provided.
    3) Build checkout kwargs from agent payload.
    4) Call order_api.checkout(...) and return confirmation.
    """
    cfg = get_agent_config("Agent5")

    # 1) Check top-level context keys
    missing_ctx = [key for key in cfg.get("required_context_keys", []) if key not in payload]
    if missing_ctx:
        return {"response": f"Error: missing context keys: {', '.join(missing_ctx)}."}

    # 2) Extract Agent5 action payload
    actions = payload.get("actions", [])
    agent_block = next((a for a in actions if a.get("agent") == "Agent5"), None)
    if not agent_block or "payload" not in agent_block:
        return {"response": "Error: no Agent5 action payload found."}
    agent_data = agent_block["payload"]

    # Validate conversation_id in agent_data
    if not isinstance(agent_data.get("conversation_id"), int):
        return {"response": "Error: missing or invalid 'conversation_id' in payload."}

    # Validate customer_info fields
    customer = agent_data.get("customer_info", {})
    missing_info = [field for field in ["name", "phone"] if not customer.get(field)]
    if missing_info:
        return {"response": f"Error: missing {', '.join(missing_info)} in customer_info."}

    # 3) Prepare checkout API
    api_conf = cfg.get("api_call", {})
    client_key = api_conf.get("client")
    client = payload.get("apis", {}).get(client_key)
    if not client:
        return {"response": f"Error: API client '{client_key}' not provided."}
    method = getattr(client, api_conf.get("method", ""), None)
    if not callable(method):
        return {"response": f"Error: method '{api_conf.get('method')}' not found on client."}

    # Build args for checkout
    kwargs = {
        "conversation_id": agent_data["conversation_id"],
        "cart": agent_data.get("cart", []),
        "customer_info": customer
    }

    # 4) Call checkout API
    order = method(**kwargs)
    return {"response": f"🎉 Đơn hàng #{order.id} đã được gửi yêu cầu lập! Nhân viên bán hàng sẽ gọi lại để xác nhận với Quý khách."}

# --- API def emulator ---
class OrderCheckoutApi:
    """
    Emulates the checkout API by sending a Chatwoot interactive form
    for the customer to confirm their order, then returns a stubbed order ID.
    """
    def send_checkout_form(
        self,
        conversation_id: int,
        cart: List[Dict[str, Any]],
        customer_info: Dict[str, Any]
    ) -> SimpleNamespace:
        """
        Test endpoint to invoke send_checkout_form via HTTP.
        Expects JSON body with 'conversation_id', 'customer_info', 'cart_items'.
        """
        step_1_message = "🛍️Em xin phép gửi Quý khách thông tin sản phẩm và thông tin khách hàng trước khi lập đơn."
        step_2_message = "📝Quý khách kiểm tra và bổ sung thêm thông tin và bấm xác nhận để bên mình tiến hành lập đơn hàng."

        send_message_to_chatwoot(conversation_id,
                                 step_1_message)

        # Build card items
        included_columns = ["Đơn vị", "Danh sách link ảnh", "Link sản phẩm"]
        card_items = build_card_items_from_cart(
            cart,
            get_api_client("weaviate"),
            get_setting("weaviate_vectorstore")["class_name"],
            included_columns=included_columns
        )

        send_card_as_interactive_message(conversation_id,
                                         card_items
                                         )
        send_form_as_interactive_message(conversation_id,
                                         customer_info
                                         )

        send_message_to_chatwoot(conversation_id,
                                 step_2_message)

        return SimpleNamespace(id=random.randint(1000, 9999))


if __name__ == "__main__":
    sample_payload = {'actions': [{'agent': 'Agent5',
              'payload': {
        "conversation_id": 1,
        "customer_info": {
            "name": "John Doe",
            "phone": "0123456789",
            "address": "",  # not yet provided
        },
        "cart": [
            {"product_id": "147", "product_name": "Soundbar X", "product_price": 199.99, "quantity": 1},
            {"product_id": "312", "product_name": "Subwoofer Y", "product_price": 89.50, "quantity": 2}
        ]
    },
              'task': 'process_order'}],
 'additional_info': {},
 'apis': {'order_api': OrderCheckoutApi()},

 'user_message': 'Cho tôi đặt mua loa Bose 101, tên Khánh, số điện thoại '
                 '0909933916.',
 'user_profile': 'Khách hàng đang quan tâm đến loa Bose.',
 'workflow_stage': 'Qualification',
 'workflow_stages': ['Greeting', 'Needs Assessment']}


    # --- 2) Call the agent and print its reply ---
    response = agent5_simulated_checkout(None, sample_payload)
    print(response)
