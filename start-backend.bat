@echo off
echo ========================================
echo    PocketCoach AI - Backend Server
echo ========================================
echo.

cd backend

echo Checking Python installation...
python --version
echo.

echo Installing/Updating dependencies...
pip install -r requirements.txt
echo.

echo Starting FastAPI server on port 8080...
echo.
echo Backend will be available at: http://localhost:8080
echo API Documentation: http://localhost:8080/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py

pause
