"""
Meridian — Party Validation: LlamaIndex Tool Definitions

These are the tools the ReAct agent can call. The deterministic matching
logic lives in matching.py — this file only wraps it so LlamaIndex can
invoke it and log the reasoning trace.

Two tools:
  - validate_parties   : screen all three parties at once, return overall verdict
  - get_list_version   : returns the current list version (useful for audit logs)
"""

import csv
import json
import os
from llama_index.core.tools import FunctionTool

from matching import score_against_list


# ── List loader ─────────────────────────────────────────────────────────────

# Map list_type label → CSV filename
LIST_TYPE_MAP = {
    "":           "denied_party_list.csv",
    "default":    "denied_party_list.csv",
    "normal":     "denied_party_list.csv",
    "escalation": "denied_party_list_escalation.csv",
}


def _resolve_filename(list_type: str = "") -> str:
    """Resolve a list_type label to a CSV filename. Unknown labels fall back to the default list."""
    return LIST_TYPE_MAP.get((list_type or "").strip().lower(), "denied_party_list.csv")


def _load_denied_list(filename: str = "denied_party_list.csv") -> list[dict]:
    """
    Load the denied party CSV from the agent's directory.
    Switch to denied_party_list_escalation.csv for the demo escalation paths.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Tool functions (plain Python — LlamaIndex will wrap these) ───────────────

def validate_parties(
    shipper: str,
    consignee: str,
    vessel_operator: str,
    list_type: str = "",
) -> str:
    """
    Screen a shipper, consignee, and vessel_operator against the denied party list.

    Performs token-set Jaccard matching against the selected denied party list.
    Returns a JSON string containing:
      - overallStatus  : CLEAR | POSSIBLE_MATCH | CONFIRMED_MATCH
      - routeTo        : none | HUMAN_REVIEW | ON_HOLD
      - partyResults   : per-party detail (status, score, matchedAgainst, reason)

    Thresholds: score < 0.30 → CLEAR, score >= 0.75 → CONFIRMED_MATCH, else POSSIBLE_MATCH.
    Overall status = worst individual status.

    Args:
        shipper:         Name of the shipping party.
        consignee:       Name of the receiving party.
        vessel_operator: Name of the vessel operator.
        list_type:       Which denied list to use. "escalation" loads
                         denied_party_list_escalation.csv; "" or anything else
                         loads the default denied_party_list.csv.
    """
    denied = _load_denied_list(_resolve_filename(list_type))

    party_results = {
        "shipper":         score_against_list(shipper,         denied),
        "consignee":       score_against_list(consignee,       denied),
        "vessel_operator": score_against_list(vessel_operator, denied),
    }

    statuses = [r["status"] for r in party_results.values()]

    if "CONFIRMED_MATCH" in statuses:
        overall = "CONFIRMED_MATCH"
    elif "POSSIBLE_MATCH" in statuses:
        overall = "POSSIBLE_MATCH"
    else:
        overall = "CLEAR"

    route_map = {
        "CLEAR":            "none",
        "POSSIBLE_MATCH":   "HUMAN_REVIEW",
        "CONFIRMED_MATCH":  "ON_HOLD",
    }

    result = {
        "overallStatus": overall,
        "routeTo":       route_map[overall],
        "partyResults":  party_results,
    }
    return json.dumps(result)


def get_list_version(list_type: str = "") -> str:
    """
    Return the version of the denied party list currently loaded.
    Useful for stamping the assumption ledger entry.

    Args:
        list_type: Which denied list to inspect ("escalation" or default).
    """
    denied = _load_denied_list(_resolve_filename(list_type))
    version = denied[0].get("list_version", "unknown") if denied else "unknown"
    return json.dumps({"listVersion": version, "entryCount": len(denied)})


# ── LlamaIndex FunctionTool wrappers ─────────────────────────────────────────

party_validation_tool = FunctionTool.from_defaults(
    fn=validate_parties,
    name="validate_parties",
    description=(
        "Screen trade parties against the denied party list. "
        "Provide shipper, consignee, and vessel_operator as separate string arguments. "
        "Optional list_type: 'escalation' selects the escalation CSV; empty or omitted uses the default list. "
        "Returns JSON with overallStatus (CLEAR/POSSIBLE_MATCH/CONFIRMED_MATCH), "
        "routeTo directive, and per-party match details. "
        "Call this tool first and always for any party screening request."
    ),
)

list_version_tool = FunctionTool.from_defaults(
    fn=get_list_version,
    name="get_list_version",
    description=(
        "Returns the version string and entry count of the currently loaded denied party list. "
        "Optional list_type: 'escalation' inspects the escalation CSV; empty/omitted uses the default. "
        "Call this when the caller needs the list version for audit or ledger stamping."
    ),
)
