@echo off
echo ========================================
echo    PocketCoach AI - Frontend Server
echo ========================================
echo.

cd frontend

echo Starting HTTP server on port 3000...
echo.
echo Frontend will be available at: http://localhost:3000
echo.
echo Pages:
echo - Landing Page: http://localhost:3000/index.html
echo - Login/Signup: http://localhost:3000/pages/login.html
echo - Integration Test: http://localhost:3000/integration-test.html
echo.
echo Press Ctrl+C to stop the server
echo.

python -m http.server 3000

pause
