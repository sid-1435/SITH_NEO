from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable
from ..core.wave import Wave, WaveCount
from ..config.rules import RuleDefinition, Severity, FibonacciRange, is_fibonacci_aligned

class PatternRule:
    """Executable pattern validation rule"""
    
    def __init__(self, definition: RuleDefinition, condition: Callable[[List[Wave]], bool]):
        self.definition = definition
        self.condition = condition
        self.name = definition.name
        self.severity_name, self.penalty = definition.severity
        self.description = definition.description
    
    def validate(self, waves: List[Wave]) -> Dict:
        """
        Validate the rule against a wave sequence.
        
        Returns:
            dict with keys: passed (bool), message (str), penalty (int), severity (str)
        """
        try:
            passed = self.condition(waves)
            return {
                'passed': passed,
                'message': self.description,
                'penalty': 0 if passed else self.penalty,
                'severity': self.severity_name
            }
        except Exception as e:
            return {
                'passed': False,
                'message': f"Rule evaluation error: {str(e)}",
                'penalty': self.penalty,
                'severity': self.severity_name
            }


class BasePattern(ABC):
    """
    Abstract base class for all NEoWave patterns.
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.rules: List[PatternRule] = []
        self._initialize_rules()
    
    @abstractmethod
    def _initialize_rules(self):
        """Initialize pattern-specific rules. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def required_wave_count(self) -> int:
        """Return the number of waves required for this pattern"""
        pass
    
    @abstractmethod
    def expected_labels(self) -> List[str]:
        """Return the expected wave labels for this pattern"""
        pass
    
    def validate(self, waves: List[Wave]) -> WaveCount:
        """
        Validate a wave sequence against this pattern.
        
        Returns:
            WaveCount object with confidence score and violations
        """
        # Check wave count
        if len(waves) != self.required_wave_count():
            return WaveCount(
                waves=waves,
                pattern_name=self.name,
                confidence=0.0,
                description=f"Invalid wave count. Expected {self.required_wave_count()}, got {len(waves)}"
            )
        
        wave_count = WaveCount(
            waves=waves,
            pattern_name=self.name,
            confidence=100.0,  # Start at 100%, deduct for violations
            description=f"{self.name} pattern"
        )
        
        # Validate each rule
        for rule in self.rules:
            result = rule.validate(waves)
            
            if not result['passed']:
                wave_count.confidence -= result['penalty']
                wave_count.add_violation(
                    rule_name=rule.name,
                    severity=result['severity'],
                    message=result['message']
                )
                
                # If it's a "must" rule and failed, pattern is invalid
                if result['severity'] == 'must':
                    wave_count.confidence = 0.0
                    wave_count.warnings.append(f"CRITICAL: {result['message']}")
                    break
        
        # Ensure confidence is between 0 and 100
        wave_count.confidence = max(0.0, min(100.0, wave_count.confidence))
        
        # Add targets if pattern is valid
        if wave_count.confidence > 0:
            self._calculate_targets(wave_count)
        
        return wave_count
    
    @abstractmethod
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate price targets for the pattern. Must be implemented by subclasses."""
        pass
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def fibonacci_check(self, wave: Wave, reference: Wave, 
                       fib_range: FibonacciRange) -> bool:
        """Check if wave is within Fibonacci ratio range of reference"""
        ratio = wave.fibonacci_relationship(reference)
        return fib_range.contains(ratio)
    
    def time_check(self, wave: Wave, reference: Wave,
                   min_ratio: float, max_ratio: float) -> bool:
        """Check if wave time is within ratio range of reference"""
        ratio = wave.time_relationship(reference)
        return min_ratio <= ratio <= max_ratio
    
    def overlap_check(self, wave1: Wave, wave2: Wave) -> bool:
        """Check if two waves overlap in price"""
        return not (wave1.high_price < wave2.low_price or 
                   wave1.low_price > wave2.high_price)
    
    def retracement_percent(self, corrective_wave: Wave, motive_wave: Wave) -> float:
        """Calculate retracement percentage"""
        if abs(motive_wave.price_movement) == 0:
            return 0
        return abs(corrective_wave.price_movement) / abs(motive_wave.price_movement)
    
    def is_shortest(self, wave: Wave, wave_list: List[Wave]) -> bool:
        """Check if given wave is the shortest in the list"""
        wave_length = abs(wave.price_movement)
        return all(wave_length <= abs(w.price_movement) for w in wave_list)