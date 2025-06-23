# agent-chatbot/common/yaml_loader.py

import yaml
from pathlib import Path
from typing import Any, Dict

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

_cache: Dict[str, Any] = {}
_mtimes: Dict[str, float] = {}
_cached_settings: Dict[str, Any] = {}


def load_config_yaml(filename: str) -> Any:
    """
    Load and cache: agent-chatbot/config/filename.
    Re‐load if file’s mtime changed.
    """
    path = _CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    current_mtime = path.stat().st_mtime
    cached_mtime = _mtimes.get(filename)

    if (filename not in _cache) or (cached_mtime != current_mtime):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        _cache[filename] = data
        _mtimes[filename] = current_mtime

    return _cache[filename]

def preload_all_yaml() -> Dict[str, Any]:
    """
    Read every .yaml under config/ into the _cache at once.
    Returns the entire cache dict mapping filename → parsed data.
    """
    for filepath in _CONFIG_DIR.glob("*.yaml"):
        fname = filepath.name
        # Calling load_config_yaml will cache & track mtime
        load_config_yaml(fname)
    return _cache
