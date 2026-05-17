#!/bin/bash
set -e

echo "🛡️ Starting VANGUARD MILANO v2.0..."

# Start FastAPI backend in the background
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ FastAPI backend started (PID: $BACKEND_PID) on port 8000"

# Give the backend a moment to initialise before the frontend starts
sleep 2

# Start Streamlit frontend (use FILE PATH, not Python module notation)
echo "✅ Starting Streamlit frontend on port 8501..."
streamlit run src/vanguard_ui.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false

# If streamlit exits, bring down the backend too
kill $BACKEND_PID