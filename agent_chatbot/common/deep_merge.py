from typing import Dict, Any


def deep_merge(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge `new` into `old`:

    - If both `old[key]` and `new[key]` are dicts: recurse.
    - If both are lists: union them (keep all unique items).
    - Otherwise: overwrite `old[key]` with `new[key]`.

    Returns the merged dictionary `old`.
    """
    for key, new_val in new.items():
        if key in old and isinstance(old[key], dict) and isinstance(new_val, dict):
            deep_merge(old[key], new_val)
        elif key in old and isinstance(old[key], list) and isinstance(new_val, list):
            # Union lists without duplicates
            merged_list = old[key] + [item for item in new_val if item not in old[key]]
            old[key] = merged_list
        else:
            # Replace or add
            old[key] = new_val
    return old