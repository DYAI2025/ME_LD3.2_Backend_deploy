"""
🗄️ MongoDB Service for Marker Engine
Handles all database operations for markers and events
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
import json
from bson import ObjectId

from utils.logger import setup_logger

logger = setup_logger(__name__)

class MongoDBService:
    """
    MongoDB service for Marker Engine data persistence
    """
    
    def __init__(self):
        self.client = None
        self.db = None
        self.markers_collection = None
        self.events_collection = None
        self.sessions_collection = None
        self.files_collection = None
        
        # MongoDB configuration
        self.mongo_url = os.getenv(
            "MONGODB_URL",
            "mongodb://admin:marker-secure-password@localhost:27017/marker_engine?authSource=admin"
        )
        self.database_name = "marker_engine"
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            logger.info("🔗 Connecting to MongoDB...")
            
            # Create MongoDB client
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self.markers_collection = self.db["markers_definitions"]
            self.events_collection = self.db["events_timeline"]
            self.sessions_collection = self.db["analysis_sessions"]
            self.files_collection = self.db["uploaded_files"]
            self.emotions_collection = self.db["emotion_metrics"]
            
            # Create indexes
            await self.create_indexes()
            
            # Test connection
            await self.db.command("ping")
            
            logger.info("✅ Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔌 Disconnected from MongoDB")
    
    async def create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Markers collection indexes
            await self.markers_collection.create_index([("id", 1)], unique=True)
            await self.markers_collection.create_index([("level", 1)])
            await self.markers_collection.create_index([("category", 1)])
            
            # Events collection indexes
            await self.events_collection.create_index([("session_id", 1)])
            await self.events_collection.create_index([("marker_id", 1)])
            await self.events_collection.create_index([("timestamp", -1)])
            await self.events_collection.create_index([
                ("session_id", 1),
                ("timestamp", -1)
            ])
            
            # Sessions collection indexes
            await self.sessions_collection.create_index([("session_id", 1)], unique=True)
            await self.sessions_collection.create_index([("created_at", -1)])
            
            # Files collection indexes
            await self.files_collection.create_index([("file_id", 1)], unique=True)
            await self.files_collection.create_index([("status", 1)])
            
            logger.info("📇 Database indexes created")
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {str(e)}")
    
    async def health_check(self) -> str:
        """Check database health"""
        try:
            await self.db.command("ping")
            return "healthy"
        except:
            return "unhealthy"
    
    # ============= Marker Operations =============
    
    async def get_markers(
        self,
        filters: Dict[str, Any],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get marker definitions from database"""
        try:
            cursor = self.markers_collection.find(filters).limit(limit)
            markers = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for marker in markers:
                if "_id" in marker:
                    marker["_id"] = str(marker["_id"])
            
            return markers
            
        except Exception as e:
            logger.error(f"❌ Error fetching markers: {str(e)}")
            return []
    
    async def insert_marker(self, marker: Dict[str, Any]) -> str:
        """Insert a new marker definition"""
        try:
            marker["created_at"] = datetime.utcnow()
            result = await self.markers_collection.insert_one(marker)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error inserting marker: {str(e)}")
            raise
    
    async def update_marker(self, marker_id: str, updates: Dict[str, Any]) -> bool:
        """Update a marker definition"""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.markers_collection.update_one(
                {"id": marker_id},
                {"$set": updates}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating marker: {str(e)}")
            return False
    
    # ============= Event Operations =============
    
    async def store_event(self, event: Dict[str, Any]) -> str:
        """Store a marker event"""
        try:
            event["created_at"] = datetime.utcnow()
            result = await self.events_collection.insert_one(event)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error storing event: {str(e)}")
            raise
    
    async def store_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """Store multiple events in batch"""
        try:
            if not events:
                return 0
            
            # Add timestamps
            for event in events:
                event["created_at"] = datetime.utcnow()
            
            result = await self.events_collection.insert_many(events)
            return len(result.inserted_ids)
            
        except Exception as e:
            logger.error(f"❌ Error storing events batch: {str(e)}")
            return 0
    
    async def get_events(
        self,
        session_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get events for a session"""
        try:
            query = {"session_id": session_id}
            
            # Add time range filter
            if start_time or end_time:
                time_filter = {}
                if start_time:
                    time_filter["$gte"] = datetime.fromisoformat(start_time)
                if end_time:
                    time_filter["$lte"] = datetime.fromisoformat(end_time)
                query["timestamp"] = time_filter
            
            cursor = self.events_collection.find(query).sort("timestamp", 1).limit(limit)
            events = await cursor.to_list(length=limit)
            
            # Convert ObjectId and datetime to strings
            for event in events:
                if "_id" in event:
                    event["_id"] = str(event["_id"])
                if "timestamp" in event and isinstance(event["timestamp"], datetime):
                    event["timestamp"] = event["timestamp"].isoformat()
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error fetching events: {str(e)}")
            return []
    
    # ============= Session Operations =============
    
    async def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new analysis session"""
        try:
            session_data["created_at"] = datetime.utcnow()
            session_data["status"] = "active"
            
            result = await self.sessions_collection.insert_one(session_data)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error creating session: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            updates["updated_at"] = datetime.utcnow()
            result = await self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": updates}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating session: {str(e)}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            session = await self.sessions_collection.find_one({"session_id": session_id})
            
            if session:
                if "_id" in session:
                    session["_id"] = str(session["_id"])
                if "created_at" in session and isinstance(session["created_at"], datetime):
                    session["created_at"] = session["created_at"].isoformat()
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Error fetching session: {str(e)}")
            return None
    
    # ============= Analysis Operations =============
    
    async def store_analysis_result(
        self,
        session_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """Store complete analysis result"""
        try:
            # Store session data
            await self.update_session(session_id, {
                "analysis_result": result,
                "completed_at": datetime.utcnow(),
                "status": "completed"
            })
            
            # Store events
            if "markers" in result:
                events = []
                for marker in result["markers"]:
                    event = {
                        "session_id": session_id,
                        **marker
                    }
                    events.append(event)
                
                if events:
                    await self.store_events_batch(events)
            
            # Store emotion metrics
            if "emotions" in result:
                await self.emotions_collection.insert_one({
                    "session_id": session_id,
                    **result["emotions"],
                    "created_at": datetime.utcnow()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing analysis result: {str(e)}")
            return False
    
    async def get_complete_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete analysis data for export"""
        try:
            # Get session data
            session = await self.get_session(session_id)
            if not session:
                return None
            
            # Get all events
            events = await self.get_events(session_id)
            
            # Get emotion metrics
            emotions = await self.emotions_collection.find_one({"session_id": session_id})
            if emotions and "_id" in emotions:
                del emotions["_id"]
            
            # Combine all data
            analysis_data = {
                "session": session,
                "events": events,
                "emotions": emotions,
                "export_timestamp": datetime.utcnow().isoformat()
            }
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching complete analysis: {str(e)}")
            return None
    
    # ============= File Operations =============
    
    async def store_file_metadata(self, file_info: Dict[str, Any]) -> str:
        """Store uploaded file metadata"""
        try:
            file_info["uploaded_at"] = datetime.utcnow()
            file_info["status"] = "pending"
            
            result = await self.files_collection.insert_one(file_info)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error storing file metadata: {str(e)}")
            raise
    
    async def update_file_status(
        self,
        file_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Update file processing status"""
        try:
            updates = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                updates["error_message"] = error_message
            
            if status == "processed":
                updates["processed_at"] = datetime.utcnow()
            
            result = await self.files_collection.update_one(
                {"file_id": file_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating file status: {str(e)}")
            return False
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata"""
        try:
            file_data = await self.files_collection.find_one({"file_id": file_id})
            
            if file_data and "_id" in file_data:
                file_data["_id"] = str(file_data["_id"])
            
            return file_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching file metadata: {str(e)}")
            return None
    
    # ============= Emotion Operations =============
    
    async def get_emotion_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get emotion dynamics metrics for a session"""
        try:
            emotions = await self.emotions_collection.find_one({"session_id": session_id})
            
            if emotions:
                if "_id" in emotions:
                    del emotions["_id"]
                if "created_at" in emotions and isinstance(emotions["created_at"], datetime):
                    emotions["created_at"] = emotions["created_at"].isoformat()
            
            return emotions
            
        except Exception as e:
            logger.error(f"❌ Error fetching emotion metrics: {str(e)}")
            return None
    
    # ============= Cleanup Operations =============
    
    async def cleanup_old_sessions(self, days: int = 30):
        """Clean up old sessions and related data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Find old sessions
            old_sessions = await self.sessions_collection.find(
                {"created_at": {"$lt": cutoff_date}}
            ).to_list(length=None)
            
            session_ids = [s["session_id"] for s in old_sessions]
            
            if session_ids:
                # Delete related data
                await self.events_collection.delete_many({"session_id": {"$in": session_ids}})
                await self.emotions_collection.delete_many({"session_id": {"$in": session_ids}})
                await self.sessions_collection.delete_many({"session_id": {"$in": session_ids}})
                
                logger.info(f"🧹 Cleaned up {len(session_ids)} old sessions")
            
            return len(session_ids)
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
            return 0