#!/bin/bash
set -e

echo "🚀 Starting Marker Engine..."

# Start backend API
echo "Starting backend API..."
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
while ! curl -f http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Backend is ready"

# Start frontend if in full mode
if [ "$RUN_FRONTEND" = "true" ]; then
    echo "Starting frontend..."
    cd /app/frontend
    npm start &
fi

# Keep container running
wait