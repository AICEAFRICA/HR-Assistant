# PowerShell Script to start FastAPI Server
# Usage: .\start_server.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "HR ASSISTANT FASTAPI BACKEND - STARTUP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Set location
Set-Location "c:\Users\USER\Documents\HR agent Folder"

# Check Python
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
python --version

# Check FastAPI
Write-Host "`nChecking FastAPI installation..." -ForegroundColor Yellow
try {
    python -c "import fastapi; print('FastAPI is installed')" -ErrorAction Stop
} catch {
    Write-Host "WARNING: FastAPI not found. Installing dependencies..." -ForegroundColor Red
    pip install fastapi uvicorn python-multipart pydantic
}

# Check other requirements
Write-Host "`nChecking environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found. Make sure GEMINI_API_KEY is set." -ForegroundColor Yellow
}

# Display startup info
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "STARTING SERVER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nServer will start in 3 seconds..." -ForegroundColor Green
Write-Host "API Base URL: http://localhost:8000" -ForegroundColor Green
Write-Host "Swagger UI: http://localhost:8000/api/docs" -ForegroundColor Green
Write-Host "ReDoc: http://localhost:8000/api/redoc" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

Start-Sleep -Seconds 3

# Start the server
Write-Host "Starting uvicorn server..." -ForegroundColor Cyan
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Keep window open if server crashes
Read-Host "Press Enter to exit"
