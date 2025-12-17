# Memory/Session History Test

## Setup
1. Start the FastAPI server:
```bash
cd app
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

## Test Sequence (Use Postman or curl)

### 1. Health Check
```bash
GET http://localhost:7860/health
```
Expected: `{"status": "ok"}`

---

### 2. First Query (Create Session)
```bash
POST http://localhost:7860/run
Content-Type: application/json

{
  "session_id": "test-session-123",
  "query": "What is semaglutide?"
}
```

Expected Response:
- `session_id`: "test-session-123"
- `decision_brief`: (some text about semaglutide)
- `citations`: (list of URLs)

---

### 3. Check Session History
```bash
GET http://localhost:7860/session/test-session-123/history
```

Expected Response:
```json
{
  "session_id": "test-session-123",
  "message_count": 2,
  "messages": [
    {
      "role": "user",
      "content": "What is semaglutide?"
    },
    {
      "role": "assistant",
      "content": "# FINAL DECISION BRIEF..."
    }
  ]
}
```

---

### 4. Follow-up Query (Same Session)
```bash
POST http://localhost:7860/run
Content-Type: application/json

{
  "session_id": "test-session-123",
  "query": "What are its side effects?"
}
```

Expected: Should have context from previous message about semaglutide

---

### 5. Check History Again
```bash
GET http://localhost:7860/session/test-session-123/history
```

Expected Response:
```json
{
  "session_id": "test-session-123",
  "message_count": 4,
  "messages": [
    {"role": "user", "content": "What is semaglutide?"},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "What are its side effects?"},
    {"role": "assistant", "content": "..."}
  ]
}
```

---

### 6. Clear Session
```bash
DELETE http://localhost:7860/session/test-session-123
```

Expected: `{"session_id": "test-session-123", "status": "cleared"}`

---

### 7. Verify Cleared
```bash
GET http://localhost:7860/session/test-session-123/history
```

Expected: `{"session_id": "test-session-123", "message_count": 0, "messages": []}`

---

## Quick Test (No API Calls)

To test memory without burning tokens, use stub evidence:

```bash
# Temporarily modify graph.py TOOLS to only include stub_evidence_tool
# Then run these queries
```

Or create a minimal test endpoint that just saves/retrieves without calling the graph.
