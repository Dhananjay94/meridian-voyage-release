"""
Meridian — Party Validation: LlamaIndex ReAct Agent
"""

import json
import re

from llama_index.core.agent import ReActAgent
from uipath_llamaindex import get_llm

from tools import party_validation_tool, list_version_tool


SYSTEM_PROMPT = """
You are the Meridian Party Validation Agent, a trade compliance screening component
in a case management system for maritime voyage release.

YOUR ONLY JOB:
1. Receive a screening request containing shipper, consignee, and vessel_operator names.
2. Call the validate_parties tool with those exact names.
3. Return the tool JSON output verbatim as your final answer.

STRICT RULES:
- Always call validate_parties. Never skip it.
- Do not invent or guess compliance verdicts. The tool result IS the verdict.
- Do not rephrase CLEAR, POSSIBLE_MATCH, or CONFIRMED_MATCH — return these exact strings.
- If a party name is missing from the input, substitute the string UNKNOWN for that field.
- Your final response must be a valid JSON object matching the tool output schema.
- Do not add commentary, explanations, or preamble around the JSON.

OUTPUT SCHEMA (return exactly this structure):
{
  "overallStatus": "CLEAR | POSSIBLE_MATCH | CONFIRMED_MATCH",
  "routeTo": "none | HUMAN_REVIEW | ON_HOLD",
  "partyResults": {
    "shipper":         {"name": str, "status": str, "score": float, "matchedAgainst": str or null, "reason": str or null, "listVersion": str},
    "consignee":       {"name": str, "status": str, "score": float, "matchedAgainst": str or null, "reason": str or null, "listVersion": str},
    "vessel_operator": {"name": str, "status": str, "score": float, "matchedAgainst": str or null, "reason": str or null, "listVersion": str}
  }
}
"""


def build_agent() -> ReActAgent:
    llm = get_llm()
    return ReActAgent.from_tools(
        tools=[party_validation_tool, list_version_tool],
        llm=llm,
        verbose=True,
        max_iterations=5,
        system_prompt=SYSTEM_PROMPT,
    )


def run(input_data: dict) -> dict:
    shipper         = input_data.get("shipper",         "UNKNOWN")
    consignee       = input_data.get("consignee",       "UNKNOWN")
    vessel_operator = input_data.get("vessel_operator", "UNKNOWN")

    query = (
        f"Screen these trade parties for denied-party compliance:\n"
        f"  Shipper:         {shipper}\n"
        f"  Consignee:       {consignee}\n"
        f"  Vessel Operator: {vessel_operator}\n"
        f"\n"
        f"Call validate_parties and return the result as JSON."
    )

    agent    = build_agent()
    response = agent.chat(query)
    raw      = str(response).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {
            "overallStatus": "ERROR",
            "routeTo":       "HUMAN_REVIEW",
            "partyResults":  {},
            "error":         f"Agent response could not be parsed: {raw[:500]}",
        }
