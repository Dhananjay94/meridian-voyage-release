"""
Meridian — Party Validation: Token-Set Matching Engine

Pure Python, zero dependencies. This is the core matching logic extracted
from the FastAPI service (main__2_.py) so it can be used as a LlamaIndex
tool without any HTTP layer.

DO NOT change CLEAR_BELOW or CONFIRMED_AT_OR_ABOVE without updating Maestro
stage rules — they are contracts between this agent and the case flow.
"""

# ── Thresholds (the contract) ───────────────────────────────────────────────
CLEAR_BELOW            = 0.30   # score < 0.30           → CLEAR
CONFIRMED_AT_OR_ABOVE  = 0.75   # score >= 0.75           → CONFIRMED_MATCH
                                 # 0.30 <= score < 0.75   → POSSIBLE_MATCH

# Company-type words that add noise to token comparison and should be ignored
STOPWORDS = {
    "sa", "sal", "llc", "fze", "ltd", "gmbh", "oao", "corp", "co", "inc",
    "plc", "holdings", "agency", "bureau", "group", "the", "and", "of",
    "trading", "limited",
}


def _tokens(name: str) -> set:
    """Tokenise a party name: lowercase, strip punctuation, remove stopwords."""
    cleaned = name.lower().replace(",", " ").replace(".", " ")
    return {w for w in cleaned.split() if w not in STOPWORDS and len(w) > 1}


def _overlap(a: str, b: str) -> float:
    """Jaccard token-set overlap between two party name strings."""
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if (ta and tb) else 0.0


def _classify(score: float) -> str:
    if score < CLEAR_BELOW:
        return "CLEAR"
    if score < CONFIRMED_AT_OR_ABOVE:
        return "POSSIBLE_MATCH"
    return "CONFIRMED_MATCH"


def score_against_list(name: str, denied_parties: list[dict]) -> dict:
    """
    Score a single party name against every entry in the denied list.
    Returns the best match and its classification.

    Args:
        name:           The party name to screen (e.g. "Aegean Bulk Traders SA").
        denied_parties: List of dicts with keys: party_name, list_version, reason.

    Returns:
        {
          "name":          str  — the input name,
          "status":        str  — CLEAR | POSSIBLE_MATCH | CONFIRMED_MATCH,
          "score":         float,
          "matchedAgainst": str | None,
          "reason":        str | None,
          "listVersion":   str,
        }
    """
    best_score = 0.0
    best_entry = None

    for entry in denied_parties:
        s = _overlap(name, entry["party_name"])
        if s > best_score:
            best_score = s
            best_entry = entry

    status = _classify(best_score)
    # Pull list_version from the loaded CSV even when no match is found
    # (all entries share the same version; "unknown" only when CSV is empty)
    if best_entry:
        list_ver = best_entry["list_version"]
    elif denied_parties:
        list_ver = denied_parties[0].get("list_version", "unknown")
    else:
        list_ver = "unknown"

    return {
        "name":          name,
        "status":        status,
        "score":         round(best_score, 3),
        "matchedAgainst": best_entry["party_name"] if (best_entry and status != "CLEAR") else None,
        "reason":        best_entry["reason"]      if (best_entry and status != "CLEAR") else None,
        "listVersion":   list_ver,
    }
