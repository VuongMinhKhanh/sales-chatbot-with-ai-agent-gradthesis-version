from collections import Counter
from typing import List, Dict, Any
from weaviate.classes.query import Filter
from langchain_community.vectorstores import Weaviate
from langchain_core.documents import Document

from agent_chatbot.common.yaml_loader.api_manager import get_api_client
from agent_chatbot.common.yaml_loader.setting_manager import get_setting


def retrieve_context_sync(semantic_query, workflow_stage, top_k=3):
    """Truy vấn vectorstore Qdrant với điều kiện theo workflow_stage."""
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    context = {}
    query_vector = get_api_client("openai_embeddings").embed_query(semantic_query)

    for coll in get_setting("collection_names"):
        query_filter = Filter(
            must=[FieldCondition(
                key="workflow_stage",
                match=MatchValue(value=workflow_stage)
            )]
        )
        results = get_api_client("qdrant").query_points(
            collection_name=coll,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter
        )
        context[coll] = [point.payload for point in results.points]
    return context


def get_retriever(search_type: str = "similarity_score_threshold",
                  score_threshold: float = 0.4,
                  k: int = 20,
                  filters: dict=None):
    """
    Retrieve top_k documents related to semantic_query.
    """

    docsearch = get_api_client("docsearch")
    retriever = docsearch.as_retriever(
        search_type=search_type,
        search_kwargs={
            "score_threshold": score_threshold,
            "k": k,
            "filters": filters,  # ✅ Sử dụng đối tượng Filter đã kết hợp
        }
    )
    return retriever


# Rank documents based on relevance to the query
def rank_documents_by_relevance(query, documents):
    def compute_score(doc):
        name = doc.metadata.get("Tên", "").lower()
        return name.count(query.lower())  # Higher count means more relevant

    return sorted(documents, key=compute_score, reverse=True)


def get_top_n_rows_by_frequency(docs, top_n=3):
    row_counter = Counter(doc.metadata.get("row") for doc in docs if "row" in doc.metadata)
    most_common_rows = [row for row, _ in row_counter.most_common(top_n)]
    return set(most_common_rows)


def get_secondary_search_by_rows(
    docsearch: Weaviate,
    query: str,
    valid_rows: List[int],
    score_threshold: float = 0.4,
    k: int = 10
) -> List[Document]:
    """
    Truy xuất các Document bằng truy vấn `query`, chỉ lấy các chunk
    có metadata["row"] thuộc tập `valid_rows`, dùng retriever của LangChain.

    Parameters:
    - docsearch: LangChain vectorstore đã cấu hình
    - query: câu truy vấn người dùng
    - valid_rows: danh sách row IDs cần giữ lại
    - score_threshold: ngưỡng điểm similarity
    - k: số lượng tối đa kết quả cần lấy

    Returns:
    - List[Document] thỏa điều kiện
    """

    if isinstance(valid_rows, dict):
        valid_rows = list(valid_rows)

    # Tạo row_filter bằng Filter class
    row_filter = Filter.by_property("row").contains_any(valid_rows)

    # Gắn filter vào retriever
    retriever_filtered = docsearch.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "score_threshold": score_threshold,
            "k": k,
            "filters": row_filter,
        },
    )

    # Thực thi truy vấn
    return retriever_filtered.invoke(query)


def retrieve_and_filter_chunks_with_graphql(
    weaviate_client,
    collection_name: str,
    row_numbers: List[int],
    excluded_columns: List[str] = None
) -> List[Document]:
    """
    Fetch chunks from Weaviate by `row`, then build Documents exactly as
    in your pandas version—except aggregate all "Danh sách link ảnh"
    into a single chunk per row (max 3 links).
    """
    if excluded_columns is None:
        excluded_columns = [
            "Mô tả", "Mô tả chi tiết", "Nội dung", "Nội dung nổi bật",
            "Nội dung nổi bật 1", "Nội dung nổi bật 2", "Nội dung nổi bật 3",
            "Nội dung nổi bật 4", "Nội dung nổi bật 5", "Nội dung nổi bật 6",
            "Nội dung nổi bật 7", "Nội dung nổi bật 8", "Nội dung nổi bật 9",
            "Từ khóa", "Thẻ"
        ]

    # 1) Fetch all records for the given rows
    or_filters = ",\n".join(
        f"""{{
              path: ["row"]
              operator: Equal
              valueInt: {r}
            }}""" for r in row_numbers
    )
    query = f"""
    {{
      Get {{
        {collection_name}(
          where: {{
            operator: Or
            operands: [
              {or_filters}
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
    resp = weaviate_client.graphql_raw_query(query)
    records = resp.get[collection_name]

    # 2) Group by row: collect image links separately
    by_row = {r: {"others": [], "images": []} for r in row_numbers}
    for rec in records:
        row = rec.get("row")
        col = rec.get("column")
        txt = rec.get("text") or ""
        if col in excluded_columns:
            continue
        if col.strip().lower() == "danh sách link ảnh":
            # assume txt may be comma-separated or single URL
            for part in str(txt).split(","):
                url = part.strip()
                if url:
                    by_row[row]["images"].append(url)
        else:
            by_row[row]["others"].append((col, txt))

    # 3) Build Documents
    filtered_chunks: List[Document] = []
    for row, parts in by_row.items():
        # non-image chunks first
        for col, txt in parts["others"]:
            filtered_chunks.append(
                Document(
                    page_content=f"{txt}",
                    metadata={"source": col, "row": row}
                )
            )
        # then single aggregated image chunk
        if parts["images"]:
            top3 = parts["images"][:3]
            filtered_chunks.append(
                Document(
                    page_content=f"Danh sách link ảnh: {top3}",
                    metadata={
                        "source": "Danh sách link ảnh",
                        "row": row,
                    }
                )
            )

    return filtered_chunks


def retrieve_and_combine_documents(
    primary_query: str,
    secondary_query: str,
    retriever,                   # primary semantic retriever
    docsearch,                   # Weaviate vectorstore for secondary search
    collection_name: str,
    max_products: int = 3,
    score_threshold: float = 0.4,
    k: int = 10
) -> List[Document]:
    """
    1. Use `primary_query` to get initial_docs via retriever.invoke().
    2. Rank & exact-'Tên' filter.
    3. Pick top `max_products` rows.
    4. Use `secondary_query` to get secondary_docs restricted to those rows.
    5. Fetch full metadata chunks via GraphQL for those rows.
    6. Merge all chunks and collapse into one Document per row.
    """

    # Step 1: primary retrieval
    initial_docs = retriever.invoke(primary_query)

    # Step 2: rank by relevance & exact 'Tên' filter
    ranked_docs = rank_documents_by_relevance(primary_query, initial_docs)
    filtered_docs = [
        doc for doc in ranked_docs
        if "Tên" in doc.metadata and primary_query.lower() in doc.metadata["Tên"].lower()
    ]
    if not filtered_docs:
        filtered_docs = ranked_docs

    # Step 3: select top rows by frequency
    top_rows = get_top_n_rows_by_frequency(filtered_docs, top_n=max_products)

    # Step 4: secondary retrieval within top_rows (if secondary_query is non-empty)
    secondary_docs = []
    if secondary_query:
        secondary_docs = get_secondary_search_by_rows(
            docsearch,
            secondary_query,
            valid_rows=list(top_rows),
            score_threshold=score_threshold,
            k=k
        )

    # Step 5: fetch complete chunks via GraphQL
    additional_docs = retrieve_and_filter_chunks_with_graphql(
        get_api_client("weaviate"),
        collection_name,
        row_numbers=list(top_rows)
    )

    # Step 6: combine all docs whose row in top_rows
    all_docs = (
        [doc for doc in filtered_docs if doc.metadata.get("row") in top_rows]
        + secondary_docs
        + additional_docs
    )

    # Step 7: group by row and merge content
    grouped = {}
    for doc in all_docs:
        r = doc.metadata.get("row")
        grouped.setdefault(r, []).append(doc.page_content)

    combined = [
        Document(page_content="\n".join(contents), metadata={"row": r})
        for r, contents in grouped.items()
    ]

    return combined


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