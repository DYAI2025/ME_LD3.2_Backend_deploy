"""
📊 Emotion Dynamics Calculator
Calculates emotional state changes and patterns over time
"""

from typing import Dict, List, Any, Optional
import math
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmotionDynamicsCalculator:
    """Calculates emotion dynamics from marker events"""
    
    def __init__(self):
        # Emotion mappings for different marker types
        self.emotion_mappings = {
            'A_EM_': {'valence': 0.8, 'arousal': 0.6, 'dominance': 0.5},  # Positive emotion
            'A_FE_': {'valence': -0.5, 'arousal': 0.7, 'dominance': 0.3}, # Fear
            'A_AN_': {'valence': -0.8, 'arousal': 0.9, 'dominance': 0.8}, # Anger
            'S_PO_': {'valence': 0.6, 'arousal': 0.4, 'dominance': 0.6},  # Positive sentiment
            'S_NE_': {'valence': -0.6, 'arousal': 0.5, 'dominance': 0.4}, # Negative sentiment
            'C_MO_': {'valence': 0.0, 'arousal': 0.3, 'dominance': 0.5},  # Mood cluster
        }
    
    def calculate(self, events: List[Any], time_window: int = 300) -> Dict[str, Any]:
        """Calculate emotion dynamics from marker events"""
        try:
            if not events:
                return self._default_emotions()
            
            logger.debug(f"📊 Calculating emotions for {len(events)} events")
            
            # Group events by time windows
            time_series = self._create_time_series(events, time_window)
            
            # Calculate emotion values for each time window
            emotion_timeline = []
            for timestamp, window_events in time_series.items():
                emotions = self._calculate_window_emotions(window_events)
                emotion_timeline.append({
                    'timestamp': timestamp,
                    'emotions': emotions
                })
            
            # Calculate overall metrics
            if emotion_timeline:
                overall = self._calculate_overall_emotions(emotion_timeline)
                drift_rate = self._calculate_drift_rate(emotion_timeline)
                stability = self._calculate_stability(emotion_timeline)
            else:
                overall = self._default_emotions()
                drift_rate = 0.0
                stability = 1.0
            
            return {
                'valence': overall['valence'],
                'arousal': overall['arousal'],
                'dominance': overall['dominance'],
                'drift_rate': drift_rate,
                'stability': stability,
                'timeline': emotion_timeline[-10:] if emotion_timeline else []  # Last 10 windows
            }
            
        except Exception as e:
            logger.error(f"❌ Emotion calculation error: {str(e)}")
            return self._default_emotions()
    
    def _default_emotions(self) -> Dict[str, float]:
        """Return default neutral emotions"""
        return {
            'valence': 0.0,
            'arousal': 0.5,
            'dominance': 0.5,
            'drift_rate': 0.0,
            'stability': 1.0
        }
    
    def _create_time_series(self, events: List[Any], window_seconds: int) -> Dict[datetime, List[Any]]:
        """Group events into time windows"""
        time_series = {}
        
        for event in events:
            # Get timestamp from event (handle different event types)
            if hasattr(event, 'timestamp'):
                timestamp = event.timestamp
            elif isinstance(event, dict) and 'timestamp' in event:
                timestamp = event['timestamp']
            else:
                timestamp = datetime.utcnow()
            
            # Round timestamp to window boundary
            window_start = timestamp.replace(
                second=(timestamp.second // window_seconds) * window_seconds,
                microsecond=0
            )
            
            if window_start not in time_series:
                time_series[window_start] = []
            time_series[window_start].append(event)
        
        return time_series
    
    def _calculate_window_emotions(self, events: List[Any]) -> Dict[str, float]:
        """Calculate emotions for events in a time window"""
        if not events:
            return {'valence': 0.0, 'arousal': 0.5, 'dominance': 0.5}
        
        total_valence = 0.0
        total_arousal = 0.0
        total_dominance = 0.0
        total_weight = 0.0
        
        for event in events:
            # Get marker ID from event
            if hasattr(event, 'marker_id'):
                marker_id = event.marker_id
                confidence = getattr(event, 'confidence', 1.0)
            elif isinstance(event, dict):
                marker_id = event.get('marker_id', 'unknown')
                confidence = event.get('confidence', 1.0)
            else:
                marker_id = 'unknown'
                confidence = 1.0
            
            # Get emotion values for this marker
            if marker_id in self.emotion_mappings:
                emotions = self.emotion_mappings[marker_id]
                weight = confidence
                
                total_valence += emotions['valence'] * weight
                total_arousal += emotions['arousal'] * weight
                total_dominance += emotions['dominance'] * weight
                total_weight += weight
        
        if total_weight == 0:
            return {'valence': 0.0, 'arousal': 0.5, 'dominance': 0.5}
        
        return {
            'valence': total_valence / total_weight,
            'arousal': total_arousal / total_weight,
            'dominance': total_dominance / total_weight
        }
    
    def _calculate_overall_emotions(self, timeline: List[Dict]) -> Dict[str, float]:
        """Calculate overall emotion averages"""
        if not timeline:
            return {'valence': 0.0, 'arousal': 0.5, 'dominance': 0.5}
        
        total_valence = sum(item['emotions']['valence'] for item in timeline)
        total_arousal = sum(item['emotions']['arousal'] for item in timeline)
        total_dominance = sum(item['emotions']['dominance'] for item in timeline)
        count = len(timeline)
        
        return {
            'valence': total_valence / count,
            'arousal': total_arousal / count,
            'dominance': total_dominance / count
        }
    
    def _calculate_drift_rate(self, timeline: List[Dict]) -> float:
        """Calculate rate of emotional change"""
        if len(timeline) < 2:
            return 0.0
        
        total_change = 0.0
        for i in range(1, len(timeline)):
            prev_emotions = timeline[i-1]['emotions']
            curr_emotions = timeline[i]['emotions']
            
            # Calculate Euclidean distance in emotion space
            valence_diff = curr_emotions['valence'] - prev_emotions['valence']
            arousal_diff = curr_emotions['arousal'] - prev_emotions['arousal']
            dominance_diff = curr_emotions['dominance'] - prev_emotions['dominance']
            
            change = math.sqrt(valence_diff**2 + arousal_diff**2 + dominance_diff**2)
            total_change += change
        
        return total_change / (len(timeline) - 1)
    
    def _calculate_stability(self, timeline: List[Dict]) -> float:
        """Calculate emotional stability (1 - variance)"""
        if len(timeline) < 2:
            return 1.0
        
        # Calculate variance in valence (primary emotion dimension)
        valences = [item['emotions']['valence'] for item in timeline]
        mean_valence = sum(valences) / len(valences)
        variance = sum((v - mean_valence)**2 for v in valences) / len(valences)
        
        # Convert variance to stability (0-1 scale)
        stability = max(0.0, 1.0 - variance)
        return stability