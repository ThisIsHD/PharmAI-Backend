# Test Integration between Node.js and Python backends
Write-Host "`n=== PharmAI Integration Test ===" -ForegroundColor Cyan

$nodeUrl = "http://localhost:5000"
$sessionId = "integration-test-$(Get-Random)"

# 1. Check Node.js health
Write-Host "`n1. Checking Node.js server..." -ForegroundColor Green
try {
    $nodeHealth = Invoke-RestMethod -Uri "$nodeUrl/health" -Method GET
    Write-Host "   Node.js: $($nodeHealth.status)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: Node.js server not running!" -ForegroundColor Red
    Write-Host "   Start with: npm start" -ForegroundColor Yellow
    exit 1
}

# 2. Check Python backend via Node.js proxy
Write-Host "`n2. Checking Python backend (via Node.js)..." -ForegroundColor Green
try {
    $agentHealth = Invoke-RestMethod -Uri "$nodeUrl/api/agent/health" -Method GET
    Write-Host "   Python backend: $($agentHealth.python_backend.status)" -ForegroundColor Green
    Write-Host "   Backend URL: $($agentHealth.backend_url)" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: Python backend not reachable!" -ForegroundColor Red
    Write-Host "   Start with: cd app; uvicorn app:app --port 7860" -ForegroundColor Yellow
    exit 1
}

# 3. Test agent query through Node.js
Write-Host "`n3. Testing agent query (via Node.js proxy)..." -ForegroundColor Green
$body = @{
    session_id = $sessionId
    query = "What is pembrolizumab?"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$nodeUrl/api/agent/run" -Method POST -ContentType "application/json" -Body $body
    Write-Host "   Session ID: $($response.session_id)" -ForegroundColor Gray
    Write-Host "   Brief length: $($response.decision_brief.Length) chars" -ForegroundColor Gray
    Write-Host "   Citations: $($response.citations.Count)" -ForegroundColor Gray
    Write-Host "   First 200 chars: $($response.decision_brief.Substring(0, [Math]::Min(200, $response.decision_brief.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: Agent query failed!" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. Check session history
Write-Host "`n4. Checking session history..." -ForegroundColor Green
try {
    $history = Invoke-RestMethod -Uri "$nodeUrl/api/agent/session/$sessionId/history" -Method GET
    Write-Host "   Messages in session: $($history.message_count)" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: Failed to get history!" -ForegroundColor Red
}

# 5. Clear session
Write-Host "`n5. Cleaning up test session..." -ForegroundColor Green
try {
    $clear = Invoke-RestMethod -Uri "$nodeUrl/api/agent/session/$sessionId" -Method DELETE
    Write-Host "   Session cleared: $($clear.status)" -ForegroundColor Gray
} catch {
    Write-Host "   Warning: Failed to clear session" -ForegroundColor Yellow
}

Write-Host "`n=== Integration Test Complete ===" -ForegroundColor Cyan
Write-Host "✅ All systems operational!" -ForegroundColor Green
Write-Host "`nEndpoints available:" -ForegroundColor Yellow
Write-Host "  - Node.js: http://localhost:5000" -ForegroundColor Gray
Write-Host "  - Python:  http://localhost:7860" -ForegroundColor Gray
Write-Host "  - Agent:   http://localhost:5000/api/agent/run" -ForegroundColor Gray
