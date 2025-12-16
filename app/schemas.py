# schemas.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# Core Enums
class AgentType(str, Enum):
    PLANNER = "planner"
    SCIENTIFIC = "scientific"
    PATENT = "patent"
    MARKET = "market"
    SUPPLY = "supply"
    SYNTHESIS = "synthesis"

class EvidenceType(str, Enum):
    LITERATURE = "literature"
    CLINICAL_TRIAL = "clinical_trial"
    PATENT = "patent"
    MARKET = "market"
    OTHER = "other"

# API Schemas (FastAPI I/O)
class AgentRunRequest(BaseModel):
    """
    Incoming request from Node.js backend or direct API call.
    """
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID to maintain conversation state"
    )
    query: str = Field(
        ...,
        description="User query, e.g. 'Drug X for Indication Y'"
    )

class AgentRunResponse(BaseModel):
    """
    Final response returned by the agent system.
    """
    session_id: Optional[str]
    decision_brief: str
    confidence_score: Optional[float] = Field(
        default=None,
        description="Optional overall confidence score (0–1)"
    )
    citations: Optional[List[str]] = Field(
        default=None,
        description="List of citation identifiers or URLs"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extra debug or trace metadata"
    )

# Internal Agent State
class Message(BaseModel):
    """
    Canonical message format passed between agents.
    """
    role: str  # system | user | assistant | tool
    content: str

class EvidenceItem(BaseModel):
    """
    A single piece of evidence produced by tools or agents.
    """
    type: EvidenceType
    source: str
    summary: str
    confidence: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None

class AgentOutput(BaseModel):
    """
    Output produced by a single agent.
    """
    agent: AgentType
    text: str
    evidence: Optional[List[EvidenceItem]] = None

class AgentState(BaseModel):
    """
    LangGraph state object.
    This is what flows between graph nodes.
    """
    session_id: Optional[str]
    user_query: str

    messages: List[Message] = Field(default_factory=list)

    agent_outputs: Dict[AgentType, AgentOutput] = Field(
        default_factory=dict,
        description="Outputs from each agent"
    )

    final_decision: Optional[str] = None

    confidence_score: Optional[float] = None
