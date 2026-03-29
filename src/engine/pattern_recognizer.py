from typing import List, Dict, Optional
from ..core.wave import Wave, WaveCount
from ..patterns.impulse import ImpulsePattern
from ..patterns.zigzag import ZigzagPattern
from ..patterns.flat import FlatPattern
from ..patterns.triangle import TrianglePattern
from ..patterns.diametric import DiametricPattern
from ..patterns.symmetrical import SymmetricalPattern
from ..patterns.diagonal import DiagonalPattern

class PatternRecognizer:
    """
    Main engine for recognizing NEoWave patterns in wave sequences.
    """
    
    # Pattern labels mapping
    PATTERN_LABELS = {
        'impulse': ['1', '2', '3', '4', '5'],
        'leading_diagonal': ['1', '2', '3', '4', '5'],
        'terminal_diagonal': ['1', '2', '3', '4', '5'],
        'zigzag': ['A', 'B', 'C'],
        'flat': ['A', 'B', 'C'],
        'triangle': ['A', 'B', 'C', 'D', 'E'],
        'diametric': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
        'symmetrical': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
    }
    
    def __init__(self):
        # Initialize all pattern detectors
        self.patterns = {
            'impulse': ImpulsePattern(),
            'leading_diagonal': DiagonalPattern(is_leading=True),
            'terminal_diagonal': DiagonalPattern(is_leading=False),
            'zigzag': ZigzagPattern(),
            'flat': FlatPattern(),
            'triangle': TrianglePattern(),
            'diametric': DiametricPattern(),
            'symmetrical': SymmetricalPattern(),
        }
    
    def get_labels_for_pattern(self, pattern_name: str) -> List[str]:
        """Get the proper wave labels for a pattern type"""
        return self.PATTERN_LABELS.get(pattern_name, [])
    
    def recognize_all(self, waves: List[Wave], min_confidence: float = 0.0) -> List[WaveCount]:
        """
        Try to recognize all possible patterns in the wave sequence.
        
        Args:
            waves: List of Wave objects to analyze
            min_confidence: Minimum confidence threshold (0-100)
        
        Returns:
            List of WaveCount objects sorted by confidence (highest first)
        """
        valid_counts = []
        
        for pattern_name, pattern in self.patterns.items():
            if len(waves) == pattern.required_wave_count():
                # Ensure waves have correct labels for this pattern
                expected_labels = self.get_labels_for_pattern(pattern_name)
                
                # Re-label waves if needed
                labeled_waves = self._apply_labels(waves, expected_labels)
                
                # Validate pattern
                wave_count = pattern.validate(labeled_waves)
                
                if wave_count.confidence >= min_confidence:
                    valid_counts.append(wave_count)
        
        # Sort by confidence
        valid_counts.sort(key=lambda x: x.confidence, reverse=True)
        
        return valid_counts
    
    def _apply_labels(self, waves: List[Wave], labels: List[str]) -> List[Wave]:
        """Apply correct labels to waves"""
        if len(waves) != len(labels):
            return waves
        
        for i, (wave, label) in enumerate(zip(waves, labels)):
            wave.label = label
        
        return waves
    
    def recognize_best(self, waves: List[Wave]) -> WaveCount:
        """
        Find the best matching pattern for the wave sequence.
        """
        all_counts = self.recognize_all(waves, min_confidence=0.0)
        
        if all_counts:
            return all_counts[0]
        
        return WaveCount(
            waves=waves,
            pattern_name="Unknown",
            confidence=0.0,
            description="No valid pattern recognized"
        )
    
    def recognize_with_labels(self, waves: List[Wave], pattern_name: str) -> Optional[WaveCount]:
        """
        Recognize a specific pattern and ensure proper labeling.
        
        Args:
            waves: List of Wave objects
            pattern_name: Name of pattern to validate against
        
        Returns:
            WaveCount with properly labeled waves, or None if invalid
        """
        pattern = self.patterns.get(pattern_name)
        
        if not pattern:
            return None
        
        if len(waves) != pattern.required_wave_count():
            return None
        
        # Apply correct labels
        labels = self.get_labels_for_pattern(pattern_name)
        labeled_waves = self._apply_labels(waves, labels)
        
        # Validate
        wave_count = pattern.validate(labeled_waves)
        
        return wave_count