from typing import List, Dict, Any

import sys

from agent_chatbot.services.vectorstore import retrieve_products_by_ids

def build_card_items_from_cart(
    cart_items: List[Dict[str, Any]],
    weaviate_client,
    collection_name: str,
    included_columns: List
) -> List[Dict[str, Any]]:
    """
    Given cart_items containing product_id, use Weaviate to fetch "Danh sách link ảnh" and "Đơn vị",
    then build and return Chatwoot card_items with media_url and unit applied.
    """
    # 1. Extract and convert product_ids
    product_ids = [int(item["product_id"]) for item in cart_items]

    # 2. Retrieve Weaviate data for images and units
    # included_columns = ["Danh sách link ảnh", "Đơn vị"]
    retrieved = retrieve_products_by_ids(
        weaviate_client,
        collection_name,
        product_ids,
        included_columns=included_columns
    )

    # 3. Build a lookup by product_id
    info_by_id = {int(d["id"]): d for d in retrieved}

    # 4. Construct card_items
    card_items: List[Dict[str, Any]] = []
    for item in cart_items:
        pid = int(item.get("product_id"))
        info = info_by_id.get(pid, {})
        images = info.get("images", [])
        unit_val = info.get("Đơn vị")
        product_link = info.get("Link sản phẩm", "")
        mentioned_product = next((item for item in cart_items if int(item["product_id"]) == pid), {})
        price = mentioned_product.get("price", 0)
        formatted_price = f"{price:,}".replace(",", ".")
        name = mentioned_product.get("name", "")
        description = f"💰{formatted_price} VND"
        quantity = item.get("quantity")

        if name != "":
            description = f"🛍️{name} - {description}"

        if quantity is not None and unit_val:
            description += f" - 📦{quantity} {unit_val}"

        # Use first image URL if available
        media_url = images[0] if images else item.get("media_url")

        # Build product link URI
        action = {
            "type": "link",
            "text": "Xem sản phẩm",
            "uri": f"{product_link}"
        }

        card_items.append({
            "title": item.get("product_name", ""),
            "description": description,
            "media_url": media_url,
            "actions": [action]
        })

    return card_items