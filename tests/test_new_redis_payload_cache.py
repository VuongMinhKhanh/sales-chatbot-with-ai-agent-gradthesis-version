from pprint import pprint

from chatbot.agents.agent5 import DummyOrderApi
from redis_store.redis_cache import store_payload, get_payload

workflow_stages = "Greeting, Needs Assessment, Qualification, Product Presentation, Objection Handling, Closing"

# actions = [
#         {
#             "agent": "Agent5",
#             "task": "process_task",
#             "payload": {
#                 'cart': ['loa này'], 'customer_info': {'customer_name': 'Khánh', 'customer_phone': '0909933916'}
#             }
#         }
#     ]

payload = {
   'user_message': 'Tôi muốn đặt mua loa này, tên Khánh, số điện thoại: 0909933916',
   'workflow_stage': 'Needs Assessment', 'chat_history': [],
   # 'business_logic': '1. rule-004:\n   When a user mentions or asks about a product with a specific price (X), any alternative or upsell recommendation should fall within a reasonable price range around X, based on customer intent.\n\n2. rule-001:\n   If user asks about a product, recommend discounted items and ask about intended usage.',
   # 'user_feedback': '🧾 tôi muốn mua loa bose 101 mexico\n❌ Xin lỗi, tôi không thể cung cấp thông tin vì context không nói rõ về nơi bạn có thể mua loa Bose 101 Mexico.\n🛠 Khi khách hàng nói muốn mua, bạn ko cần phải xem xét khả năng thực sự mua ở đâu, mà là những thông tin cần thiết để mua, như giá, thời gian bảo hàng.\n✅ Vâng, bên chúng tôi có bán loa bose 101 mexico, với giá là <giá> và thời gian bảo hành là <thời gian bảo hành> tháng <và các thông tin cần thiết khác nếu bạn thấy chúng phù hợp>\n\n---\n\n🧾 Anh đã mua loa JBL Eon 712 Loa liền công suất, Thấy quảng cáo khuyến mãi amplifiers, Tư vấn đầu tư thêm gì để có bộ Karaoke tốt hơn không ?\n❌ Tôi không biết\n🛠 Bạn tuyệt đối không được trả lời "Tôi không biết" hay các câu trả lời cụt ngủn như vậy được.\n✅ Dạ, tôi không biết phải hỗ trợ bạn như thế nào. Bạn có thể tư vấn nhân viên kỹ thuật của 769audio tại SĐT: <SĐT>\n\n---\n\n🧾 tôi muốn mua loa bose 101 mexico\n❌ Loa Bose 101 Mexico bạn muốn mua là hàng cũ đã qua sử dụng vì hiện nay hãng Bose không còn sản xuất model này nữa. Giá của loa Bose 101 Mexico là 2,900,000 VND và sản phẩm bảo hành trong 02 tháng.\n🛠 Khi bạn báo giá, bạn nên hỏi là "giá bên chúng tôi" hãy "giá bán của cửa hàng 769audio".\n✅ Vâng, Loa Bose 101 chúng tôi có giá là <giá sản phẩm>',
   # 'user_profile': '', 'workflow_stages': workflow_stages,
   # 'instruction': 'Đặt câu hỏi trọng tâm để khám phá nhu cầu...',
   'apis': {'order_api': DummyOrderApi()  },
    # "actions": actions
}

# conversation_id = 0
#
# store_payload(conversation_id, payload)
#
# stored_payload = get_payload(conversation_id)
#
# pprint(stored_payload)