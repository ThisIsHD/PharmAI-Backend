---
title: PharmAI Navigator
emoji: 💊
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# PharmAI Navigator

An AI-powered pharmaceutical due diligence assistant using LangGraph and Claude.

## Features

- 🔍 Evidence-based drug evaluation
- 📊 Clinical trial search
- 🧬 Scientific rationale analysis
- 📈 Market and IP assessment
- 💬 Multi-turn conversations with memory
- 🗄️ MongoDB session persistence

## API Endpoints

### Health Check
```bash
GET /health
```

### Run Agent Query
```bash
POST /run
Content-Type: application/json

{
  "session_id": "user-123",
  "query": "Evaluate semaglutide for obesity"
}
```

### Get Session History
```bash
GET /session/{session_id}/history
```

### Clear Session
```bash
DELETE /session/{session_id}
```

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `MONGO_URI` - MongoDB connection string

Optional:
- `TAVILY_API_KEY` - For web search
- `LANGSMITH_API_KEY` - For tracing
- `MAX_OUTPUT_TOKENS` - Default: 1200
- `MAX_TOOL_LOOPS` - Default: 4

## Usage Example

```python
import requests

response = requests.post(
    "https://your-space.hf.space/run",
    json={
        "session_id": "demo",
        "query": "What is pembrolizumab?"
    }
)

print(response.json()["decision_brief"])
```

## Tech Stack

- FastAPI
- LangChain / LangGraph
- Anthropic Claude
- MongoDB
- Tavily Search
- LangSmith (optional)
