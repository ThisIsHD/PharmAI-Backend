# PharmAI Navigator - Integration Guide

## Architecture

```
Frontend/Client
    ↓
Node.js Express (Port 5000)
    ↓ HTTP Proxy
Python FastAPI (Port 7860)
    ↓
LangGraph Agent → Anthropic Claude
```

## Quick Start

### Option 1: Start Both Servers Automatically
```powershell
.\start-all.ps1
```

### Option 2: Start Manually

**Terminal 1 - Python Backend:**
```powershell
cd app
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

**Terminal 2 - Node.js Server:**
```powershell
npm start
```

## Test Integration

```powershell
.\test-integration.ps1
```

## API Endpoints

### Node.js Proxy Endpoints (Port 5000)

#### 1. Run Agent Query
```http
POST /api/agent/run
Content-Type: application/json

{
  "session_id": "user-123",
  "query": "Evaluate semaglutide for obesity"
}
```

**Response:**
```json
{
  "session_id": "user-123",
  "decision_brief": "# FINAL DECISION BRIEF...",
  "citations": ["https://..."],
  "confidence_score": null,
  "metadata": {
    "has_prior_messages": false
  }
}
```

#### 2. Get Session History
```http
GET /api/agent/session/{session_id}/history
```

#### 3. Clear Session
```http
DELETE /api/agent/session/{session_id}
```

#### 4. Health Check
```http
GET /api/agent/health
```

### Direct Python Endpoints (Port 7860)

Same endpoints available directly on Python backend if needed.

## Environment Variables

### `.env` (Root)
```env
PORT=5000
MONGO_URI=mongodb+srv://...
PYTHON_BACKEND_URL=http://localhost:7860
```

### `app/.env` (Python)
```env
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=pharmai-navigator
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
MAX_OUTPUT_TOKENS=1200
MAX_TOOL_LOOPS=4
```

## Example Usage

### PowerShell
```powershell
# Query via Node.js proxy
$body = @{
    session_id = "user-abc"
    query = "Evaluate pembrolizumab for melanoma"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/agent/run" -Method POST -ContentType "application/json" -Body $body
```

### cURL
```bash
curl -X POST http://localhost:5000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"session_id":"user-abc","query":"Evaluate pembrolizumab for melanoma"}'
```

### JavaScript/Fetch
```javascript
const response = await fetch('http://localhost:5000/api/agent/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'user-abc',
    query: 'Evaluate pembrolizumab for melanoma'
  })
});

const data = await response.json();
console.log(data.decision_brief);
```

## Troubleshooting

### Python backend not reachable
```
Error: ECONNREFUSED
```
**Solution:** Start Python backend first:
```powershell
cd app
uvicorn app:app --port 7860
```

### Rate limit errors
```
Error code: 429
```
**Solution:** Wait 1 minute or reduce `MAX_OUTPUT_TOKENS` in `.env`

### MongoDB connection issues
**Solution:** Check `MONGO_URI` in `.env` is correct

## Production Deployment

For production, consider:
1. Use process managers (PM2 for Node.js, Gunicorn for Python)
2. Add authentication/API keys
3. Enable HTTPS
4. Set up proper logging
5. Configure CORS appropriately
6. Use environment-specific configs
7. Add rate limiting
8. Set up monitoring (LangSmith already configured)

## Next Steps

- [ ] Add authentication middleware
- [ ] Implement streaming responses
- [ ] Add MongoDB persistence for sessions
- [ ] Create frontend UI
- [ ] Deploy to production
- [ ] Add API documentation (Swagger/OpenAPI)
