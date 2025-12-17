# Full Integration Test with MongoDB Persistence
Write-Host "`n=== PharmAI Full Persistence Test ===" -ForegroundColor Cyan

$nodeUrl = "http://localhost:5000"
$pythonUrl = "http://localhost:7860"
$sessionId = "persist-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "Session ID: $sessionId" -ForegroundColor Yellow
Write-Host "This session will be saved in MongoDB`n" -ForegroundColor Yellow

# 1. Check servers
Write-Host "1. Checking servers..." -ForegroundColor Green
try {
    $nodeHealth = Invoke-RestMethod -Uri "$nodeUrl/health" -Method GET
    Write-Host "   Node.js: OK" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: Node.js not running" -ForegroundColor Red
    exit 1
}

try {
    $pythonHealth = Invoke-RestMethod -Uri "$pythonUrl/health" -Method GET
    Write-Host "   Python: OK" -ForegroundColor Gray
    Write-Host "   MongoDB: $($pythonHealth.mongodb)" -ForegroundColor Gray
    Write-Host "   Active sessions: $($pythonHealth.active_sessions)" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: Python backend not running" -ForegroundColor Red
    exit 1
}

# 2. First query
Write-Host "`n2. Sending first query..." -ForegroundColor Green
Write-Host "   Query: What is pembrolizumab?" -ForegroundColor Gray

$body1 = @{
    session_id = $sessionId
    query = "What is pembrolizumab?"
} | ConvertTo-Json

$startTime = Get-Date
try {
    $response1 = Invoke-RestMethod -Uri "$nodeUrl/api/agent/run" -Method POST -ContentType "application/json" -Body $body1 -TimeoutSec 120
    $duration = ((Get-Date) - $startTime).TotalSeconds
    
    Write-Host "   Response received in $([math]::Round($duration, 1)) seconds" -ForegroundColor Gray
    Write-Host "   Brief length: $($response1.decision_brief.Length) chars" -ForegroundColor Gray
    Write-Host "   Citations: $($response1.citations.Count)" -ForegroundColor Gray
    
    $preview = $response1.decision_brief.Substring(0, [Math]::Min(200, $response1.decision_brief.Length))
    Write-Host "`n   Preview: $preview..." -ForegroundColor DarkGray
    
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. Check MongoDB
Write-Host "`n3. Verifying MongoDB storage..." -ForegroundColor Green
try {
    $history1 = Invoke-RestMethod -Uri "$pythonUrl/session/$sessionId/history" -Method GET
    Write-Host "   Messages in MongoDB: $($history1.message_count)" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: Could not retrieve session" -ForegroundColor Red
}

# 4. Follow-up query
Write-Host "`n4. Sending follow-up query..." -ForegroundColor Green
Write-Host "   Query: What are common side effects?" -ForegroundColor Gray

$body2 = @{
    session_id = $sessionId
    query = "What are common side effects?"
} | ConvertTo-Json

$startTime = Get-Date
try {
    $response2 = Invoke-RestMethod -Uri "$nodeUrl/api/agent/run" -Method POST -ContentType "application/json" -Body $body2 -TimeoutSec 120
    $duration = ((Get-Date) - $startTime).TotalSeconds
    
    Write-Host "   Response received in $([math]::Round($duration, 1)) seconds" -ForegroundColor Gray
    Write-Host "   Has prior context: $($response2.metadata.has_prior_messages)" -ForegroundColor Gray
    
    $preview = $response2.decision_brief.Substring(0, [Math]::Min(200, $response2.decision_brief.Length))
    Write-Host "`n   Preview: $preview..." -ForegroundColor DarkGray
    
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Final verification
Write-Host "`n5. Final MongoDB verification..." -ForegroundColor Green
try {
    $history2 = Invoke-RestMethod -Uri "$pythonUrl/session/$sessionId/history" -Method GET
    Write-Host "   Total messages: $($history2.message_count)" -ForegroundColor Gray
    
    Write-Host "`n   Conversation:" -ForegroundColor Gray
    foreach ($msg in $history2.messages) {
        $preview = $msg.content.Substring(0, [Math]::Min(60, $msg.content.Length))
        Write-Host "   - [$($msg.role)]: $preview..." -ForegroundColor DarkGray
    }
} catch {
    Write-Host "   ERROR: Could not retrieve history" -ForegroundColor Red
}

# Summary
Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "Session ID: $sessionId" -ForegroundColor Yellow
Write-Host "Status: SAVED in MongoDB (not deleted)" -ForegroundColor Green
Write-Host "`nTo view in MongoDB Atlas:" -ForegroundColor Yellow
Write-Host "  Database: pharmai" -ForegroundColor Gray
Write-Host "  Collection: sessions" -ForegroundColor Gray
Write-Host "  Document _id: $sessionId" -ForegroundColor Gray
Write-Host "`nTo retrieve: curl http://localhost:7860/session/$sessionId/history" -ForegroundColor Gray
Write-Host "To delete: curl -X DELETE http://localhost:7860/session/$sessionId" -ForegroundColor Gray
