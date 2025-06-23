import yaml, importlib, os
from dotenv import load_dotenv
from pathlib import Path

# from chatbot.agent_registry import load_all_agents_and_controller

# Load environment variables from .env file
load_dotenv()

# Get root path
# In a script __file__ exists; in interactive it doesn’t
if "__file__" in globals():
    BASE_DIR = Path(__file__).resolve().parent.parent
else:
    BASE_DIR = Path.cwd()
CLIENT_DIR = BASE_DIR / "clients"

API_FILE     = CLIENT_DIR / "api_registry.yaml"
SETTING_FILE = CLIENT_DIR / "setting_registry.yaml"
AGENT_FILE   = CLIENT_DIR / "agent_registry.yaml"
#%%
_apis = None
_settings = None
_agents = None


def load_apis(path: Path | str = None) -> dict:
    """
    Parse api_registry.yaml, instantiate all client_class entries,
    update the global _apis, and return it.
    """
    global _apis
    p   = Path(path or API_FILE)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    clients = {}
    for name, cfg in raw.items():
        if isinstance(cfg, dict) and "client_class" in cfg:
            mod, cls = cfg["client_class"].rsplit(".", 1)
            factory  = getattr(importlib.import_module(mod), cls)
            init_args = {}
            for k, v in cfg.get("init_args", {}).items():
                if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                    init_args[k] = os.getenv(v[2:-1])
                else:
                    init_args[k] = v
            clients[name] = factory(**init_args)
    _apis = clients
    return _apis


def load_settings(path: Path | str = None) -> dict:
    """
    Parse setting_registry.yaml, update global _settings, and return it.
    """
    global _settings
    p = Path(path or SETTING_FILE)
    _settings = yaml.safe_load(p.read_text(encoding="utf-8"))
    return _settings


def load_agents_config(path: Path | str = None) -> dict:
    """
    Parse agent_registry.yaml into the AGENTS manifest dict,
    reload any Python agent modules, update global _agents, and return it.
    """
    global _agents
    p = Path(path or AGENT_FILE)
    manifest = yaml.safe_load(p.read_text(encoding="utf-8"))
    _agents = manifest
    return _agents


def force_load_services() -> tuple[dict, dict, dict]:
    """
    Unconditionally reload APIs, settings, and agents.
    """
    # apis     = load_apis()
    # settings = load_settings()
    agents   = load_agents_config()
    return None, None, agents


def safe_load_services() -> tuple[dict, dict, dict]:
    """
    Load all three once (on first call) and cache; subsequent calls return
    the cached versions unless you explicitly call force_load_services().
    """
    global _apis, _settings, _agents
    if _apis is None or _settings is None or _agents is None:
        return force_load_services()
    return None, None, _agents


# ─── Module‐level singletons ──────────────────────────────────────────────────
APIS, SETTINGS, AGENTS = safe_load_services()
# print(APIS)
# print(SETTINGS)
# print(AGENTS)
# APIS, SETTINGS, AGENTS = None, None, None