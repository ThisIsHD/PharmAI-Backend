from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from tools import tavily_search, stub_evidence

# Load environment variables
load_dotenv()

# -----------------------------
# LangChain Tool Wrappers
# -----------------------------
@tool("web_search")
def web_search_tool(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Web search using Tavily. Returns a list of evidence dicts."""
    ev = tavily_search(query=query, max_results=max_results)
    return [e.model_dump() for e in ev]


@tool("stub_evidence")
def stub_evidence_tool(query: str) -> List[Dict[str, Any]]:
    """Deterministic fallback evidence tool (offline/demo)."""
    ev = stub_evidence(query=query)
    return [e.model_dump() for e in ev]


TOOLS = [web_search_tool, stub_evidence_tool]


# -----------------------------
# LangGraph State
# -----------------------------
class PharmAIState(MessagesState):
    session_id: Optional[str]
    user_query: str
    decision_brief: str
    citations: List[str]
    confidence_score: float
    tool_loops: int  # safety counter


# -----------------------------
# Guardrails + Prompts
# -----------------------------
SYSTEM_PROMPT = """You are PharmAI Navigator, an evidence-grounded diligence assistant for drug/asset evaluation.

Your job:
Turn a query like "Assess {Drug} for {Indication}" into a decision-grade brief.

Guardrails (STRICT):
- Do NOT invent specific facts (approval dates, trial names, endpoints, statistics, patent expiry) without evidence.
- If you state a concrete number/date/claim, it MUST be supported by tool evidence (web_search output).
- Prefer using tools for factual claims. If tools are unavailable/insufficient, say so clearly and list what is missing.
- Be concise, structured, and decision-oriented.
- Avoid medical advice; present as diligence/analysis.

Citations policy:
- The final response's "Citations" section is handled by the system. Do not create your own custom citation list.
"""

FINAL_PROMPT = """Write the FINAL decision brief with these sections:

1) Executive Recommendation (1–2 lines)
2) Scientific Rationale (bullets)
3) Clinical Evidence Snapshot (bullets)
4) IP / Exclusivity Quick View (bullets)
5) Market / SoC Snapshot (bullets)
6) Key Risks + Next Actions (bullets)

Rules:
- If evidence is insufficient, include "Evidence Gaps" with bullets.
- Do NOT add a citations section yourself; the system will append it.
Return plain text only.
"""

# Placeholder detection to avoid wasting tokens on "Drug X / Indication Y"
PLACEHOLDER_PATTERNS = [
    r"\bdrug\s*x\b",
    r"\bindication\s*y\b",
    r"\bdrug\s*name\b",
    r"\bindication\s*name\b",
]
def _looks_like_placeholder(q: str) -> bool:
    ql = (q or "").strip().lower()
    return any(re.search(p, ql) for p in PLACEHOLDER_PATTERNS)


def _build_model() -> ChatAnthropic:
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-latest")
    return ChatAnthropic(
        model=model_name,
        temperature=0.2,
        max_tokens=1200,
    ).bind_tools(TOOLS)


# Safety cap to avoid endless tool loops
MAX_TOOL_LOOPS = int(os.getenv("MAX_TOOL_LOOPS", "4"))


def llm_call(state: PharmAIState) -> Dict[str, Any]:
    """
    Calls Claude with tool schemas attached.
    Returns new messages to append into state["messages"].
    """
    llm = _build_model()
    messages: List[BaseMessage] = state["messages"]

    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    tool_loops = state.get("tool_loops", 0)
    if tool_loops >= MAX_TOOL_LOOPS:
        # Stop tool-calling loop and force synthesis
        stop_msg = HumanMessage(
            content=(
                "Stop calling tools now. Proceed to final synthesis using what you already have. "
                "If evidence is insufficient, clearly list Evidence Gaps."
            )
        )
        messages = messages + [stop_msg]

    resp = llm.invoke(messages)
    return {"messages": [resp]}


# -----------------------------
# Citations extraction (tool-only)
# -----------------------------
def _clean_url(u: str) -> str:
    return u.strip().strip("),.]}\"'")

def _extract_citations_from_messages(messages: List[BaseMessage]) -> List[str]:
    """
    Tool-only citation extraction (single source of truth):
    - ONLY reads ToolMessage contents (actual tool outputs).
    - If tool output is JSON (list/dict), pull `source` fields.
    - Fallback: regex URL extraction from tool text.
    """
    citations: List[str] = []
    url_re = re.compile(r"https?://[^\s\]\)\}\",']+")

    for m in messages:
        if not isinstance(m, ToolMessage):
            continue

        content = getattr(m, "content", None)
        if not content:
            continue

        if isinstance(content, str):
            parsed = None
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = None

            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        src = item.get("source")
                        if isinstance(src, str) and src.startswith(("http://", "https://")):
                            citations.append(_clean_url(src))
            elif isinstance(parsed, dict):
                src = parsed.get("source")
                if isinstance(src, str) and src.startswith(("http://", "https://")):
                    citations.append(_clean_url(src))

            for u in url_re.findall(content):
                citations.append(_clean_url(u))

    # De-duplicate
    seen = set()
    out = []
    for c in citations:
        # drop clearly broken/truncated URLs
        if len(c) < 12:
            continue
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _append_citations_section(brief_text: str, citations: List[str]) -> str:
    """
    Enforces "single source of truth":
    - Removes any existing 'Citations' section the model may have produced
    - Appends citations derived from tool outputs only
    """
    text = (brief_text or "").strip()

    # Remove any model-generated citations section (best-effort)
    # (handles '## Citations' or 'Citations' headers)
    text = re.split(r"\n#{1,3}\s*Citations\s*\n|\nCitations\s*\n", text, maxsplit=1)[0].rstrip()

    if citations:
        lines = ["", "## Citations"]
        for i, c in enumerate(citations, 1):
            lines.append(f"{i}. {c}")
        text = text + "\n" + "\n".join(lines)
    else:
        text = text + "\n\n## Citations\n- (No external sources retrieved.)"

    return text


# -----------------------------
# Final Synthesis Node
# -----------------------------
def synthesize(state: PharmAIState) -> Dict[str, Any]:
    # Fast guardrail: placeholders -> short response without tool burn
    uq = state.get("user_query", "")
    if _looks_like_placeholder(uq):
        brief = (
            "# FINAL DECISION BRIEF\n\n"
            "I need the **actual drug name** and **specific indication** to perform diligence.\n\n"
            "## Evidence Gaps\n"
            "- Drug name (e.g., semaglutide)\n"
            "- Indication (e.g., obesity)\n"
            "- Trial/program context (if any)\n"
        )
        return {
            "decision_brief": _append_citations_section(brief, []),
            "citations": [],
            "messages": [HumanMessage(content="(placeholder query detected; returned guardrail response)")],
        }

    llm = _build_model()
    messages: List[BaseMessage] = state["messages"]
    messages = messages + [HumanMessage(content=FINAL_PROMPT)]

    resp = llm.invoke(messages)

    tool_citations = _extract_citations_from_messages(state["messages"])
    brief_text = resp.content if isinstance(resp.content, str) else str(resp.content)
    brief_text = _append_citations_section(brief_text, tool_citations)

    return {
        "decision_brief": brief_text,
        "citations": tool_citations,
        "messages": [resp],
    }


# -----------------------------
# Build + Compile Graph
# -----------------------------
def build_graph():
    g = StateGraph(PharmAIState)

    g.add_node("llm_call", llm_call)

    tool_node = ToolNode(TOOLS)
    g.add_node("tools", tool_node)

    g.add_node("synthesize", synthesize)

    g.add_edge(START, "llm_call")

    g.add_conditional_edges(
        "llm_call",
        tools_condition,
        {
            "tools": "tools",
            END: "synthesize",
        },
    )

    def bump_tool_loop(state: PharmAIState) -> Dict[str, Any]:
        return {"tool_loops": state.get("tool_loops", 0) + 1}

    g.add_node("bump_tool_loop", bump_tool_loop)
    g.add_edge("tools", "bump_tool_loop")
    g.add_edge("bump_tool_loop", "llm_call")

    g.add_edge("synthesize", END)

    return g.compile()


# -----------------------------
# Test execution
# -----------------------------
if __name__ == "__main__":
    print("Building PharmAI Navigator graph...")
    graph = build_graph()
    print("Graph compiled successfully!")

    test_query = "Assess donanemab for early Alzheimer's disease"
    print(f"\nRunning test query: {test_query}")

    result = graph.invoke({
        "messages": [HumanMessage(content=test_query)],
        "user_query": test_query,
        "tool_loops": 0,
    })

    print("\n" + "=" * 60)
    print("DECISION BRIEF:")
    print("=" * 60)
    print(result.get("decision_brief", "No brief generated"))

    print("\n" + "=" * 60)
    print("CITATIONS (tool-only):")
    print("=" * 60)
    for i, citation in enumerate(result.get("citations", []), 1):
        print(f"{i}. {citation}")
