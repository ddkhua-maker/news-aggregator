#!/bin/bash

# iGaming News Aggregator - Startup Script

echo "=========================================="
echo "iGaming News Aggregator - Starting..."
echo "=========================================="

# Navigate to backend directory
cd backend

# Install dependencies
echo ""
echo "Installing Python dependencies..."
python -m pip install -r requirements.txt

# Start the FastAPI server
echo ""
echo "Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run with uvicorn
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
