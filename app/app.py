from __future__ import annotations
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import AgentRunRequest, AgentRunResponse, Message
from memory_mongo import memory_store  # MongoDB-backed memory
from graph import build_graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from fastapi.responses import StreamingResponse
import json
import time
from fastapi.encoders import jsonable_encoder

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
    """Health check with MongoDB status."""
    mongo_status = "connected"
    session_count = 0
    
    try:
        session_count = memory_store.get_session_count()
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "mongodb": mongo_status,
        "active_sessions": session_count
    }


@app.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    """Get chat history for a session (for testing)."""
    messages = memory_store.get(session_id)
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [{"role": m.role, "content": m.content[:100] + "..." if len(m.content) > 100 else m.content} for m in messages]
    }


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear a session's history (for testing)."""
    memory_store.clear(session_id)
    return {"session_id": session_id, "status": "cleared"}


@app.post("/admin/cleanup-sessions")
def cleanup_old_sessions(days: int = 7):
    """
    Admin endpoint to manually cleanup old sessions.
    (TTL index handles this automatically if configured)
    """
    try:
        deleted = memory_store.cleanup_old_sessions(days=days)
        return {
            "status": "ok",
            "deleted_sessions": deleted,
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/echo")
def test_echo(req: AgentRunRequest):
    """
    Lightweight test endpoint - no LLM calls, just tests memory.
    Echoes back the query and shows session history.
    """
    session_id = req.session_id or str(uuid.uuid4())
    
    # Get prior history
    prior = memory_store.get(session_id)
    
    # Append user message
    memory_store.append(session_id, role="user", content=req.query)
    
    # Create fake response
    fake_response = f"Echo: {req.query} (Session has {len(prior)} prior messages)"
    
    # Append assistant message
    memory_store.append(session_id, role="assistant", content=fake_response)
    
    return {
        "session_id": session_id,
        "decision_brief": fake_response,
        "prior_message_count": len(prior),
        "current_message_count": len(memory_store.get(session_id)),
        "citations": [],
        "metadata": {"test_mode": True}
    }


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
        if m.role == "user":
            messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            messages.append(AIMessage(content=m.content))
        elif m.role == "system":
            messages.append(SystemMessage(content=m.content))

    # 3) append this user query to memory (pre-run)
    memory_store.append(session_id, role="user", content=req.query)

    # Append new user query as LangChain message
    messages = messages + [HumanMessage(content=req.query)]

    # 4) run graph (Mode A synchronous)
    try:
        final_state = GRAPH.invoke(
            {
                "session_id": session_id,
                "user_query": req.query,
                "messages": messages,
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
