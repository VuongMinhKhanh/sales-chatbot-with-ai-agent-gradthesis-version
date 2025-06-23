# clients/docsearch_factory.py

from langchain_weaviate.vectorstores import WeaviateVectorStore

from agent_chatbot.common.yaml_loader.api_manager import get_api_client
from agent_chatbot.common.yaml_loader.setting_manager import get_setting

# (If you already have these constants defined elsewhere, import them instead:)
WEAVIATE_CLASS_NAME = get_setting("weaviate_vectorstore")["class_name"]   # <— e.g. from a config module
WEAVIATE_TEXT_KEY   = get_setting("weaviate_vectorstore")["text_key"]             # <— e.g. "text"

def make_docsearch():
    """
    This factory will be called by api_manager._instantiate_client(...)
    whenever someone does get_api_client("docsearch").

    It pulls in the already‐instantiated Weaviate client and OpenAI embeddings
    from the API registry, then builds a WeaviateVectorStore on top of them.
    """
    # 1) get the low‐level weaviate Client object that was instantiated via YAML
    weaviate_client = get_api_client("weaviate")
    # 2) get the already‐instantiated OpenAIEmbeddings client from YAML
    embeddings       = get_api_client("openai_embeddings")

    return WeaviateVectorStore(
        client=weaviate_client,
        index_name=WEAVIATE_CLASS_NAME,
        text_key=WEAVIATE_TEXT_KEY,
        embedding=embeddings
    )
