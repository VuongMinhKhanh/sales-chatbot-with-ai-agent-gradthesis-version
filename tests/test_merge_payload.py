from pprint import pprint
from typing import Dict, Any, List

from langchain_core.messages import AIMessage


def deep_merge(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge `new` into `old`:

    - If both `old[key]` and `new[key]` are dicts: recurse.
    - If both are lists: union them (keep all unique items).
    - Otherwise: overwrite `old[key]` with `new[key]`.

    Returns the merged dictionary `old`.
    """
    for key, new_val in new.items():
        if key in old and isinstance(old[key], dict) and isinstance(new_val, dict):
            deep_merge(old[key], new_val)
        elif key in old and isinstance(old[key], list) and isinstance(new_val, list):
            # Union lists without duplicates
            merged_list = old[key] + [item for item in new_val if item not in old[key]]
            old[key] = merged_list
        else:
            # Replace or add
            old[key] = new_val
    return old


# Example usage:
if __name__ == '__main__':
    # old_payload = {
    #     'cart': ['loa này'],
    #     'customer_info': {
    #         'customer_name': 'Khánh',
    #         'customer_phone': '0909933916'
    #     },
    #     'user_message': 'Tôi muốn đặt mua loa này, tên Khánh, số điện thoại: 0909933916',
    #     'workflow_stage': 'Needs Assessment',
    #     'chat_history': [AIMessage(content="hello, im bot")],
    #     'instruction': 'Đặt câu hỏi trọng tâm để khám phá nhu cầu...',
    #     'additional_info': {
    #         'mentioned_products': [
    #             {'product_id': 3, 'product_name': 'Loa A', 'product_price': 1000000},
    #         ],
    #     }
    # }
    #
    # new_payload = {
    #     'additional_info': {
    #         'mentioned_products': [
    #             {'product_id': 1, 'product_name': 'Loa A', 'product_price': 1000000},
    #             {'product_id': 2, 'product_name': 'Loa B', 'product_price': 2500000},
    #         ],
    #         'extra_flag': True,
    #     },
    #     'user_message': 'Tôi muốn đặt mua loa này, tên Khánh',
    #     'workflow_stage': 'Purchase Intent',
    #     "chat_history": [AIMessage(content="hello, im bot 2")]
    # }

    old_payload = {
        "actions": [{'agent': 'Agent2',
              'payload': {'hint': 'Tìm thông tin chi tiết về loa Bose'},
              'task': 'retrieve_product_info'},
             {'agent': 'Agent3',
              'payload': {'hint': 'Hỏi thêm về loại loa Bose mà khách đang '
                                  'quan tâm hoặc tính năng cụ thể mà họ muốn '
                                  'biết.'},
              'task': 'generate_follow_up'}
        ]
    }

    new_payload = {
        "actions": [{'agent': 'Agent2',
              'payload': {'hint': 'Tìm thông tin chi tiết về loa Bose, bao gồm '
                                  'tính năng, giá cả và các sản phẩm khác.'},
              'task': 'retrieve_product_info'},
             {'agent': 'Agent3',
              'payload': {'hint': 'Hỏi thêm về nhu cầu cụ thể của khách hàng '
                                  'đối với loa Bose, ví dụ như mục đích sử '
                                  'dụng hoặc ngân sách.'},
              'task': 'generate_follow_up'},
             {'agent': 'Agent3',
              'payload': {'hint': 'Xin vui lòng cho tôi biết tên và số điện '
                                  'thoại của bạn để tôi có thể tiến hành đặt '
                                  'hàng loa Bose 101.'},
              'task': 'generate_follow_up'},
             {'agent': 'Agent5',
              'payload': {'cart': ['bose_101_product_id'],
                          'customer_info': {'customer_name': 'Khánh',
                                            'customer_phone': '0909933916'}},
              'task': 'place_order'}]
    }

    merged = deep_merge(old_payload, new_payload)
    pprint(merged)
