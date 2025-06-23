# chatbot/bootstrap.py
from agent_chatbot.common.yaml_loader.api_manager import load_all_api_clients, load_api_clients_grouped_by_agent
from agent_chatbot.common.yaml_loader.setting_manager import load_all_settings
from agent_chatbot.core.agent_loader import list_registered_agents

ALL_CONFIGS = {}
SETTINGS = {}
AGENT_REGISTRY = {}
API_CLIENTS = {}

def initialize_system():
    """
    Bootstrap the chatbot system: eager-initialize all heavy clients,
    warm up vectorstores, register agents, and prepare retrievers.
    """
    print("🚀 Bootstrapping system...")
    global ALL_CONFIGS, AGENT_REGISTRY, API_CLIENTS, SETTINGS
    # ─── 1. Preload “everything else” from config/ ────────────────────────────────
    # If you want to read *all* YAML files at startup, call preload_all_yaml().
    # That will fill the internal cache for load_config_yaml(). We can expose it as ALL_CONFIGS.
    # ALL_CONFIGS = preload_all_yaml()

    # ─── 3. Any additional “master settings” you want to expose directly ────────────
    # For example, you probably want a global SETTINGS dict read from setting_registry.yaml:
    SETTINGS = load_all_settings()

    # ─── 2. Agent/API registries ──────────────────────────────────────────────────
    # Rather than pulling agent_registry.yaml out of ALL_CONFIGS, we let agent_loader handle it.
    # But we “wrap” them here into module‐level globals that everyone else can import.
    AGENT_REGISTRY = list_registered_agents()  # this returns the “agents:” dict
    API_CLIENTS = load_all_api_clients()  # this returns the client dict


    # print("ALL_CONFIGS", ALL_CONFIGS)
    print("SETTINGS", SETTINGS)
    print("AGENT_REGISTRY", AGENT_REGISTRY)
    print("API_REGISTRY", API_CLIENTS)

    # # Load & cache LLMs & embeddings
    # get_openai_embeddings()
    # get_llm_generic()
    # get_llm_generic_with_json()
    # get_llm_agent1_dispatch()
    # get_llm_agent2_contextualization()
    # get_llm_agent2_response()
    # get_llm_agent3_followup()
    #
    # # Connect to vector databases
    # get_weaviate_client()
    # get_qdrant_client()
    # get_redis_client()
    #
    # # Build vectorstore wrapper and retriever
    # get_docsearch()
    # get_retriever()
    #
    # # Ensure agents are registered
    # load_all_agents_and_controller()
    # assert agent_registry, "🛑 No agents registered! Did you forget to decorate/register one?"
    # print(f"✅ Registered agents: {list(agent_registry.keys())}")

    print("✅ Chatbot system initialized successfully.")


if __name__ == "__main__":
    initialize_system()