@echo off
REM FastAPI Server Startup Script for HR Assistant
REM Run with: start_server.bat

cd /d "c:\Users\USER\Documents\HR agent Folder"

echo.
echo ============================================================
echo HR ASSISTANT FASTAPI BACKEND - STARTUP
echo ============================================================
echo.
echo Checking Python installation...
python --version

echo.
echo Checking FastAPI installation...
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')" 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: FastAPI not found. Installing dependencies...
    pip install fastapi uvicorn python-multipart pydantic
)

echo.
echo ============================================================
echo STARTING SERVER
echo ============================================================
echo.
echo API will be available at: http://localhost:8000
echo Swagger UI: http://localhost:8000/api/docs
echo ReDoc: http://localhost:8000/api/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

timeout /t 3

REM Start the server with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
