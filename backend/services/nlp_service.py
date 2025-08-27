"""
🧠 NLP Service for content analysis
Provides sentiment analysis and named entity recognition
"""

from typing import Dict, List, Any, Optional
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NLPService:
    """Basic NLP service for text analysis"""
    
    def __init__(self):
        # Simple sentiment keywords (can be enhanced with proper NLP libraries)
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
            'love', 'like', 'happy', 'joy', 'pleased', 'satisfied', 'awesome'
        }
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry',
            'sad', 'disappointed', 'frustrated', 'annoyed', 'upset', 'worried'
        }
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text for sentiment and basic NLP features"""
        try:
            logger.debug(f"🧠 Analyzing text: {text[:50]}...")
            
            # Basic preprocessing
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Sentiment analysis
            sentiment = self._analyze_sentiment(words)
            
            # Named entity recognition (basic)
            entities = self._extract_entities(text)
            
            # Language features
            features = self._extract_features(text, words)
            
            return {
                'sentiment': sentiment,
                'entities': entities,
                'features': features,
                'word_count': len(words),
                'char_count': len(text)
            }
            
        except Exception as e:
            logger.error(f"❌ NLP analysis error: {str(e)}")
            return {
                'sentiment': {'score': 0.0, 'label': 'neutral'},
                'entities': [],
                'features': {},
                'word_count': 0,
                'char_count': len(text) if text else 0
            }
    
    def _analyze_sentiment(self, words: List[str]) -> Dict[str, Any]:
        """Simple sentiment analysis based on keyword matching"""
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        total_words = len(words)
        
        if total_words == 0:
            return {'score': 0.0, 'label': 'neutral'}
        
        # Calculate sentiment score (-1 to 1)
        score = (positive_count - negative_count) / max(total_words, 1)
        score = max(-1.0, min(1.0, score * 5))  # Amplify and clamp
        
        # Determine label
        if score > 0.1:
            label = 'positive'
        elif score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': score,
            'label': label,
            'positive_words': positive_count,
            'negative_words': negative_count
        }
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Basic named entity recognition"""
        entities = []
        
        # Email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({'text': email, 'type': 'EMAIL'})
        
        # Phone numbers (basic pattern)
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        for phone in phones:
            entities.append({'text': phone, 'type': 'PHONE'})
        
        # URLs
        urls = re.findall(r'https?://[^\s]+', text)
        for url in urls:
            entities.append({'text': url, 'type': 'URL'})
        
        # Money amounts
        money = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
        for amount in money:
            entities.append({'text': amount, 'type': 'MONEY'})
        
        return entities
    
    def _extract_features(self, text: str, words: List[str]) -> Dict[str, Any]:
        """Extract basic linguistic features"""
        return {
            'sentence_count': len(re.split(r'[.!?]+', text)),
            'avg_word_length': sum(len(word) for word in words) / max(len(words), 1),
            'question_count': text.count('?'),
            'exclamation_count': text.count('!'),
            'uppercase_ratio': sum(1 for char in text if char.isupper()) / max(len(text), 1),
            'has_profanity': any(word in ['damn', 'hell', 'crap'] for word in words),  # Basic list
        }