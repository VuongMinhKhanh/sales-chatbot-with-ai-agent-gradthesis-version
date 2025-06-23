# agent-chatbot/common/api_manager.py

import os
import importlib
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from agent_chatbot.common.yaml_loader.yaml_loader import load_config_yaml
from agent_chatbot.core.agent_loader import list_registered_agents

load_dotenv()
# Path to the YAML under config/ (though load_config_yaml knows where to find it)
_API_REGISTRY_FILENAME = "api_registry.yaml"
_AGENT_DIR = Path(__file__).parent.parent.parent / "agents"

# Cache for all instantiated API clients
_API_CLIENTS: Dict[str, Any] = {}

def _instantiate_client(name: str, cfg: Dict[str, Any]) -> Any:
    """
    Given 'name' (e.g. "weaviate") and its config dict from api_registry.yaml,
    import the specified client_class, resolve init_args (with ${ENV_VAR} → os.getenv),
    instantiate it, and return the instance.
    """
    # 1) Split "module.ClassName" into module path and class name
    class_path = cfg.get("client_class")
    if not (isinstance(class_path, str) and "." in class_path):
        raise RuntimeError(f"Invalid or missing 'client_class' for API '{name}': {class_path!r}")

    module_name, cls_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    ClientClass = getattr(module, cls_name)

    # 2) Build init_args, substituting any "${ENV_VAR}" with os.getenv("ENV_VAR")
    init_args: Dict[str, Any] = {}
    for k, v in cfg.get("init_args", {}).items():
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_key = v[2:-1]
            init_args[k] = os.getenv(env_key)
        else:
            init_args[k] = v

    # 3) Instantiate and return
    return ClientClass(**init_args)

def load_all_api_clients() -> Dict[str, Any]:
    """
    Read api_registry.yaml (via yaml_loader), instantiate all client_classes,
    store them in the global _API_CLIENTS, and return that dict.
    If already loaded, just return the cached dict.
    """
    global _API_CLIENTS
    if _API_CLIENTS:
        return _API_CLIENTS

    # 1) Load the raw YAML dict (filename → parsed dict)
    raw_registry = load_config_yaml(_API_REGISTRY_FILENAME)
    # raw_registry should look like { "weaviate": { client_class: "...", init_args: { ... } }, "pinecone": {...} }

    # clients: Dict[str, Any] = {}
    for name, cfg in raw_registry.items():
        if isinstance(cfg, dict) and "client_class" in cfg:
            # clients[name] = _instantiate_client(name, cfg)
            _API_CLIENTS[name] = _instantiate_client(name, cfg)
        else:
            # You can choose to raise an error or skip entries that do not define client_class
            raise RuntimeError(f"Entry '{name}' in { _API_REGISTRY_FILENAME } is missing 'client_class'")

    # _API_CLIENTS = clients
    return _API_CLIENTS

def get_api_client(client_name: str) -> Any:
    """
    Return a single client instance by name (e.g. "weaviate", "pinecone", etc.).
    If not already instantiated, load_all_api_clients() will populate _API_CLIENTS.
    Raises KeyError if no such name exists in api_registry.yaml.
    """
    if not _API_CLIENTS:
        load_all_api_clients()

    try:
        return _API_CLIENTS[client_name]
    except KeyError:
        raise KeyError(f"No API client named {client_name!r} (check api_registry.yaml)")


def get_api_client_with_namespace(client_name: str, namespace: str = "global") -> Any:
    """
    Retrieve API client instance by name and optional namespace (agent folder).
    Defaults to "global" namespace.
    """
    if not _API_CLIENTS:
        load_all_api_clients()

    try:
        clients_in_namespace = _API_CLIENTS.get(namespace)
        if not clients_in_namespace:
            raise KeyError(f"No API clients loaded for namespace '{namespace}'")

        client = clients_in_namespace.get(client_name)
        if client is None:
            raise KeyError(f"API client '{client_name}' not found in namespace '{namespace}'")
        return client
    except KeyError:
        raise KeyError(f"No API client named {client_name!r} (check api_registry.yaml)")

def reload_api_clients() -> Dict[str, Any]:
    """
    Force‐rebuild every client (e.g. if api_registry.yaml changed on disk).
    Clears the cache and re‐instantiates all entries.
    """
    global _API_CLIENTS
    _API_CLIENTS = {}
    return load_all_api_clients()


def load_api_clients_grouped_by_agent(agents_root_dir=_AGENT_DIR):
    """
    Auto-detect agent folders under `agents_root_dir` that have api_registry.yaml,
    load global clients, then load & instantiate each agent's clients grouped by agent name.
    Returns a dict:
        {
          "global": {client_name: instance, ...},
          "agent1": {client_name: instance, ...},
          ...
        }
    """
    global _API_CLIENTS

    # 1) Load global API clients (flat dict)
    global_clients = load_all_api_clients()
    _API_CLIENTS["global"] = global_clients

    # 2) Scan agents_root_dir for subfolders with api_registry.yaml
    for entry in os.listdir(agents_root_dir):
        agent_folder_path = os.path.join(agents_root_dir, entry)
        if not os.path.isdir(agent_folder_path):
            continue  # skip files, only dirs
        print(agent_folder_path)
        agent_api_yaml_path = os.path.join(agent_folder_path, "api_registry.yaml")
        if not os.path.isfile(agent_api_yaml_path):
            continue  # skip if no api_registry.yaml in this folder

        # Load and instantiate agent clients from YAML
        agent_clients_config = load_config_yaml(agent_api_yaml_path)
        agent_clients_instances = {}

        for client_name, client_cfg in agent_clients_config.items():
            instance = _instantiate_client(client_name, client_cfg)
            agent_clients_instances[client_name] = instance

        _API_CLIENTS[entry] = agent_clients_instances

    return _API_CLIENTS


def get_llms_for_agent(agent_name: str):
    """
    :param agent_name:
    agent_name: Agent1-5
    :return: llm_clients as dict
    """
    agent_registry = list_registered_agents()  # your agent configs

    if agent_name not in agent_registry:
        raise ValueError(f"Agent '{agent_name}' not found in agent registry.")

    agent_cfg = agent_registry[agent_name]

    llm_key_mapping = agent_cfg.get("llm_keys")
    if llm_key_mapping is None:
        # Could be missing or empty
        print(f"Warning: Agent '{agent_name}' has no 'llm_keys' defined.")
        return {}

    if not isinstance(llm_key_mapping, dict):
        raise TypeError(f"'llm_keys' for agent '{agent_name}' must be a dict mapping friendly names to client keys.")

    missing_clients = [client_key for client_key in llm_key_mapping.values() if client_key not in _API_CLIENTS]
    if missing_clients:
        print(f"Warning: The following client keys for agent '{agent_name}' are missing in _API_CLIENTS: {missing_clients}")

    # Build llm_clients dict with only existing clients
    llm_clients = {
        friendly_name: _API_CLIENTS[client_key]
        for friendly_name, client_key in llm_key_mapping.items()
        if client_key in _API_CLIENTS
    }

    return llm_clients


if __name__ == "__main__":
    all_clients = load_all_api_clients()
    print("all_clients", all_clients)
    print("Loaded API clients:", list(all_clients.keys()))

    agent1_llm_clients = get_llms_for_agent("Agent1")
    print("agent1_llm_clients", agent1_llm_clients)
    llm_generic = agent1_llm_clients["generic_json"]
    print("llm_generic", llm_generic)