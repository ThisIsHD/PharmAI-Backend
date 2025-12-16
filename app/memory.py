from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import time
import threading
from schemas import Message

@dataclass
class SessionMemory:
    """In-memory chat history for a single session."""
    messages: List[Message]
    updated_at: float


class MemoryStore:
    """
    Simple thread-safe in-memory store.

    - session_id -> list[Message]
    - trims to keep memory bounded
    - includes basic TTL cleanup hooks (optional)
    """

    def __init__(self, max_messages: int = 30, ttl_seconds: Optional[int] = None):
        self.max_messages = max_messages
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._store: Dict[str, SessionMemory] = {}

    def _now(self) -> float:
        return time.time()

    def get(self, session_id: str) -> List[Message]:
        """Get messages for a session (returns empty list if new session)."""
        if not session_id:
            return []
        with self._lock:
            self._gc_locked()
            if session_id not in self._store:
                self._store[session_id] = SessionMemory(messages=[], updated_at=self._now())
            return list(self._store[session_id].messages)

    def append(self, session_id: str, role: str, content: str) -> None:
        """Append a message and enforce trimming."""
        if not session_id:
            return
        with self._lock:
            self._gc_locked()
            if session_id not in self._store:
                self._store[session_id] = SessionMemory(messages=[], updated_at=self._now())

            self._store[session_id].messages.append(Message(role=role, content=content))
            self._store[session_id].updated_at = self._now()

            # Trim oldest messages (keep most recent)
            if len(self._store[session_id].messages) > self.max_messages:
                overflow = len(self._store[session_id].messages) - self.max_messages
                self._store[session_id].messages = self._store[session_id].messages[overflow:]

    def set_messages(self, session_id: str, messages: List[Message]) -> None:
        """Replace session history entirely (rarely needed, but handy)."""
        if not session_id:
            return
        with self._lock:
            self._store[session_id] = SessionMemory(
                messages=messages[-self.max_messages :],
                updated_at=self._now(),
            )

    def clear(self, session_id: str) -> None:
        """Clear a single session."""
        if not session_id:
            return
        with self._lock:
            self._store.pop(session_id, None)

    def _gc_locked(self) -> None:
        """TTL cleanup (only runs if ttl_seconds is configured)."""
        if not self.ttl_seconds:
            return
        cutoff = self._now() - self.ttl_seconds
        expired = [sid for sid, mem in self._store.items() if mem.updated_at < cutoff]
        for sid in expired:
            self._store.pop(sid, None)


# Global singleton (simple for HF Spaces demo)
memory_store = MemoryStore(
    max_messages=int(__import__("os").getenv("MAX_SESSION_MESSAGES", "30")),
    ttl_seconds=int(__import__("os").getenv("SESSION_TTL_SECONDS", "0")) or None,
)
