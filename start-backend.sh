#!/bin/bash

echo "========================================"
echo "   PocketCoach AI - Backend Server"
echo "========================================"
echo ""

cd backend

echo "Checking Python installation..."
python3 --version
echo ""

echo "Installing/Updating dependencies..."
pip3 install -r requirements.txt
echo ""

echo "Starting FastAPI server on port 8080..."
echo ""
echo "Backend will be available at: http://localhost:8080"
echo "API Documentation: http://localhost:8080/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 main.py
