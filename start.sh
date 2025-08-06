#!/bin/bash
# Glitch startup script

echo "🚀 Starting Marker Engine for Glitch..."

# Install Python dependencies if not already installed
if [ ! -d "$HOME/.local" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install --user -r backend/requirements-glitch.txt
    
    # Download spacy model if needed
    python3 -m spacy download en_core_web_sm || true
fi

# Start the application
echo "✨ Launching Marker Engine..."
cd backend
python3 main_glitch.py