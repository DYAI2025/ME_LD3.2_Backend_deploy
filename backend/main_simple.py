#!/usr/bin/env python3
"""
Simplified Marker Engine for Fly.io deployment
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Marker Engine",
    version="1.0.0",
    description="Lean-Deep 3.2 Marker Analysis API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class AnalysisRequest(BaseModel):
    content: str
    context: dict = {}

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Marker Engine",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )

# Analysis endpoint
@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    """Simple marker analysis endpoint"""
    try:
        # Simple marker detection
        markers = []
        content_lower = request.content.lower()
        
        # Basic marker patterns
        if "feel" in content_lower or "feeling" in content_lower:
            markers.append({"id": "A_FE_", "level": "ATO", "confidence": 0.8})
        if "think" in content_lower or "thought" in content_lower:
            markers.append({"id": "A_TH_", "level": "ATO", "confidence": 0.8})
        if "?" in request.content:
            markers.append({"id": "S_QU_", "level": "SEM", "confidence": 0.9})
        
        return JSONResponse(content={
            "status": "success",
            "markers": markers,
            "statistics": {
                "total_markers": len(markers),
                "by_level": {
                    "ATO": sum(1 for m in markers if m["level"] == "ATO"),
                    "SEM": sum(1 for m in markers if m["level"] == "SEM"),
                    "CLU": 0,
                    "MEMA": 0
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Stats endpoint
@app.get("/api/stats")
async def get_stats():
    return {
        "status": "operational",
        "uptime": "N/A",
        "requests_processed": 0,
        "timestamp": datetime.utcnow().isoformat()
    }

# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting Marker Engine on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )