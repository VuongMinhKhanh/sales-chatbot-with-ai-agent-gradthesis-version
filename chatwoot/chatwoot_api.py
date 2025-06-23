import requests

from config import ACCOUNT_ID, CHATWOOT_API_TOKEN, AGENT_ID

account_id = ACCOUNT_ID
api_access_token = CHATWOOT_API_TOKEN
consultant_id = AGENT_ID
headers = {
    "api_access_token": api_access_token,
    "Content-Type": "application/json"
}


def send_typing_indicator(conversation_id, typing_status):
    """
    Toggles the 'typing...' indicator in Chatwoot.

    :param conversation_id: Conversation ID
    :param typing_status: True to show typing, False to hide
    """
    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conversation_id}/toggle_typing_status"

    payload = {
        "typing_status": typing_status  # Should be on or off
    }

    response = requests.post(url, headers=headers, json=payload)

    # # ✅ Debugging: Print response details
    # print("📌 API Request Details")
    # print("URL:", url)
    # print("Headers:", headers)
    # print("Payload:", payload)
    # print("🔹 Status Code:", response.status_code)
    #
    # # ✅ Check if response is empty
    # if response.text.strip() == "":
    #     print("⚠️ Empty Response from Chatwoot API")
    #     return {"error": "Empty response from Chatwoot API"}

    # ✅ Try parsing JSON response
    try:
        response_json = response.json()
        # print("🔹 Response JSON:", response_json)
        return response_json
    except ValueError:
        print("⚠️ Response is not in JSON format:", response.text)
        return {"error": "Response is not JSON", "raw_response": response.text}


def update_chatwoot_user(contact_id, new_description):
    """
    Updates the description field inside 'additional_attributes' for a contact in Chatwoot.

    :param contact_id: Contact ID to update
    :param new_description: New description to update
    :return: API response (JSON)
    """
    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/contacts/{contact_id}"

    payload = {
        "additional_attributes": {
            "description": new_description
        }
    }

    response = requests.put(url, headers=headers, json=payload)

    # # 🔍 Debugging: Print request details
    # print("📌 API Request Details")
    # print("URL:", url)
    # print("Headers:", headers)
    # print("Payload:", payload)
    #
    # # 🔍 Debugging: Print response details
    # print("🔹 Status Code:", response.status_code)
    # print("🔹 Response JSON:", response.json())

    return response.json()


def get_chatwoot_customer_details(contact_id):
    """
    Fetch full information of a customer from Chatwoot.

    :param contact_id: The contact ID of the customer
    :return: JSON response containing customer details
    """
    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/contacts/{contact_id}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": f"Failed to fetch contact details. Status Code: {response.status_code}",
            "response": response.text
        }


def send_message_to_chatwoot(conversation_id, message_content):
    url = f"https://app.chatwoot.com/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}/messages"

    data = {"content": message_content}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Message sent successfully to Chatwoot.")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")


def set_unassigned(conversation_id):
    url = f"https://app.chatwoot.com/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}/assignments"
    data = {"assignee_id": None}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Conversation {conversation_id} successfully set to Unassigned status.")
    else:
        print(f"Failed to set conversation to Unassigned status: {response.status_code}, {response.text}")


def assign_to_consultant(conversation_id):
    """
    Assign a conversation to a specific consultant if it is not already assigned.

    :param conversation_id: The ID of the conversation to assign.
    :return: Boolean indicating success or failure.
    """
    url = f"https://app.chatwoot.com/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}/assignments"
    data = {"assignee_id": consultant_id}

    # Check if the conversation is already assigned to avoid conflicts
    check_url = f"https://app.chatwoot.com/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}"
    response_check = requests.get(check_url, headers=headers)

    if response_check.status_code == 200:
        current_assignee = response_check.json().get("assignee_id")
        if current_assignee is not None:
            print(
                f"Conversation {conversation_id} is already assigned to consultant {current_assignee}. No reassignment performed.")
            return False  # Already assigned

    # Proceed to assign the consultant
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Conversation {conversation_id} successfully assigned to consultant {consultant_id}.")
        return True
    else:
        print(f"Failed to assign consultant: {response.status_code}, {response.text}")
        return False


def send_form_as_interactive_message(conversation_id,
                                     customer_info,
                                     form_items=None,
                                     content="Please fill out your checkout details:"):
    """
    Sends an interactive checkout form into a Chatwoot conversation.

    :param conversation_id: ID of the Chatwoot conversation
    :param customer_info:   Dict with keys 'name', 'phone_num', 'address' (pre-filled or empty)
    :param form_items:      List of dicts defining fields for the user to fill; defaults to name, phone_num, address
    :param content:         Intro text shown above the form
    :return:                JSON response from Chatwoot API or error dict
    """
    # Default customer-fillable items
    if form_items is None:
        form_items = [
            {"name": "name", "label": "Full Name", "placeholder": "Enter your full name", "type": "text",
             "default": customer_info.get("name", "")},
            {"name": "phone", "label": "Phone Number", "placeholder": "Enter your phone number", "type": "text",
             "default": customer_info.get("phone", "")},
            {"name": "address", "label": "Shipping Address", "placeholder": "Enter your shipping address",
             "type": "text_area", "default": customer_info.get("address", "")}
        ]

    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    payload = {
        "content": content,
        "message_type": "outgoing",
        "content_type": "form",
        "content_attributes": {
            "items": form_items,
        },
        "private": False
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except ValueError:
        return {"error": "Non-JSON response", "status_code": response.status_code, "body": response.text}


def send_card_as_interactive_message(conversation_id,
                                     card_items,
                                     content="🛒 Your Cart Items:"
                                     ):
    """
    Sends an interactive cards message listing products in the customer's cart.

    :param conversation_id: ID of the Chatwoot conversation
    :param card_items:      List of dicts with keys: product_id, product_name, product_price
    :param content:         Introductory text above the cards
    :return:                Parsed JSON response or error dict
    """
    # card_items = [{'actions': [{'text': 'Xem sản phẩm',
    #                             'type': 'link',
    #                             'uri': 'https://769audio.vn/san-pham/147/loa-bose-acoustimass-m10-seri-iv.html'}],
    #                'description': '💰Price: $199.99\n📦Quantity: 1 Bộ',
    #                'media_url': 'https://769audio.vn/upload/images/C%E1%BB%A5c%20%C4%90%E1%BA%A9y%20C%C3%B4ng%20Su%E1%BA%A5t%20Bosa%20K3800%201.jpg',
    #                'title': 'Soundbar X'},
    #               {'actions': [{'text': 'Xem sản phẩm',
    #                             'type': 'link',
    #                             'uri': 'https://769audio.vn/san-pham/312/loa-jbl-control-25-chinh-hang.html'}],
    #                'description': '💰Price: $89.50\n📦Quantity: 2 cặp',
    #                'media_url': 'https://769audio.vn/upload/images/jbl%20control%2025%20(9).jpg',
    #                'title': 'Subwoofer Y'}]
    #

    # cart_items = []
    # for item in cart_items:
    #     # Build description with price and optional quantity/unit
    #     price = item.get("product_price", 0)
    #     description = f"💰Price: ${price:.2f}"
    #     quantity = item.get("quantity")
    #     unit = item.get("unit")
    #     if quantity is not None and unit:
    #         description += f"\n📦Quantity: {quantity} {unit}"
    #
    #     # Minimal dummy action (empty link) to satisfy validation
    #     action = {
    #         "type": "link",
    #         "text": "Xem sản phẩm",  # Invisible button label
    #         "uri": "https://#"
    #     }
    #
    #     card_items.append({
    #         "title": item.get("product_name", ""),
    #         "description": description,
    #         "media_url": item.get("media_url"),  # optional image URL
    #         "actions": [action]
    #     })

    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    payload = {
        "content": content,
        "message_type": "outgoing",
        "content_type": "cards",
        "content_attributes": {"items": card_items},
        "private": False
    }
    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except ValueError:
        return {"error": "Non-JSON response", "status_code": response.status_code, "body": response.text}


