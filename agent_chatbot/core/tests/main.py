# core/main.py

import argparse
import os
import sys

# ── INSERT THESE FOUR LINES ──────────────────────────────────────────────
# Calculate the “parent of core/” (i.e. agent-chatbot/)
this_file = os.path.abspath(__file__)        # …/agent-chatbot/core/main.py
core_folder = os.path.dirname(this_file)     # …/agent-chatbot/core
project_root = os.path.dirname(core_folder)  # …/agent-chatbot
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agent_loader import (
    list_registered_agents,
    get_agent_callable,
    reload_changed_agent_modules,
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent",
        default="Agent5",   # ←– whatever agent you want as a quick default
        help="The agent name (e.g. Agent5). If omitted, defaults to Agent5."
    )
    parser.add_argument("--payload", required=False, help="JSON‐encoded payload or input text")
    args = parser.parse_args()

    # (1) Reload any changed modules under agents/
    reload_result = reload_changed_agent_modules("agents")
    if reload_result["added_modules"] or reload_result["reloaded_modules"]:
        print("Reloaded modules:", reload_result)

    # (2) Look up the registry entry for args.agent
    registry = list_registered_agents()
    entry = registry.get(args.agent)
    if entry is None:
        print(f"[!] Agent '{args.agent}' not found in agent_registry.yaml.")
        return

    print(f"[*] Found registry entry for {args.agent}:\n    {entry}")

    # (3) Dynamically import the agent’s class or function
    AgentOrFunc = get_agent_callable(args.agent)
    print(f"[*] Imported Agent or function:\n    {AgentOrFunc}")

    # (4) Build a dummy payload (or parse --payload if provided)
    dummy_payload_text = args.payload or "{}"
    try:
        import json
        payload_data = json.loads(dummy_payload_text)
    except Exception:
        payload_data = {"raw_payload": dummy_payload_text}

    # (5) Call the agent
    if isinstance(AgentOrFunc, type):
        print("[*] Detected a class. Instantiating with no args…")
        agent_instance = AgentOrFunc()
        try:
            result = agent_instance.dispatch(payload_data)
        except TypeError as e:
            result = f"[!] dispatch() failed: {e}"
    else:
        print("[*] Detected a function. Calling directly…")
        try:
            result = AgentOrFunc(payload_data)
        except TypeError as e:
            result = f"[!] function call failed: {e}"

    print("[*] Result:", result)


if __name__ == "__main__":
    print("list_registered_agents()", list_registered_agents())
