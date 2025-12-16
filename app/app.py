from __future__ import annotations
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import AgentRunRequest, AgentRunResponse, Message
from memory import memory_store
from graph import build_graph

app = FastAPI(title="PharmAI Navigator (Agentic)", version="0.1.0")

# CORS (HF Spaces + your Node proxy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile graph once at startup
GRAPH = build_graph()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run", response_model=AgentRunResponse)
def run_agent(req: AgentRunRequest):
    # 1) session handling
    session_id = req.session_id or str(uuid.uuid4())

    # 2) load prior history (for chat continuity)
    prior = memory_store.get(session_id)

    # Convert to LangChain message dict format for LangGraph MessagesState
    # LangGraph expects state["messages"] as list of LC messages; we pass dict-like messages.
    messages = []
    for m in prior:
        # role: system/user/assistant/tool (we store user+assistant primarily)
        messages.append({"role": m.role, "content": m.content})

    # 3) append this user query to memory (pre-run)
    memory_store.append(session_id, role="user", content=req.query)

    # 4) run graph (Mode A synchronous)
    try:
        final_state = GRAPH.invoke(
            {
                "session_id": session_id,
                "user_query": req.query,
                "messages": messages + [{"role": "user", "content": req.query}],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent run failed: {str(e)}")

    decision_brief = final_state.get("decision_brief") or final_state.get("final_decision") or ""
    citations = final_state.get("citations") or []

    # 5) save assistant response to memory (post-run)
    if decision_brief.strip():
        memory_store.append(session_id, role="assistant", content=decision_brief)

    return AgentRunResponse(
        session_id=session_id,
        decision_brief=decision_brief,
        confidence_score=final_state.get("confidence_score"),
        citations=citations,
        metadata={
            "has_prior_messages": len(prior) > 0,
        },
    )
