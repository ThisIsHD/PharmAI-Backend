# tools.py
from typing import List, Dict, Any, Optional
import os
import uuid
from schemas import EvidenceItem, EvidenceType

# Tool 1: Tavily Web Search (Optional, real data)
def tavily_search(query: str, max_results: int = 5) -> List[EvidenceItem]:
    """
    Uses Tavily API to perform web search.
    Returns structured evidence items.
    """
    api_key = os.getenv("TAVILY_API_KEY")

    # If Tavily is not configured, gracefully fall back
    if not api_key:
        return [
            EvidenceItem(
                type=EvidenceType.OTHER,
                source="tavily_disabled",
                summary="Tavily API key not configured; search skipped.",
                confidence=0.0,
            )
        ]

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=query,
            max_results=max_results,
            include_raw_content=False,
        )

        evidence: List[EvidenceItem] = []

        for r in results.get("results", []):
            evidence.append(
                EvidenceItem(
                    type=EvidenceType.LITERATURE,
                    source=r.get("url", "unknown"),
                    summary=r.get("content", "")[:500],
                    confidence=0.6,
                    raw=r,
                )
            )

        return evidence

    except Exception as e:
        return [
            EvidenceItem(
                type=EvidenceType.OTHER,
                source="tavily_error",
                summary=f"Tavily search failed: {str(e)}",
                confidence=0.0,
            )
        ]

# Tool 2: Stub Evidence Generator (Offline / Demo)
def stub_evidence(query: str) -> List[EvidenceItem]:
    """
    Deterministic fallback tool.
    Useful for demos, offline mode, or testing agent logic.
    """
    return [
        EvidenceItem(
            type=EvidenceType.OTHER,
            source="stub_tool",
            summary=f"Stub evidence generated for query: '{query}'. "
                    f"This indicates where real retrieval will plug in.",
            confidence=0.2,
            raw={
                "id": str(uuid.uuid4()),
                "note": "Replace with real retrieval later",
            },
        )
    ]

# Tool Registry
TOOL_REGISTRY: Dict[str, Any] = {
    "web_search": tavily_search,
    "stub_evidence": stub_evidence,
}
