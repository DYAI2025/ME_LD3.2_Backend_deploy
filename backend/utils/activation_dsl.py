"""
🔧 Activation DSL Parser
Parses and evaluates marker activation rules using Domain Specific Language
"""

from typing import Dict, List, Any, Set
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ActivationDSLParser:
    """Parser for marker activation rules"""
    
    def __init__(self):
        # Supported operators
        self.operators = {
            'AND': self._eval_and,
            'OR': self._eval_or,
            'NOT': self._eval_not,
            '&': self._eval_and,
            '|': self._eval_or,
            '!': self._eval_not,
        }
    
    def parse_and_evaluate(self, rule: str, active_markers: Set[str]) -> bool:
        """Parse and evaluate an activation rule"""
        try:
            if not rule or not rule.strip():
                return True
            
            logger.debug(f"🔧 Evaluating rule: {rule} with markers: {active_markers}")
            
            # Tokenize the rule
            tokens = self._tokenize(rule)
            
            # Parse and evaluate
            result = self._evaluate_tokens(tokens, active_markers)
            
            logger.debug(f"🔧 Rule result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ DSL parsing error for rule '{rule}': {str(e)}")
            return False
    
    def _tokenize(self, rule: str) -> List[str]:
        """Tokenize the rule into components"""
        # Replace operator symbols with words for easier parsing
        rule = rule.replace('&&', ' AND ').replace('||', ' OR ').replace('!', ' NOT ')
        
        # Split by whitespace and filter empty tokens
        tokens = [token.strip() for token in re.split(r'\s+', rule) if token.strip()]
        
        return tokens
    
    def _evaluate_tokens(self, tokens: List[str], active_markers: Set[str]) -> bool:
        """Evaluate tokenized rule"""
        if not tokens:
            return True
        
        # Handle single marker
        if len(tokens) == 1:
            return self._is_marker_active(tokens[0], active_markers)
        
        # Handle NOT operator
        if tokens[0].upper() == 'NOT':
            if len(tokens) >= 2:
                return not self._is_marker_active(tokens[1], active_markers)
            return False
        
        # Handle binary operations (AND, OR)
        result = self._is_marker_active(tokens[0], active_markers)
        
        i = 1
        while i < len(tokens) - 1:
            operator = tokens[i].upper()
            operand = tokens[i + 1]
            
            if operator in self.operators:
                operand_value = self._is_marker_active(operand, active_markers)
                result = self.operators[operator](result, operand_value)
            
            i += 2
        
        return result
    
    def _is_marker_active(self, marker_id: str, active_markers: Set[str]) -> bool:
        """Check if a marker is active"""
        # Remove any parentheses or extra characters
        clean_marker = marker_id.strip('()')
        return clean_marker in active_markers
    
    def _eval_and(self, left: bool, right: bool) -> bool:
        """Evaluate AND operation"""
        return left and right
    
    def _eval_or(self, left: bool, right: bool) -> bool:
        """Evaluate OR operation"""
        return left or right
    
    def _eval_not(self, left: bool, right: bool = None) -> bool:
        """Evaluate NOT operation (unary)"""
        return not left
    
    def extract_dependencies(self, rule: str) -> List[str]:
        """Extract marker dependencies from a rule"""
        if not rule:
            return []
        
        # Find all marker IDs (format: X_XX_ where X is alphanumeric)
        marker_pattern = r'\b[A-Z]_[A-Z]{2}_\b'
        dependencies = re.findall(marker_pattern, rule)
        
        return list(set(dependencies))  # Remove duplicates
    
    def validate_rule(self, rule: str) -> Dict[str, Any]:
        """Validate a DSL rule syntax"""
        try:
            if not rule or not rule.strip():
                return {'valid': True, 'message': 'Empty rule (always true)'}
            
            # Extract dependencies
            dependencies = self.extract_dependencies(rule)
            
            # Test parse with dummy markers
            dummy_markers = set(dependencies)
            self.parse_and_evaluate(rule, dummy_markers)
            
            return {
                'valid': True,
                'message': 'Rule syntax is valid',
                'dependencies': dependencies
            }
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'Invalid rule syntax: {str(e)}',
                'dependencies': []
            }