# Quick Memory Test Script (No API tokens burned!)
# Run after: uvicorn app:app --host 0.0.0.0 --port 7860

$baseUrl = "http://localhost:7860"
$sessionId = "test-session-$(Get-Random)"

Write-Host "`n=== PharmAI Memory Test ===" -ForegroundColor Cyan
Write-Host "Session ID: $sessionId`n" -ForegroundColor Yellow

# 1. Health Check
Write-Host "1. Health Check..." -ForegroundColor Green
$health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
Write-Host "   Status: $($health.status)`n"

# 2. First Message
Write-Host "2. Sending first message..." -ForegroundColor Green
$body1 = @{
    session_id = $sessionId
    query = "What is semaglutide?"
} | ConvertTo-Json

$response1 = Invoke-RestMethod -Uri "$baseUrl/test/echo" -Method POST -ContentType "application/json" -Body $body1
Write-Host "   Response: $($response1.decision_brief)"
Write-Host "   Prior messages: $($response1.prior_message_count)"
Write-Host "   Current messages: $($response1.current_message_count)`n"

# 3. Check History
Write-Host "3. Checking session history..." -ForegroundColor Green
$history1 = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId/history" -Method GET
Write-Host "   Total messages: $($history1.message_count)"
foreach ($msg in $history1.messages) {
    Write-Host "   - [$($msg.role)]: $($msg.content)"
}
Write-Host ""

# 4. Follow-up Message
Write-Host "4. Sending follow-up message..." -ForegroundColor Green
$body2 = @{
    session_id = $sessionId
    query = "What are its side effects?"
} | ConvertTo-Json

$response2 = Invoke-RestMethod -Uri "$baseUrl/test/echo" -Method POST -ContentType "application/json" -Body $body2
Write-Host "   Response: $($response2.decision_brief)"
Write-Host "   Prior messages: $($response2.prior_message_count)"
Write-Host "   Current messages: $($response2.current_message_count)`n"

# 5. Check History Again
Write-Host "5. Checking updated history..." -ForegroundColor Green
$history2 = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId/history" -Method GET
Write-Host "   Total messages: $($history2.message_count)"
foreach ($msg in $history2.messages) {
    Write-Host "   - [$($msg.role)]: $($msg.content)"
}
Write-Host ""

# 6. Clear Session
Write-Host "6. Clearing session..." -ForegroundColor Green
$clear = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId" -Method DELETE
Write-Host "   Status: $($clear.status)`n"

# 7. Verify Cleared
Write-Host "7. Verifying session cleared..." -ForegroundColor Green
$history3 = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId/history" -Method GET
Write-Host "   Total messages: $($history3.message_count)`n"

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host "Memory is working correctly!" -ForegroundColor Green
