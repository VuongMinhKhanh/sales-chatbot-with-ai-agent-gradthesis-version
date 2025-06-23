# clients/weaviate_factory.py

import weaviate
from weaviate.classes.init import Auth

def make_weaviate_client(
    cluster_url: str,
    api_key: str,
    openai_api_key: str = None,
):
    headers = {}
    if openai_api_key:
        headers["X-OpenAI-Api-Key"] = openai_api_key

    return weaviate.connect_to_weaviate_cloud(
        cluster_url=cluster_url,
        auth_credentials=Auth.api_key(api_key),
        headers=headers or None,
    )
