#!/usr/bin/env python3
"""
Lean-Deep 3.2 Marker Engine - Glitch Optimized Version
Simplified for 512MB RAM constraint
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
import yaml
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    PORT = int(os.getenv("PORT", 3000))
    HOST = os.getenv("HOST", "0.0.0.0")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB
    ENABLE_WEBSOCKET = os.getenv("ENABLE_WEBSOCKET", "true").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
config = Config()

# FastAPI app
app = FastAPI(
    title="Marker Engine - Glitch Edition",
    version="1.0.0-glitch",
    description="Lightweight Lean-Deep 3.2 Marker Analysis for Glitch deployment"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client
mongo_client: Optional[AsyncIOMotorClient] = None
db = None

# Pydantic models
class AnalysisRequest(BaseModel):
    content: str = Field(..., description="Text content to analyze")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")
    options: Optional[Dict[str, Any]] = Field(default={}, description="Analysis options")

class MarkerEvent(BaseModel):
    marker_id: str
    level: str  # ATO, SEM, CLU, MEMA
    content: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = {}

# Simplified marker patterns (no heavy NLP libraries)
MARKER_PATTERNS = {
    "ATO": {
        # Atomic markers - simple pattern matching
        "A_TE_": r"\b(test|testing|tested)\b",
        "A_TH_": r"\b(think|thinking|thought)\b",
        "A_FE_": r"\b(feel|feeling|felt)\b",
        "A_WA_": r"\b(want|wanting|wanted)\b",
        "A_NE_": r"\b(need|needing|needed)\b",
        "A_HA_": r"\b(have|having|had)\b",
        "A_DO_": r"\b(do|doing|did|done)\b",
        "A_BE_": r"\b(am|is|are|was|were|being|been)\b",
    },
    "SEM": {
        # Semantic markers - phrase patterns
        "S_QU_": r"\?|^(what|when|where|why|how|who)",
        "S_AG_": r"\b(yes|yeah|ok|okay|sure|agree)\b",
        "S_DI_": r"\b(no|not|disagree|but)\b",
        "S_EM_": r"[!]{2,}|[😀-🙏]",
        "S_TI_": r"\b\d{1,2}:\d{2}\b|\b(morning|afternoon|evening|night)\b",
    },
    "CLU": {
        # Cluster markers - context patterns
        "C_TOP_": "topic_shift",  # Requires context analysis
        "C_EMO_": "emotion_cluster",  # Requires emotion tracking
        "C_ACT_": "action_sequence",  # Requires verb analysis
    },
    "MEMA": {
        # Meta-markers - high-level patterns
        "M_SUM_": "summary_pattern",  # Requires full text analysis
        "M_CON_": "conclusion_pattern",
        "M_REF_": "reflection_pattern",
    }
}

class SimpleMarkerEngine:
    """Lightweight marker engine for Glitch constraints"""
    
    def __init__(self):
        self.patterns = MARKER_PATTERNS
        
    async def analyze(self, content: str, context: Optional[Dict] = None) -> Dict:
        """Simple pattern-based analysis"""
        import re
        
        markers = []
        
        # ATO level - direct pattern matching
        for marker_id, pattern in self.patterns["ATO"].items():
            if re.search(pattern, content.lower()):
                markers.append({
                    "marker_id": marker_id,
                    "level": "ATO",
                    "confidence": 0.8,
                    "content": content[:50]
                })
        
        # SEM level - semantic patterns
        for marker_id, pattern in self.patterns["SEM"].items():
            if isinstance(pattern, str) and re.search(pattern, content):
                markers.append({
                    "marker_id": marker_id,
                    "level": "SEM",
                    "confidence": 0.7,
                    "content": content[:50]
                })
        
        # Simple emotion detection
        emotion_score = self._calculate_emotion(content)
        
        return {
            "markers": markers,
            "emotion_dynamics": {
                "valence": emotion_score,
                "arousal": 0.5,
                "home_base": emotion_score,
                "variability": 0.2,
                "drift": 0.0
            },
            "statistics": {
                "total_markers": len(markers),
                "by_level": {
                    "ATO": sum(1 for m in markers if m["level"] == "ATO"),
                    "SEM": sum(1 for m in markers if m["level"] == "SEM"),
                    "CLU": 0,
                    "MEMA": 0
                }
            }
        }
    
    def _calculate_emotion(self, text: str) -> float:
        """Simple emotion scoring"""
        positive_words = ["good", "happy", "great", "love", "excellent", "wonderful"]
        negative_words = ["bad", "sad", "angry", "hate", "terrible", "awful"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.5
        
        return pos_count / (pos_count + neg_count)

# Initialize marker engine
marker_engine = SimpleMarkerEngine()

# Startup event
@app.on_event("startup")
async def startup_event():
    global mongo_client, db
    try:
        mongo_client = AsyncIOMotorClient(config.MONGODB_URI)
        db = mongo_client.marker_engine
        await mongo_client.admin.command('ping')
        logger.info("✅ Connected to MongoDB")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB connection failed: {e}. Running without database.")
        db = None

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

# Routes
@app.get("/")
async def root():
    return {
        "name": "Marker Engine - Glitch Edition",
        "version": "1.0.0-glitch",
        "status": "running",
        "features": {
            "websocket": config.ENABLE_WEBSOCKET,
            "database": db is not None,
            "max_upload_size": config.MAX_UPLOAD_SIZE
        }
    }

@app.get("/health")
async def health_check():
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db else "disconnected",
        "memory_usage": get_memory_usage()
    }
    return status

@app.post("/api/analyze")
async def analyze_content(request: AnalysisRequest):
    """Analyze text content for markers"""
    try:
        result = await marker_engine.analyze(request.content, request.context)
        
        # Store in database if available
        if db:
            await db.analyses.insert_one({
                "timestamp": datetime.utcnow(),
                "content": request.content[:500],  # Store snippet only
                "result": result,
                "options": request.options
            })
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads"""
    if file.size > config.MAX_UPLOAD_SIZE:
        raise HTTPException(400, f"File too large. Max size: {config.MAX_UPLOAD_SIZE} bytes")
    
    try:
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        # Analyze the content
        result = await marker_engine.analyze(text_content)
        
        return {
            "filename": file.filename,
            "size": file.size,
            "analysis": result
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/markers")
async def get_markers(limit: int = 100, skip: int = 0):
    """Get stored markers from database"""
    if not db:
        return {"markers": [], "message": "Database not connected"}
    
    try:
        cursor = db.analyses.find({}).skip(skip).limit(limit)
        markers = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            markers.append(doc)
        
        return {"markers": markers, "count": len(markers)}
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(500, str(e))

# WebSocket endpoint (if enabled)
if config.ENABLE_WEBSOCKET:
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        logger.info("WebSocket connection established")
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "analyze":
                    result = await marker_engine.analyze(
                        message.get("content", ""),
                        message.get("context")
                    )
                    await websocket.send_json({
                        "type": "analysis_result",
                        "result": result
                    })
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close()

# Utility functions
def get_memory_usage():
    """Get current memory usage"""
    import psutil
    process = psutil.Process(os.getpid())
    return {
        "rss_mb": process.memory_info().rss / 1024 / 1024,
        "percent": process.memory_percent()
    }

# Export endpoints for monitoring
@app.get("/api/export/yaml")
async def export_yaml(limit: int = 100):
    """Export analysis results as YAML"""
    if not db:
        return {"error": "Database not connected"}
    
    cursor = db.analyses.find({}).limit(limit)
    data = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        data.append(doc)
    
    yaml_content = yaml.dump(data, default_flow_style=False)
    return JSONResponse(
        content={"yaml": yaml_content},
        media_type="application/x-yaml"
    )

@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "memory": get_memory_usage(),
        "database": "connected" if db else "disconnected"
    }
    
    if db:
        stats["document_count"] = await db.analyses.count_documents({})
    
    return stats

# Main entry point
if __name__ == "__main__":
    logger.info(f"🚀 Starting Marker Engine on {config.HOST}:{config.PORT}")
    logger.info(f"📊 Memory limit optimized for Glitch (512MB)")
    logger.info(f"🔧 WebSocket: {'Enabled' if config.ENABLE_WEBSOCKET else 'Disabled'}")
    
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True
    )