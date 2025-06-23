import os

from dotenv import load_dotenv

from agent_chatbot.services.weaviate_factory import make_weaviate_client

load_dotenv()

if __name__ == "__main__":
    cluster_url = os.getenv("WEAVIATE_URL")
    print("cluster_url", cluster_url)
    api_key = os.getenv("WEAVIATE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    weaviate_client = make_weaviate_client(
        cluster_url,
        api_key,
        openai_api_key
    )

    print(weaviate_client.is_ready())