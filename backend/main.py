"""
🎯 Marker Engine - FastAPI Backend
Main application entry point with REST and WebSocket endpoints
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import json
import os
from datetime import datetime

from services.marker_engine import MarkerEngine
from services.mongodb_service import MongoDBService
from services.websocket_manager import WebSocketManager
from services.file_processor import FileProcessor
from models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    MarkerEvent,
    EmotionMetrics
)
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Initialize services
db_service = MongoDBService()
marker_engine = MarkerEngine(db_service)
ws_manager = WebSocketManager()
file_processor = FileProcessor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("🚀 Starting Marker Engine Backend...")
    await db_service.connect()
    await marker_engine.initialize()
    logger.info("✅ Marker Engine Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("🔌 Shutting down Marker Engine Backend...")
    await db_service.disconnect()
    await ws_manager.disconnect_all()
    logger.info("✅ Marker Engine Backend stopped")

# Create FastAPI app
app = FastAPI(
    title="Marker Engine API",
    description="Lean-Deep 3.2 Semantic Analysis System",
    version="3.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== REST Endpoints ==================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Marker Engine API",
        "version": "3.2.0",
        "status": "operational",
        "endpoints": {
            "upload": "/api/upload",
            "analyze": "/api/analyze",
            "markers": "/api/markers",
            "events": "/api/events",
            "websocket": "/ws",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await db_service.health_check(),
            "marker_engine": marker_engine.is_initialized,
            "websocket_connections": ws_manager.active_connections_count()
        }
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload WhatsApp ZIP, .opus audio, or text files for processing
    """
    try:
        logger.info(f"📤 Uploading file: {file.filename}")
        
        # Process uploaded file
        file_info = await file_processor.process_upload(file)
        
        # Store file metadata in database
        await db_service.store_file_metadata(file_info)
        
        # Trigger background processing
        asyncio.create_task(process_file_background(file_info))
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": file_info["file_id"],
            "filename": file.filename,
            "size": file_info["size"],
            "type": file_info["type"]
        }
        
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_content(request: AnalysisRequest):
    """
    Analyze text or conversation with the Marker Engine
    """
    try:
        logger.info(f"🔍 Starting analysis for session: {request.session_id}")
        
        # Run marker analysis
        analysis_result = await marker_engine.analyze(
            content=request.content,
            context=request.context,
            options=request.options
        )
        
        # Store results in database
        await db_service.store_analysis_result(
            session_id=request.session_id,
            result=analysis_result
        )
        
        # Broadcast to WebSocket clients
        await ws_manager.broadcast({
            "type": "analysis_complete",
            "session_id": request.session_id,
            "result": analysis_result
        })
        
        return AnalysisResponse(
            session_id=request.session_id,
            markers=analysis_result["markers"],
            emotions=analysis_result["emotions"],
            timeline=analysis_result["timeline"],
            profile=analysis_result["profile"]
        )
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markers")
async def get_markers(
    category: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100
):
    """
    Get marker definitions from the database
    """
    try:
        filters = {}
        if category:
            filters["category"] = category
        if level:
            filters["level"] = level  # ATO, SEM, CLU, MEMA
            
        markers = await db_service.get_markers(filters, limit)
        
        return {
            "total": len(markers),
            "markers": markers
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching markers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/{session_id}")
async def get_events(
    session_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """
    Get marker events for a specific session
    """
    try:
        events = await db_service.get_events(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return {
            "session_id": session_id,
            "total": len(events),
            "events": events
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emotions/{session_id}")
async def get_emotion_dynamics(session_id: str):
    """
    Get EmotionDynamics metrics for a session
    """
    try:
        emotions = await db_service.get_emotion_metrics(session_id)
        
        if not emotions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return emotions
        
    except Exception as e:
        logger.error(f"❌ Error fetching emotions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/{session_id}")
async def export_analysis(
    session_id: str,
    format: str = "yaml"  # yaml or json
):
    """
    Export analysis results in YAML or JSON format
    """
    try:
        # Get complete analysis data
        analysis_data = await db_service.get_complete_analysis(session_id)
        
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Format based on request
        if format == "yaml":
            import yaml
            export_content = yaml.dump(analysis_data, default_flow_style=False)
            media_type = "application/x-yaml"
        else:
            export_content = json.dumps(analysis_data, indent=2)
            media_type = "application/json"
        
        return JSONResponse(
            content={
                "session_id": session_id,
                "format": format,
                "data": export_content
            },
            media_type=media_type
        )
        
    except Exception as e:
        logger.error(f"❌ Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================== WebSocket Endpoint ==================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "subscribe":
                session_id = message.get("session_id")
                await ws_manager.subscribe(websocket, session_id)
                await websocket.send_json({
                    "type": "subscribed",
                    "session_id": session_id
                })
                
            elif message["type"] == "analyze_stream":
                # Stream analysis in real-time
                content = message.get("content")
                session_id = message.get("session_id")
                
                # Run analysis with streaming
                async for event in marker_engine.analyze_stream(content):
                    await websocket.send_json({
                        "type": "marker_event",
                        "session_id": session_id,
                        "event": event
                    })
                    
            elif message["type"] == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)

# ================== Background Tasks ==================

async def process_file_background(file_info: Dict[str, Any]):
    """
    Background task to process uploaded files
    """
    try:
        logger.info(f"🔄 Processing file in background: {file_info['file_id']}")
        
        # Determine file type and process accordingly
        if file_info["type"] == "whatsapp_zip":
            # Extract and process WhatsApp chat
            await file_processor.process_whatsapp_zip(file_info)
            
        elif file_info["type"] == "audio":
            # Process audio file with STT
            await file_processor.process_audio_file(file_info)
            
        elif file_info["type"] == "text":
            # Process text directly
            content = await file_processor.read_text_file(file_info)
            await marker_engine.analyze(content)
        
        # Update file status
        await db_service.update_file_status(
            file_info["file_id"],
            "processed"
        )
        
        # Notify via WebSocket
        await ws_manager.broadcast({
            "type": "file_processed",
            "file_id": file_info["file_id"],
            "status": "complete"
        })
        
    except Exception as e:
        logger.error(f"❌ Background processing error: {str(e)}")
        await db_service.update_file_status(
            file_info["file_id"],
            "error",
            error_message=str(e)
        )

# ================== Error Handlers ==================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("ENVIRONMENT") == "development" else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ================== Main Entry Point ==================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )