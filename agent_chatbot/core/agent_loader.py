# core/agent_loader.py

import yaml
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict

# Determine the folder containing this file (core/), then go up one level to agent-chatbot/
_THIS_FILE = Path(__file__).resolve()
CORE_FOLDER = _THIS_FILE.parent          # …\agent-chatbot\core
PROJECT_ROOT = CORE_FOLDER.parent        # …\agent-chatbot

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # 2 cấp lên, tương đương agent_chatbot/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_AGENT_REGISTRY_PATH = PROJECT_ROOT / "config" / "agent_registry.yaml"
_API_REGISTRY_PATH   = PROJECT_ROOT / "config" / "api_registry.yaml"

# Internal cache of the loaded YAML data
_agent_registry_data: Dict[str, Any] = {}
# _api_registry_data: Dict[str, Any] = {}

def _load_agent_registry_yaml() -> Dict[str, Any]:
    """
    Reads config/agent_registry.yaml once and caches it.
    Expected format:
    agents:
      Agent1:
        class: "agents.agent1.agent.Agent1"
        llm_key: "agent1_dispatch"
      Agent5:
        class: "agents.agent5.agent.agent5_simulated_checkout"
        llm_key: "agent5_dispatch"
      ...
    """
    global _agent_registry_data
    if not _agent_registry_data:
        raw = Path(_AGENT_REGISTRY_PATH).read_text(encoding="utf-8")
        doc = yaml.safe_load(raw)
        if "agents" not in doc or not isinstance(doc["agents"], dict):
            raise RuntimeError(f"{_AGENT_REGISTRY_PATH} must contain top-level 'agents: {{ … }}'")
        _agent_registry_data = doc["agents"]
    return _agent_registry_data

def list_registered_agents() -> Dict[str, Dict[str, Any]]:
    """
    Returns a dictionary mapping agent names → metadata dict (class path, llm_key, etc.).
    """
    return _load_agent_registry_yaml()


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    registry = _load_agent_registry_yaml()
    if agent_name not in registry:
        raise KeyError(f"No such agent in registry.yaml: '{agent_name}'")
    return registry[agent_name]


def get_agent_callable(agent_name: str) -> Callable[..., Any]:
    """
    Dynamically import and return the callable (class or function) for the given agent_name.

    For example, if agent_name="Agent5", the registry might say:
      class: "agents.agent5.agent.agent5_simulated_checkout"
    We will import module "agents.agent5.agent" and return attribute "agent5_simulated_checkout".
    """
    registry = _load_agent_registry_yaml()
    entry = registry.get(agent_name)
    if entry is None:
        raise KeyError(f"No such agent in registry.yaml: '{agent_name}'")

    class_path = entry.get("class")
    if not class_path or "." not in class_path:
        raise RuntimeError(f"Invalid 'class' path for agent '{agent_name}': {class_path!r}")

    module_name, attr_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    if not hasattr(module, attr_name):
        raise ImportError(f"{module_name!r} has no attribute {attr_name!r} for agent '{agent_name}'")

    return getattr(module, attr_name)

def reload_changed_agent_modules(package_name: str = "agents") -> Dict[str, list[str]]:
    """
    (Optional) Scan every .py file under the given package (e.g. 'agents'),
    check their file modification time, and reload any that changed.

    Returns a dict with keys:
      - 'added_modules': names of modules newly imported
      - 'reloaded_modules': names of modules that were reloaded
    """
    added, reloaded = [], []

    # Keep track of module → last seen mtime
    if not hasattr(reload_changed_agent_modules, "_module_mtimes"):
        reload_changed_agent_modules._module_mtimes = {}

    _module_mtimes: Dict[str, float] = reload_changed_agent_modules._module_mtimes

    # Helper to import or reload a given module (by full name and path)
    def _check_and_reload(full_name: str, file_path: Path):
        mtime = file_path.stat().st_mtime
        prev = _module_mtimes.get(full_name)

        if full_name not in sys.modules:
            importlib.import_module(full_name)
            added.append(full_name)
        elif prev is None or mtime != prev:
            importlib.reload(sys.modules[full_name])
            reloaded.append(full_name)

        _module_mtimes[full_name] = mtime

    # 1) Ensure the package itself is imported
    package = importlib.import_module(package_name)
    pkg_dir = Path(package.__path__[0])

    # 2) Walk all .py files directly under agents/ (no deeper recursion)
    for _, module_name, is_pkg in pkgutil.iter_modules([str(pkg_dir)]):
        full_name = f"{package_name}.{module_name}"
        module_fp = pkg_dir / f"{module_name}.py"
        if module_fp.exists():
            _check_and_reload(full_name, module_fp)

    return {"added_modules": added, "reloaded_modules": reloaded}


# def _load_api_registry_yaml() -> Dict[str, Any]:
#     global _api_registry_data
#     if not _api_registry_data:
#         raw = _API_REGISTRY_PATH.read_text(encoding="utf-8")
#         doc = yaml.safe_load(raw)
#         # assume it has top‐level “llms:” key
#         _api_registry_data = doc["llms"]
#     return _api_registry_data

if __name__ == "__main__":
    cfg = get_agent_callable("Agent3")
    print("cfg", cfg.__dict__)