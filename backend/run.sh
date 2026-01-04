#!/bin/bash
# Simple run script for the backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

