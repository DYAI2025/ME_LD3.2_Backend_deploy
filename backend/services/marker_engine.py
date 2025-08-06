"""
🎯 Marker Engine Core Service
Implements the four-tier Lean-Deep marker hierarchy (ATO→SEM→CLU→MEMA)
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import hashlib
import yaml
from dataclasses import dataclass, asdict

from .mongodb_service import MongoDBService
from .nlp_service import NLPService
from .emotion_dynamics import EmotionDynamicsCalculator
from utils.logger import setup_logger
from utils.activation_dsl import ActivationDSLParser

logger = setup_logger(__name__)

@dataclass
class MarkerDefinition:
    """Marker definition with four-letter prefix"""
    id: str  # Four-letter prefix (e.g., A_CO_, S_EM_, C_RE_, M_PS_)
    level: str  # ATO, SEM, CLU, MEMA
    category: str
    pattern: str
    description: str
    weight: float = 1.0
    activation_rule: Optional[str] = None
    context_required: bool = False
    dependencies: List[str] = None

@dataclass
class MarkerEvent:
    """Detected marker event"""
    marker_id: str
    level: str
    timestamp: datetime
    position: int
    content: str
    confidence: float
    context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

class MarkerEngine:
    """
    Core Marker Engine implementing Lean-Deep 3.2 hierarchy
    """
    
    def __init__(self, db_service: MongoDBService):
        self.db = db_service
        self.nlp = NLPService()
        self.emotion_calc = EmotionDynamicsCalculator()
        self.dsl_parser = ActivationDSLParser()
        
        self.markers: Dict[str, MarkerDefinition] = {}
        self.is_initialized = False
        
        # Marker level hierarchy
        self.LEVELS = {
            "ATO": 1,  # Atomic
            "SEM": 2,  # Semantic
            "CLU": 3,  # Cluster
            "MEMA": 4  # Meta-Marker
        }
        
    async def initialize(self):
        """Initialize marker engine and load definitions"""
        try:
            logger.info("🚀 Initializing Marker Engine...")
            
            # Load marker definitions from database
            await self.load_markers()
            
            # Initialize NLP service
            await self.nlp.initialize()
            
            # Initialize emotion dynamics
            self.emotion_calc.initialize()
            
            self.is_initialized = True
            logger.info(f"✅ Marker Engine initialized with {len(self.markers)} markers")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Marker Engine: {str(e)}")
            raise
    
    async def load_markers(self):
        """Load marker definitions from MongoDB"""
        try:
            # Get all marker definitions
            markers_data = await self.db.get_markers({})
            
            for marker_data in markers_data:
                marker = MarkerDefinition(
                    id=marker_data["id"],
                    level=marker_data["level"],
                    category=marker_data["category"],
                    pattern=marker_data["pattern"],
                    description=marker_data.get("description", ""),
                    weight=marker_data.get("weight", 1.0),
                    activation_rule=marker_data.get("activation_rule"),
                    context_required=marker_data.get("context_required", False),
                    dependencies=marker_data.get("dependencies", [])
                )
                self.markers[marker.id] = marker
                
            logger.info(f"📚 Loaded {len(self.markers)} marker definitions")
            
        except Exception as e:
            logger.error(f"❌ Error loading markers: {str(e)}")
            # Load default markers if database is empty
            await self.load_default_markers()
    
    async def load_default_markers(self):
        """Load default marker definitions"""
        default_markers = [
            # ATO (Atomic) markers
            MarkerDefinition("A_CO_", "ATO", "communication", r"\b(hello|hi|hey)\b", "Greeting"),
            MarkerDefinition("A_EM_", "ATO", "emotion", r"\b(happy|sad|angry)\b", "Basic emotion"),
            MarkerDefinition("A_QU_", "ATO", "question", r"\?", "Question marker"),
            
            # SEM (Semantic) markers
            MarkerDefinition("S_EM_", "SEM", "emotion", r"feeling\s+(good|bad|great)", "Emotion expression", context_required=True),
            MarkerDefinition("S_IN_", "SEM", "intent", r"(want|need|wish)\s+to", "Intent expression"),
            MarkerDefinition("S_CO_", "SEM", "conflict", r"(disagree|oppose|against)", "Conflict indicator"),
            
            # CLU (Cluster) markers
            MarkerDefinition("C_RE_", "CLU", "relationship", "", "Relationship pattern", activation_rule="S_EM_ AND S_CO_"),
            MarkerDefinition("C_MO_", "CLU", "mood", "", "Mood cluster", activation_rule="A_EM_ COUNT > 3"),
            
            # MEMA (Meta-Marker) markers
            MarkerDefinition("M_PS_", "MEMA", "psychological", "", "Psychological state", activation_rule="C_RE_ AND C_MO_"),
            MarkerDefinition("M_DR_", "MEMA", "drift", "", "Emotion drift", activation_rule="DRIFT_HIGH")
        ]
        
        for marker in default_markers:
            self.markers[marker.id] = marker
            
        logger.info(f"📝 Loaded {len(default_markers)} default markers")
    
    async def analyze(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content through the four-tier marker hierarchy
        """
        try:
            logger.info("🔍 Starting marker analysis...")
            
            # Initialize analysis context
            analysis_context = {
                "content": content,
                "timestamp": datetime.utcnow(),
                "context": context or {},
                "options": options or {},
                "events": [],
                "nlp_enrichment": None,
                "emotions": None,
                "profile": {}
            }
            
            # Step 1: Initial scan (ATO + simple SEM)
            await self.initial_scan(analysis_context)
            
            # Step 2: NLP enrichment
            await self.nlp_enrichment(analysis_context)
            
            # Step 3: Contextual re-scan (CLU + MEMA)
            await self.contextual_rescan(analysis_context)
            
            # Step 4: Emotion dynamics calculation
            await self.calculate_emotions(analysis_context)
            
            # Step 5: Generate profile
            await self.generate_profile(analysis_context)
            
            # Prepare response
            result = {
                "markers": [asdict(event) for event in analysis_context["events"]],
                "emotions": analysis_context["emotions"],
                "timeline": self.create_timeline(analysis_context["events"]),
                "profile": analysis_context["profile"],
                "metadata": {
                    "total_markers": len(analysis_context["events"]),
                    "levels": self.count_by_level(analysis_context["events"]),
                    "processing_time": (datetime.utcnow() - analysis_context["timestamp"]).total_seconds()
                }
            }
            
            logger.info(f"✅ Analysis complete: {result['metadata']['total_markers']} markers detected")
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis error: {str(e)}")
            raise
    
    async def initial_scan(self, context: Dict[str, Any]):
        """Step 1: Initial pattern matching for ATO and simple SEM markers"""
        content = context["content"]
        events = []
        
        for marker_id, marker in self.markers.items():
            if marker.level not in ["ATO", "SEM"]:
                continue
                
            if marker.pattern:
                # Pattern-based matching
                matches = re.finditer(marker.pattern, content, re.IGNORECASE)
                for match in matches:
                    event = MarkerEvent(
                        marker_id=marker.id,
                        level=marker.level,
                        timestamp=context["timestamp"],
                        position=match.start(),
                        content=match.group(0),
                        confidence=0.9 if marker.level == "ATO" else 0.8,
                        context={"match": match.group(0)},
                        metadata={"category": marker.category}
                    )
                    events.append(event)
        
        context["events"].extend(events)
        logger.info(f"📍 Initial scan: {len(events)} ATO/SEM markers detected")
    
    async def nlp_enrichment(self, context: Dict[str, Any]):
        """Step 2: Enrich with Spark NLP analysis"""
        try:
            content = context["content"]
            
            # Run NLP analysis
            nlp_result = await self.nlp.analyze(content)
            
            context["nlp_enrichment"] = nlp_result
            
            # Create SEM markers from NLP results
            events = []
            
            # Sentiment markers
            if nlp_result.get("sentiment"):
                sentiment = nlp_result["sentiment"]
                if sentiment["score"] > 0.7:
                    events.append(MarkerEvent(
                        marker_id="S_PO_",
                        level="SEM",
                        timestamp=context["timestamp"],
                        position=0,
                        content="Positive sentiment",
                        confidence=sentiment["score"],
                        metadata={"sentiment": sentiment}
                    ))
                elif sentiment["score"] < -0.7:
                    events.append(MarkerEvent(
                        marker_id="S_NE_",
                        level="SEM",
                        timestamp=context["timestamp"],
                        position=0,
                        content="Negative sentiment",
                        confidence=abs(sentiment["score"]),
                        metadata={"sentiment": sentiment}
                    ))
            
            # Entity markers
            for entity in nlp_result.get("entities", []):
                events.append(MarkerEvent(
                    marker_id=f"S_EN_{entity['type'][:2].upper()}_",
                    level="SEM",
                    timestamp=context["timestamp"],
                    position=entity.get("position", 0),
                    content=entity["text"],
                    confidence=entity.get("confidence", 0.8),
                    metadata={"entity": entity}
                ))
            
            context["events"].extend(events)
            logger.info(f"🧠 NLP enrichment: {len(events)} additional markers")
            
        except Exception as e:
            logger.error(f"❌ NLP enrichment error: {str(e)}")
    
    async def contextual_rescan(self, context: Dict[str, Any]):
        """Step 3: Activate CLU and MEMA markers based on activation rules"""
        events = []
        existing_markers = {e.marker_id for e in context["events"]}
        
        for marker_id, marker in self.markers.items():
            if marker.level not in ["CLU", "MEMA"]:
                continue
                
            if marker.activation_rule:
                # Evaluate activation rule
                if self.evaluate_activation_rule(marker.activation_rule, context):
                    event = MarkerEvent(
                        marker_id=marker.id,
                        level=marker.level,
                        timestamp=context["timestamp"],
                        position=0,
                        content=f"Activated: {marker.description}",
                        confidence=0.85,
                        metadata={
                            "activation_rule": marker.activation_rule,
                            "triggered_by": list(existing_markers)
                        }
                    )
                    events.append(event)
        
        context["events"].extend(events)
        logger.info(f"🔄 Contextual rescan: {len(events)} CLU/MEMA markers activated")
    
    def evaluate_activation_rule(self, rule: str, context: Dict[str, Any]) -> bool:
        """Evaluate DSL activation rules"""
        try:
            # Parse and evaluate the rule
            existing_markers = [e.marker_id for e in context["events"]]
            
            # Simple rule evaluation (to be enhanced with PEG.js parser)
            if "AND" in rule:
                required = rule.split(" AND ")
                return all(r.strip() in existing_markers for r in required)
            elif "OR" in rule:
                options = rule.split(" OR ")
                return any(o.strip() in existing_markers for o in options)
            elif "COUNT" in rule:
                # Parse count rules like "A_EM_ COUNT > 3"
                parts = rule.split()
                if len(parts) >= 4:
                    marker_prefix = parts[0]
                    operator = parts[2]
                    threshold = int(parts[3])
                    count = sum(1 for e in context["events"] if e.marker_id.startswith(marker_prefix))
                    
                    if operator == ">":
                        return count > threshold
                    elif operator == ">=":
                        return count >= threshold
                    elif operator == "<":
                        return count < threshold
                    elif operator == "<=":
                        return count <= threshold
                    elif operator == "==":
                        return count == threshold
            elif "DRIFT_HIGH" in rule:
                # Check emotion drift
                emotions = context.get("emotions", {})
                return emotions.get("drift_level") == "high"
            
            # Default: check if marker exists
            return rule in existing_markers
            
        except Exception as e:
            logger.error(f"Rule evaluation error: {str(e)}")
            return False
    
    async def calculate_emotions(self, context: Dict[str, Any]):
        """Step 4: Calculate EmotionDynamics metrics"""
        try:
            # Extract emotion-related events
            emotion_events = [
                e for e in context["events"]
                if e.metadata and e.metadata.get("category") == "emotion"
            ]
            
            # Calculate emotion dynamics
            emotions = self.emotion_calc.calculate(
                events=emotion_events,
                content=context["content"],
                nlp_data=context.get("nlp_enrichment")
            )
            
            context["emotions"] = emotions
            
            # Generate drift markers if needed
            if emotions.get("drift_level") == "high":
                drift_marker = MarkerEvent(
                    marker_id="C_EMO_DRIFT_HIGH",
                    level="CLU",
                    timestamp=context["timestamp"],
                    position=0,
                    content="High emotion drift detected",
                    confidence=0.9,
                    metadata={"emotions": emotions}
                )
                context["events"].append(drift_marker)
                
            logger.info(f"😊 Emotion dynamics calculated: {emotions.get('home_base', 0):.2f} base")
            
        except Exception as e:
            logger.error(f"❌ Emotion calculation error: {str(e)}")
            context["emotions"] = {}
    
    async def generate_profile(self, context: Dict[str, Any]):
        """Step 5: Generate dynamic profile based on markers"""
        try:
            profile = {
                "timestamp": context["timestamp"].isoformat(),
                "summary": {
                    "total_markers": len(context["events"]),
                    "dominant_level": self.get_dominant_level(context["events"]),
                    "key_patterns": self.extract_key_patterns(context["events"])
                },
                "characteristics": self.extract_characteristics(context),
                "risk_indicators": self.identify_risks(context),
                "recommendations": self.generate_recommendations(context)
            }
            
            context["profile"] = profile
            logger.info("📋 Profile generated successfully")
            
        except Exception as e:
            logger.error(f"❌ Profile generation error: {str(e)}")
            context["profile"] = {}
    
    async def analyze_stream(self, content: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream analysis results in real-time"""
        try:
            # Split content into chunks for streaming
            chunks = content.split("\n")
            accumulated_content = ""
            
            for chunk in chunks:
                accumulated_content += chunk + "\n"
                
                # Analyze current accumulated content
                result = await self.analyze(accumulated_content)
                
                # Yield incremental results
                yield {
                    "type": "incremental",
                    "content": chunk,
                    "markers": result["markers"][-5:],  # Last 5 markers
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await asyncio.sleep(0.1)  # Small delay for streaming effect
            
            # Final complete result
            final_result = await self.analyze(content)
            yield {
                "type": "complete",
                "result": final_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Stream analysis error: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Helper methods
    
    def create_timeline(self, events: List[MarkerEvent]) -> List[Dict[str, Any]]:
        """Create timeline visualization data"""
        timeline = []
        for event in sorted(events, key=lambda e: e.position):
            timeline.append({
                "position": event.position,
                "marker_id": event.marker_id,
                "level": event.level,
                "content": event.content,
                "confidence": event.confidence
            })
        return timeline
    
    def count_by_level(self, events: List[MarkerEvent]) -> Dict[str, int]:
        """Count markers by level"""
        counts = {"ATO": 0, "SEM": 0, "CLU": 0, "MEMA": 0}
        for event in events:
            counts[event.level] = counts.get(event.level, 0) + 1
        return counts
    
    def get_dominant_level(self, events: List[MarkerEvent]) -> str:
        """Get the most frequent marker level"""
        if not events:
            return "NONE"
        counts = self.count_by_level(events)
        return max(counts, key=counts.get)
    
    def extract_key_patterns(self, events: List[MarkerEvent]) -> List[str]:
        """Extract key patterns from detected markers"""
        patterns = []
        marker_groups = {}
        
        for event in events:
            category = event.metadata.get("category", "unknown")
            if category not in marker_groups:
                marker_groups[category] = []
            marker_groups[category].append(event)
        
        for category, group in marker_groups.items():
            if len(group) >= 3:
                patterns.append(f"Repeated {category} pattern ({len(group)} occurrences)")
        
        return patterns[:5]  # Top 5 patterns
    
    def extract_characteristics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral characteristics"""
        events = context["events"]
        emotions = context.get("emotions", {})
        
        return {
            "communication_style": self.analyze_communication_style(events),
            "emotional_profile": {
                "stability": emotions.get("variability", 0),
                "baseline": emotions.get("home_base", 0),
                "reactivity": emotions.get("rise_rate", 0)
            },
            "cognitive_patterns": self.analyze_cognitive_patterns(events)
        }
    
    def analyze_communication_style(self, events: List[MarkerEvent]) -> str:
        """Analyze communication style from markers"""
        question_count = sum(1 for e in events if "QU" in e.marker_id)
        emotion_count = sum(1 for e in events if "EM" in e.marker_id)
        
        if question_count > len(events) * 0.3:
            return "Inquisitive"
        elif emotion_count > len(events) * 0.4:
            return "Emotional"
        else:
            return "Balanced"
    
    def analyze_cognitive_patterns(self, events: List[MarkerEvent]) -> List[str]:
        """Analyze cognitive patterns"""
        patterns = []
        
        # Check for specific marker combinations
        marker_ids = {e.marker_id for e in events}
        
        if "C_RE_" in marker_ids and "C_MO_" in marker_ids:
            patterns.append("Complex emotional processing")
        
        if "M_PS_" in marker_ids:
            patterns.append("Deep psychological indicators")
        
        return patterns
    
    def identify_risks(self, context: Dict[str, Any]) -> List[str]:
        """Identify potential risk indicators"""
        risks = []
        events = context["events"]
        emotions = context.get("emotions", {})
        
        # Check for high-risk markers
        for event in events:
            if "DRIFT_HIGH" in event.marker_id:
                risks.append("High emotional instability")
            if "CONFLICT" in event.content.upper():
                risks.append("Conflict indicators present")
        
        # Check emotion metrics
        if emotions.get("variability", 0) > 0.7:
            risks.append("High emotional variability")
        
        return risks
    
    def generate_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        risks = self.identify_risks(context)
        
        if "High emotional instability" in risks:
            recommendations.append("Consider emotional regulation techniques")
        
        if "Conflict indicators present" in risks:
            recommendations.append("Address conflict resolution strategies")
        
        if not recommendations:
            recommendations.append("Continue monitoring patterns")
        
        return recommendations