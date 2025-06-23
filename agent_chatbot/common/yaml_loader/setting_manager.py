# agent_chatbot/common/settings.py
from agent_chatbot.common.yaml_loader.yaml_loader import load_config_yaml

_SETTING_REGISTRY_FILENAME = "setting_registry.yaml"
_cached_settings = None

def load_all_settings():
    """
    Load and cache the entire settings from setting_registry.yaml.
    Subsequent calls return the same dict.
    """
    global _cached_settings
    if _cached_settings is None:
        _cached_settings = load_config_yaml(_SETTING_REGISTRY_FILENAME)
    return _cached_settings

def get_setting(key: str):
    """
    Return the value for `key` from the cached settings.
    If not yet loaded, first calls load_all_settings().
    """
    settings = load_all_settings()
    return settings[key]
