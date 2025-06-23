# # agent-chatbot/common/config_globals.py
#
# from agent_chatbot.common.yaml_loader import load_config_yaml, preload_all_yaml
# from agent_chatbot.core.agent_loader import _load_agent_registry_yaml, _load_api_registry_yaml
#
# # ─── 1. Preload “everything else” from config/ ────────────────────────────────
# # If you want to read *all* YAML files at startup, call preload_all_yaml().
# # That will fill the internal cache for load_config_yaml(). We can expose it as ALL_CONFIGS.
# ALL_CONFIGS = preload_all_yaml()
#
# # ─── 2. Agent/API registries ──────────────────────────────────────────────────
# # Rather than pulling agent_registry.yaml out of ALL_CONFIGS, we let agent_loader handle it.
# # But we “wrap” them here into module‐level globals that everyone else can import.
# AGENT_REGISTRY = _load_agent_registry_yaml()  # this returns the “agents:” dict
# API_REGISTRY   = _load_api_registry_yaml()    # this returns the “llms:” dict
#
# # ─── 3. Any additional “master settings” you want to expose directly ────────────
# # For example, you probably want a global SETTINGS dict read from setting_registry.yaml:
# SETTINGS = load_config_yaml("setting_registry.yaml")
#
# # If you have a separate “weaviate_settings.yaml”, do the same:
# WEAVIATE_SETTINGS = load_config_yaml("weaviate_settings.yaml")
