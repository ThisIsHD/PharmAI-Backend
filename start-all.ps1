# Start both Node.js and Python servers
Write-Host "Starting PharmAI Navigator..." -ForegroundColor Cyan

# Start Python FastAPI backend in background
Write-Host "`n1. Starting Python FastAPI backend (port 7860)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd app; uvicorn app:app --host 0.0.0.0 --port 7860 --reload"

# Wait a bit for Python to start
Start-Sleep -Seconds 3

# Start Node.js Express server
Write-Host "`n2. Starting Node.js Express server (port 5000)..." -ForegroundColor Green
npm start
