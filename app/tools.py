from typing import List, Dict, Any, Optional
import os
import uuid
import re
import base64
from schemas import EvidenceItem, EvidenceType

#Helper Functions
def _etype(name: str, default: EvidenceType) -> EvidenceType:
    """Return EvidenceType.<name> if it exists, else default (prevents breaking)."""
    return getattr(EvidenceType, name, default)

def _short(s: str, n: int = 700) -> str:
    return (s or "")[:n]

def _is_url(s: str) -> bool:
    return isinstance(s, str) and s.startswith(("http://", "https://"))

# Tool 1: Tavily Web Search (existing, unchanged)
def tavily_search(query: str, max_results: int = 5) -> List[EvidenceItem]:
    """
    Uses Tavily API to perform web search.
    Returns structured evidence items.
    """
    api_key = os.getenv("TAVILY_API_KEY")

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

# Tool 2: Stub Evidence Generator (existing, unchanged)
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

# Tool 3: Query Classifier (planner helper)
def classify_query(query: str) -> Dict[str, Any]:
    """
    Lightweight classifier to help the agent decide
    which tools (if any) are required.
    """
    q = (query or "").lower()
    needs_graph = any(k in q for k in ["diagram", "graph", "graphviz", "dot", "flow", "architecture", "arch", "draw"])
    needs_trials = any(k in q for k in ["trial", "clinical", "phase", "nct", "primary endpoint", "secondary endpoint"])
    needs_facts = any(k in q for k in ["fda", "approval", "label", "patent", "exclusivity", "pricing", "aria", "safety", "market"])
    needs_entities = any(k in q for k in ["evaluate", "assess", "analyze", "repurpose", "for "])
    return {
        "needs_graph": needs_graph,
        "needs_clinical_trials": needs_trials,
        "needs_web_search": needs_facts or needs_trials,
        "needs_entity_extraction": needs_entities,
    }

# Tool 4: Entity Extraction (Drug / Indication)
def extract_entities(query: str) -> Dict[str, Optional[str]]:
    """
    Minimal entity extractor for MVP.
    """
    text = (query or "").strip()
    m = re.search(
        r"(evaluate|assess|analyze)\s+(?P<drug>.+?)\s+for\s+(?P<indication>.+)",
        text,
        re.IGNORECASE,
    )
    if m:
        return {
            "drug": m.group("drug").strip(),
            "indication": m.group("indication").strip(),
        }
    return {"drug": None, "indication": None}

# Tool 5: Evidence Normalizer (dedupe + cleanup)
def normalize_evidence(evidence: List[EvidenceItem]) -> List[EvidenceItem]:
    """
    Deduplicates evidence by source and trims noisy content.
    """
    seen = set()
    cleaned: List[EvidenceItem] = []

    for e in evidence:
        if e.source in seen:
            continue
        seen.add(e.source)

        cleaned.append(
            EvidenceItem(
                type=e.type,
                source=e.source,
                summary=(e.summary or "")[:800],
                confidence=e.confidence,
                raw=None,  # drop heavy payloads
            )
        )

    return cleaned

# Tool 6: Graph Generation (Graphviz DOT only)
def generate_graph_dot(
    title: str,
    nodes: List[Dict[str, str]],
    edges: List[Dict[str, str]],
    rankdir: str = "LR",
) -> str:
    """
    Generates Graphviz DOT code.
    IMPORTANT: LLM must call this tool; never output DOT directly.
    """
    safe_title = (title or "PharmAI Graph").replace('"', "'")

    lines = [
        "digraph G {",
        f"  rankdir={rankdir};",
        '  labelloc="t";',
        '  labeljust="c";',
        f'  label=<<B><FONT POINT-SIZE="28">{safe_title}</FONT></B>>;',
        "  node [shape=box, style=rounded];",
        "",
    ]

    for n in nodes or []:
        nid = n.get("id")
        lbl = (n.get("label") or nid).replace('"', "'")
        if nid:
            lines.append(f'  {nid} [label="{lbl}"];')

    lines.append("")

    for e in edges or []:
        src = e.get("from")
        tgt = e.get("to")
        lbl = e.get("label")
        if src and tgt:
            if lbl:
                lines.append(f'  {src} -> {tgt} [label="{lbl}"];')
            else:
                lines.append(f"  {src} -> {tgt};")

    lines.append("}")
    return "\n".join(lines)

#Tool 7: ClinicalTrials search (lightweight, Tavily-based)
def clinicaltrials_search(drug: str, indication: str, max_results: int = 5) -> List[EvidenceItem]:
    """
    MVP approach:
    - Uses Tavily to target ClinicalTrials.gov / NCT IDs
    - Returns EvidenceItems for trial links + snippets
    """
    drug = (drug or "").strip()
    indication = (indication or "").strip()

    if not drug or not indication:
        return [
            EvidenceItem(
                type=EvidenceType.OTHER,
                source="clinicaltrials_search_invalid_input",
                summary="Missing drug or indication for clinical trials search.",
                confidence=0.0,
            )
        ]

    query = f'site:clinicaltrials.gov ("{drug}") ("{indication}") NCT'
    ev = tavily_search(query=query, max_results=max_results)

    trial_type = _etype("CLINICAL_TRIAL", EvidenceType.LITERATURE)

    out: List[EvidenceItem] = []
    for e in ev:
        # only keep plausible CT.gov results if possible
        if _is_url(e.source) and "clinicaltrials.gov" in e.source:
            out.append(
                EvidenceItem(
                    type=trial_type,
                    source=e.source,
                    summary=e.summary,
                    confidence=max(0.55, float(e.confidence or 0.55)),
                    raw=e.raw,
                )
            )

    if out:
        return out

    # fallback: return whatever Tavily gave (still structured)
    return [
        EvidenceItem(
            type=trial_type,
            source=e.source,
            summary=e.summary,
            confidence=float(e.confidence or 0.4),
            raw=e.raw,
        )
        for e in ev
    ]

#Tool 8 : DOT -> PNG
def render_dot_to_png_base64(dot: str) -> Dict[str, Any]:
    """
    Converts DOT to PNG and returns base64 string.
    - Uses python 'graphviz' package if available.
    - If graphviz isn't installed in the environment, returns an error payload.
    """
    dot = (dot or "").strip()
    if not dot:
        return {"ok": False, "error": "Empty DOT string"}

    try:
        from graphviz import Source  # optional dependency

        src = Source(dot)
        png_bytes = src.pipe(format="png")
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return {"ok": True, "png_base64": b64}
    except Exception as e:
        return {
            "ok": False,
            "error": f"DOT->PNG render failed. Ensure `graphviz` Python package and system binaries are installed. Details: {str(e)}",
        }

# Tool Registry (extended, backward compatible)
TOOL_REGISTRY: Dict[str, Any] = {
    # existing
    "web_search": tavily_search,
    "stub_evidence": stub_evidence,

    # new
    "classify_query": classify_query,
    "extract_entities": extract_entities,
    "normalize_evidence": normalize_evidence,
    "generate_graph_dot": generate_graph_dot,
    "clinicaltrials_search": clinicaltrials_search,
    "render_dot_to_png_base64": render_dot_to_png_base64
}
