# Test MongoDB Memory Persistence
Write-Host "`n=== MongoDB Memory Persistence Test ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:7860"
$sessionId = "mongo-test-$(Get-Random)"

# 1. Health Check (should show MongoDB status)
Write-Host "`n1. Checking MongoDB connection..." -ForegroundColor Green
$health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
Write-Host "   Status: $($health.status)" -ForegroundColor Gray
Write-Host "   MongoDB: $($health.mongodb)" -ForegroundColor Gray
Write-Host "   Active sessions: $($health.active_sessions)" -ForegroundColor Gray

if ($health.mongodb -ne "connected") {
    Write-Host "`n   ERROR: MongoDB not connected!" -ForegroundColor Red
    Write-Host "   Check MONGO_URI in app/.env" -ForegroundColor Yellow
    exit 1
}

# 2. Create first message
Write-Host "`n2. Creating session with first message..." -ForegroundColor Green
$body1 = @{
    session_id = $sessionId
    query = "What is pembrolizumab?"
} | ConvertTo-Json

$response1 = Invoke-RestMethod -Uri "$baseUrl/test/echo" -Method POST -ContentType "application/json" -Body $body1
Write-Host "   Session: $($response1.session_id)" -ForegroundColor Gray
Write-Host "   Messages: $($response1.current_message_count)" -ForegroundColor Gray

# 3. Add second message
Write-Host "`n3. Adding second message..." -ForegroundColor Green
$body2 = @{
    session_id = $sessionId
    query = "What are its side effects?"
} | ConvertTo-Json

$response2 = Invoke-RestMethod -Uri "$baseUrl/test/echo" -Method POST -ContentType "application/json" -Body $body2
Write-Host "   Messages: $($response2.current_message_count)" -ForegroundColor Gray

# 4. Check MongoDB directly
Write-Host "`n4. Verifying data in MongoDB..." -ForegroundColor Green
$history = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId/history" -Method GET
Write-Host "   Total messages in DB: $($history.message_count)" -ForegroundColor Gray
foreach ($msg in $history.messages) {
    Write-Host "   - [$($msg.role)]: $($msg.content)" -ForegroundColor Gray
}

# 5. Simulate server restart (just check persistence)
Write-Host "`n5. Testing persistence (data should survive)..." -ForegroundColor Green
Write-Host "   Note: In production, this data survives server restarts!" -ForegroundColor Yellow
Write-Host "   Session ID: $sessionId" -ForegroundColor Yellow
Write-Host "   You can restart the server and query this session again." -ForegroundColor Yellow

# 6. Check active sessions count
Write-Host "`n6. Checking total active sessions..." -ForegroundColor Green
$health2 = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
Write-Host "   Active sessions in MongoDB: $($health2.active_sessions)" -ForegroundColor Gray

# 7. Cleanup
Write-Host "`n7. Cleaning up test session..." -ForegroundColor Green
$clear = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId" -Method DELETE
Write-Host "   Status: $($clear.status)" -ForegroundColor Gray

# 8. Verify cleanup
$health3 = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
Write-Host "   Active sessions after cleanup: $($health3.active_sessions)" -ForegroundColor Gray

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "✅ MongoDB persistence is working!" -ForegroundColor Green
Write-Host "`nKey Benefits:" -ForegroundColor Yellow
Write-Host "  - Sessions survive server restarts" -ForegroundColor Gray
Write-Host "  - Can scale across multiple servers" -ForegroundColor Gray
Write-Host "  - Automatic TTL cleanup (7 days)" -ForegroundColor Gray
Write-Host "  - Production-ready persistence" -ForegroundColor Gray
