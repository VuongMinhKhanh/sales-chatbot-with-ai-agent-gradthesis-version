from typing import List, Dict, Any

from services import get_weaviate_client


from typing import List, Dict, Any

def retrieve_products_by_ids(
    weaviate_client,
    collection_name: str,
    ids: List[str],
    included_columns: List[str] = None
) -> List[Dict[str, Any]]:
    """
    1) Fetch mapping of each UUID -> its `row` property.
    2) Fetch all (column, text) chunks for those rows.
    3) Return a list of dicts, one per input UUID, containing:
         - all `included_columns`
         - an 'images' list (up to 3 URLs from "Danh sách link ảnh")
    """

    if included_columns is None:
        included_columns = ["Tên", "Giá", "Tình trạng", "Mô tả", "Danh sách link ảnh"]

    # ─── STEP 1: get each object's `row` by filtering on its UUID ───
    or_id_filters = ",\n".join(
        f"""{{
            path: ["text"]
            operator: Equal
            valueString: "ID: {uuid}"
        }}""" for uuid in ids
    )
    query_map = f"""
    {{
      Get {{
        {collection_name}(
          where: {{
            operator: Or
            operands: [
              {or_id_filters}
            ]
          }}
        ) {{
          row
          text
        }}
      }}
    }}
    """
    resp1 = weaviate_client.graphql_raw_query(query_map)
    rows_mapping = resp1.get[collection_name]

    # build both lookups
    row_to_id: Dict[int, str] = {}
    for rec in rows_mapping:
        row = rec.get("row")
        raw_text = rec.get("text", "")
        try:
            _, clean_str = raw_text.split(":", 1)
            clean_id = int(clean_str.strip())  # <-- convert to int
        except (ValueError, TypeError):
            continue

        if row is not None and clean_id in ids:
            row_to_id[row] = clean_id

    # ─── STEP 2: fetch every chunk for those rows, but only for included_columns ───
    unique_rows = sorted(row_to_id.keys())

    # 1) OR‐filter for rows
    or_row_filters = ",\n".join(
        f"""{{ path: ["row"], operator: Equal, valueInt: {row} }}"""
        for row in unique_rows
    )

    # 2) OR‐filter for columns
    or_col_filters = ",\n".join(
        f"""{{ path: ["column"], operator: Equal, valueString: "{col}" }}"""
        for col in included_columns
    )

    query_data = f"""
    {{
      Get {{
        {collection_name}(
          where: {{
            operator: And
            operands: [
              {{
                operator: Or
                operands: [
                  {or_row_filters}
                ]
              }},
              {{
                operator: Or
                operands: [
                  {or_col_filters}
                ]
              }}
            ]
          }}
          limit: 10000
        ) {{
          row
          column
          text
        }}
      }}
    }}
    """
    resp2 = weaviate_client.graphql_raw_query(query_data)
    chunks = resp2.get[collection_name]

    # STEP 3: group by UUID, filter by included_columns, special-case image column,
    # and remove the "<column>: " prefix from non-image texts
    by_id: Dict[int, Dict[str, Any]] = {
        raw_id: {"fields": {}, "images": []} for raw_id in ids
    }

    for rec in chunks:
        row = rec.get("row")
        col = rec.get("column")
        txt = (rec.get("text") or "").strip()
        raw_id = row_to_id.get(row)
        if raw_id is None or col not in included_columns:
            continue

        # if this is the image list, split into URLs
        if col.strip().lower() == "danh sách link ảnh":
            for url in txt.split(","):
                url = url.strip()
                if url and len(by_id[raw_id]["images"]) < 3:
                    by_id[raw_id]["images"].append(url)
        else:
            # remove any leading "ColumnName:" prefix
            prefix = f"{col}:"
            if txt.startswith(prefix):
                value = txt[len(prefix):].strip()
            else:
                value = txt
            by_id[raw_id]["fields"][col] = value

    # BUILD final output
    results: List[Dict[str, Any]] = []
    for raw_id in ids:
        data = by_id[raw_id]
        entry = {"id": raw_id}
        entry.update(data["fields"])
        entry["images"] = data["images"]
        results.append(entry)

    return results


if __name__ == "__main__":
    client = get_weaviate_client()
    collection_name = "ChatBot_769Audio"
    included = ["Tên", "Giá", "Đơn vị", "Danh sách link ảnh"]
    product_data = retrieve_products_by_ids(
        client,
        collection_name,
        ids=[312, 147, 2447],
        included_columns=included
    )

    print("Product info")
    print(product_data)