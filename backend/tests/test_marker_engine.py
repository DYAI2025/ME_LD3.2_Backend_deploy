"""
Tests for Marker Engine Core Service
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from services.marker_engine import MarkerEngine, MarkerDefinition, MarkerEvent
from services.mongodb_service import MongoDBService


@pytest.fixture
def mock_db_service():
    """Create mock MongoDB service"""
    mock = Mock(spec=MongoDBService)
    mock.get_markers = AsyncMock(return_value=[
        {
            "id": "A_TE_",
            "level": "ATO",
            "category": "test",
            "pattern": r"\btest\b",
            "description": "Test marker",
            "weight": 1.0
        }
    ])
    return mock


@pytest.fixture
async def marker_engine(mock_db_service):
    """Create MarkerEngine instance with mock DB"""
    engine = MarkerEngine(mock_db_service)
    await engine.initialize()
    return engine


class TestMarkerEngine:
    """Test suite for MarkerEngine"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, marker_engine):
        """Test engine initialization"""
        assert marker_engine.is_initialized
        assert len(marker_engine.markers) > 0
        assert "A_TE_" in marker_engine.markers
    
    @pytest.mark.asyncio
    async def test_analyze_basic_text(self, marker_engine):
        """Test basic text analysis"""
        content = "This is a test message for testing"
        result = await marker_engine.analyze(content)
        
        assert "markers" in result
        assert "emotions" in result
        assert "timeline" in result
        assert "profile" in result
        assert result["metadata"]["total_markers"] >= 0
    
    @pytest.mark.asyncio
    async def test_marker_hierarchy_levels(self, marker_engine):
        """Test four-tier marker hierarchy"""
        # Add markers for each level
        marker_engine.markers["A_EM_"] = MarkerDefinition(
            id="A_EM_",
            level="ATO",
            category="emotion",
            pattern=r"\bhappy\b",
            description="Emotion marker"
        )
        
        marker_engine.markers["S_CO_"] = MarkerDefinition(
            id="S_CO_",
            level="SEM",
            category="context",
            pattern=r"feeling\s+good",
            description="Semantic marker",
            context_required=True
        )
        
        marker_engine.markers["C_MO_"] = MarkerDefinition(
            id="C_MO_",
            level="CLU",
            category="mood",
            pattern="",
            description="Cluster marker",
            activation_rule="A_EM_ AND S_CO_"
        )
        
        marker_engine.markers["M_PS_"] = MarkerDefinition(
            id="M_PS_",
            level="MEMA",
            category="psychological",
            pattern="",
            description="Meta marker",
            activation_rule="C_MO_"
        )
        
        content = "I am happy and feeling good today"
        result = await marker_engine.analyze(content)
        
        levels = result["metadata"]["levels"]
        assert "ATO" in levels
        assert "SEM" in levels
    
    @pytest.mark.asyncio
    async def test_activation_rules(self, marker_engine):
        """Test DSL activation rules"""
        # Test AND rule
        assert marker_engine.evaluate_activation_rule(
            "A_TE_ AND B_TE_",
            {"events": [
                MarkerEvent("A_TE_", "ATO", datetime.now(), 0, "", 0.9),
                MarkerEvent("B_TE_", "ATO", datetime.now(), 0, "", 0.9)
            ]}
        )
        
        # Test OR rule
        assert marker_engine.evaluate_activation_rule(
            "A_TE_ OR B_TE_",
            {"events": [
                MarkerEvent("A_TE_", "ATO", datetime.now(), 0, "", 0.9)
            ]}
        )
        
        # Test COUNT rule
        assert marker_engine.evaluate_activation_rule(
            "A_TE_ COUNT > 2",
            {"events": [
                MarkerEvent("A_TE_", "ATO", datetime.now(), 0, "", 0.9),
                MarkerEvent("A_TE_", "ATO", datetime.now(), 0, "", 0.9),
                MarkerEvent("A_TE_", "ATO", datetime.now(), 0, "", 0.9)
            ]}
        )
    
    @pytest.mark.asyncio
    async def test_emotion_dynamics_integration(self, marker_engine):
        """Test EmotionDynamics calculation"""
        content = "I feel happy but then sad and angry"
        result = await marker_engine.analyze(content)
        
        assert "emotions" in result
        # EmotionDynamics should return metrics
        if result["emotions"]:
            assert "home_base" in result["emotions"] or \
                   "variability" in result["emotions"] or \
                   "drift_level" in result["emotions"]
    
    @pytest.mark.asyncio
    async def test_profile_generation(self, marker_engine):
        """Test profile generation from markers"""
        content = "Test message for profile generation"
        result = await marker_engine.analyze(content)
        
        assert "profile" in result
        profile = result["profile"]
        
        if profile:
            assert "summary" in profile
            assert "characteristics" in profile
            assert "risk_indicators" in profile
            assert "recommendations" in profile
    
    @pytest.mark.asyncio
    async def test_stream_analysis(self, marker_engine):
        """Test streaming analysis functionality"""
        content = "Line 1\nLine 2\nLine 3"
        events = []
        
        async for event in marker_engine.analyze_stream(content):
            events.append(event)
        
        assert len(events) > 0
        assert any(e["type"] == "complete" for e in events)
    
    @pytest.mark.asyncio
    async def test_timeline_creation(self, marker_engine):
        """Test timeline visualization data creation"""
        events = [
            MarkerEvent("A_TE_", "ATO", datetime.now(), 0, "test1", 0.9),
            MarkerEvent("S_TE_", "SEM", datetime.now(), 10, "test2", 0.8),
            MarkerEvent("C_TE_", "CLU", datetime.now(), 20, "test3", 0.7)
        ]
        
        timeline = marker_engine.create_timeline(events)
        
        assert len(timeline) == 3
        assert timeline[0]["position"] == 0
        assert timeline[1]["position"] == 10
        assert timeline[2]["position"] == 20
    
    @pytest.mark.asyncio
    async def test_error_handling(self, marker_engine):
        """Test error handling in analysis"""
        # Test with None content
        with pytest.raises(Exception):
            await marker_engine.analyze(None)
        
        # Test with invalid activation rule
        result = marker_engine.evaluate_activation_rule(
            "INVALID RULE FORMAT",
            {"events": []}
        )
        assert result is False  # Should return False on error
    
    @pytest.mark.asyncio
    async def test_nlp_enrichment_mock(self, marker_engine):
        """Test NLP enrichment with mocked service"""
        with patch.object(marker_engine.nlp, 'analyze', new_callable=AsyncMock) as mock_nlp:
            mock_nlp.return_value = {
                "sentiment": {"score": 0.8, "label": "positive"},
                "entities": [
                    {"text": "John", "type": "PERSON", "confidence": 0.9}
                ]
            }
            
            content = "John is very happy today"
            result = await marker_engine.analyze(content)
            
            # Check if NLP markers were created
            markers = result["markers"]
            assert any(m for m in markers if "S_PO_" in str(m))  # Positive sentiment
            assert any(m for m in markers if "S_EN_" in str(m))  # Entity marker


@pytest.mark.asyncio
class TestMarkerDefinition:
    """Test MarkerDefinition dataclass"""
    
    def test_marker_creation(self):
        """Test creating marker definition"""
        marker = MarkerDefinition(
            id="A_TE_",
            level="ATO",
            category="test",
            pattern=r"\btest\b",
            description="Test marker"
        )
        
        assert marker.id == "A_TE_"
        assert marker.level == "ATO"
        assert marker.weight == 1.0  # Default value
        assert marker.context_required is False  # Default value
    
    def test_marker_with_dependencies(self):
        """Test marker with dependencies"""
        marker = MarkerDefinition(
            id="C_TE_",
            level="CLU",
            category="test",
            pattern="",
            description="Cluster marker",
            dependencies=["A_TE_", "S_TE_"]
        )
        
        assert len(marker.dependencies) == 2
        assert "A_TE_" in marker.dependencies


@pytest.mark.asyncio
class TestMarkerEvent:
    """Test MarkerEvent dataclass"""
    
    def test_event_creation(self):
        """Test creating marker event"""
        event = MarkerEvent(
            marker_id="A_TE_",
            level="ATO",
            timestamp=datetime.now(),
            position=10,
            content="test",
            confidence=0.95
        )
        
        assert event.marker_id == "A_TE_"
        assert event.confidence == 0.95
        assert event.position == 10