"""
Meridian — Party Validation Coded Agent
LlamaIndex Workflow for trade compliance screening.

Input:  {"shipper": str, "consignee": str, "vessel_operator": str}
Output: {"partyResult": str, "partyComment": str, "partyScore": float}

Internal verdict → flat partyResult (set by the flatten() postprocess step):
    CLEAR           → partyResult: PASS
    POSSIBLE_MATCH  → partyResult: REVIEW
    CONFIRMED_MATCH → partyResult: FAIL

The ReAct loop and matching logic are unchanged — only the final return is
reshaped so every Maestro rule is a one-liner (`vars.partyResult == "PASS"`).
"""

import json
import re

from llama_index.core.llms import ChatMessage
from llama_index.core.tools import ToolSelection
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from pydantic import Field

from uipath_llamaindex.llms import BedrockModel
from uipath_llamaindex.llms.bedrock import UiPathChatBedrockConverse

from tools import party_validation_tool, list_version_tool


# ── LLM provider ─────────────────────────────────────────────────────────────
llm = UiPathChatBedrockConverse(model=BedrockModel.anthropic_claude_haiku_4_5)


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
"""

MAX_RESPONSE_LENGTH = 5000

tools = [party_validation_tool, list_version_tool]
tools_by_name = {t.metadata.name: t for t in tools}


# ── Output flattening ────────────────────────────────────────────────────────
# Maps the existing tool verdict to the flat shape Maestro rules expect.
# Internal logic (matching.py thresholds, denied list, ReAct loop) is unchanged.

STATUS_MAP = {
    "CLEAR":           "PASS",
    "POSSIBLE_MATCH":  "REVIEW",
    "CONFIRMED_MATCH": "FAIL",
}


def flatten(overall_status: str, party_results: dict) -> dict:
    """
    Collapse the per-party screening dict to three flat fields:
      partyResult  : PASS / REVIEW / FAIL
      partyComment : one human-readable sentence
      partyScore   : the worst party's score (0.0-1.0, highest score = worst)

    party_results is a dict keyed by role (shipper/consignee/vessel_operator),
    each value carrying name/status/score/matchedAgainst/reason.
    """
    values = [v for v in party_results.values() if isinstance(v, dict) and "score" in v]
    if not values:
        # Defensive: no per-party detail to summarise.
        return {
            "partyResult":  STATUS_MAP.get(overall_status, "REVIEW"),
            "partyComment": "Screening completed without per-party detail.",
            "partyScore":   0.0,
        }

    # Worst party = highest score (closer to a denied-party match).
    worst = max(values, key=lambda r: r.get("score", 0.0))

    if overall_status == "CLEAR":
        comment = "All parties clear against denied-party list."
    else:
        comment = (
            f"{worst.get('name', 'Party')} scored {worst.get('score', 0.0):.2f} "
            f"vs '{worst.get('matchedAgainst') or 'denied entry'}' "
            f"({worst.get('reason') or 'no reason given'})."
        )

    return {
        "partyResult":  STATUS_MAP.get(overall_status, "REVIEW"),
        "partyComment": comment,
        "partyScore":   round(float(worst.get("score", 0.0)), 3),
    }


# ── Workflow events ──────────────────────────────────────────────────────────

class QueryEvent(StartEvent):
    shipper: str = Field(description="Name of the shipping party")
    consignee: str = Field(description="Name of the receiving party")
    vessel_operator: str = Field(description="Name of the vessel operator")
    list_type: str = Field(
        default="",
        description="Optional list selector. Use 'escalation' for the escalation CSV; blank/missing uses the default denied list.",
    )


class LLMInputEvent(Event):
    pass


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class AgentOutputEvent(Event):
    response: str


class ResponseEvent(StopEvent):
    partyResult: str = Field(description="PASS | REVIEW | FAIL")
    partyComment: str = Field(description="One human-readable sentence summarising the screening")
    partyScore: float = Field(description="Worst party score (0.0-1.0); 0.0 when CLEAR")


# ── Workflow ─────────────────────────────────────────────────────────────────

class PartyValidationAgent(Workflow):
    @step
    async def prepare(self, ctx: Context, ev: QueryEvent) -> LLMInputEvent:
        shipper = ev.shipper or "UNKNOWN"
        consignee = ev.consignee or "UNKNOWN"
        vessel_operator = ev.vessel_operator or "UNKNOWN"
        list_type = (ev.list_type or "").strip()

        query = (
            f"Screen these trade parties for denied-party compliance:\n"
            f"  Shipper:         {shipper}\n"
            f"  Consignee:       {consignee}\n"
            f"  Vessel Operator: {vessel_operator}\n"
            f"  List Type:       {list_type or '(default)'}\n"
            f"\n"
            f"Call validate_parties with shipper, consignee, vessel_operator, "
            f"and list_type='{list_type}'. Return the result as JSON."
        )
        await ctx.store.set("messages", [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=query),
        ])
        return LLMInputEvent()

    @step
    async def react_agent(
        self, ctx: Context, ev: LLMInputEvent
    ) -> ToolCallEvent | AgentOutputEvent:
        messages = await ctx.store.get("messages")
        response = await llm.achat_with_tools(tools, chat_history=messages)
        messages.append(response.message)
        await ctx.store.set("messages", messages)

        tool_calls = llm.get_tool_calls_from_response(response)
        if tool_calls:
            return ToolCallEvent(tool_calls=tool_calls)

        return AgentOutputEvent(response=response.message.content or "")

    @step
    async def tool_executor(self, ctx: Context, ev: ToolCallEvent) -> LLMInputEvent:
        messages = await ctx.store.get("messages")
        for call in ev.tool_calls:
            tool = tools_by_name[call.tool_name]
            result = tool.call(**call.tool_kwargs)
            messages.append(ChatMessage(
                role="tool",
                content=str(result),
                additional_kwargs={"tool_call_id": call.tool_id, "name": call.tool_name},
            ))
        await ctx.store.set("messages", messages)
        return LLMInputEvent()

    @step
    async def postprocess(self, ctx: Context, ev: AgentOutputEvent) -> ResponseEvent:
        raw = (ev.response or "").strip()
        result = None
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except json.JSONDecodeError:
                    result = None

        # Defensive branch — unparseable LLM output → REVIEW per spec.
        if not isinstance(result, dict) or "overallStatus" not in result:
            return ResponseEvent(
                partyResult="REVIEW",
                partyComment="Screening inconclusive; manual review required.",
                partyScore=0.0,
            )

        overall_status = result.get("overallStatus", "")
        party_results = result.get("partyResults", {}) or {}

        # Map verdict + worst-party detail to the flat output shape.
        flat = flatten(overall_status, party_results)

        return ResponseEvent(
            partyResult=flat["partyResult"],
            partyComment=flat["partyComment"],
            partyScore=flat["partyScore"],
        )


# ── Exported workflow instance (referenced by llama_index.json) ─────────────
agent = PartyValidationAgent(timeout=120, verbose=False)
