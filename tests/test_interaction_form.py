from pprint import pprint
from typing import List, Dict, Any

import requests
from flask import jsonify

from chatbot.utils import build_card_items_from_cart
from chatbot.vectorstore import retrieve_products_by_ids
from chatwoot.chatwoot_api import headers, account_id
from services import get_weaviate_client




if __name__ == "__main__":
    conversation_id = 1
    context = {
        "customer_info": {
            "name": "John Doe",
            "phone_num": "0123456789",
            "address": "",  # not yet provided
        },
        "cart": [
            {"product_id": "147", "product_name": "Soundbar X", "product_price": 199.99, "quantity": 1},
            {"product_id": "312", "product_name": "Subwoofer Y", "product_price": 89.50, "quantity": 2}
        ]
    }

    # send_checkout_form(conversation_id,
    #                    context.get("customer_info", {}),
    #                    context.get("cart", {})
    #                    )
    #
    # client = get_weaviate_client()
    # collection_name = "ChatBot_769Audio"
    # included = ["Đơn vị", "Danh sách link ảnh", "Link sản phẩm"]
    # cart_items = build_card_items_from_cart(
    #     context.get("cart", {}),
    #     client,
    #     collection_name,
    #     included_columns=included
    # )
    #
    # print("cart_items")
    # pprint(cart_items)

    # cart = [
    #       {
    #         "product_id": "242",
    #         "name": "Loa Bose 301 seri 4",
    #         "quantity": 1,
    #         "price": 8400000
    #       }
    #     ]
    # pid = 242
    # mentioned_product = next((item for item in cart if int(item["product_id"]) == pid), {})
    # print("mentioned_product", mentioned_product)