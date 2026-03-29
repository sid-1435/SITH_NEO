from typing import List
import numpy as np
from .base import BasePattern, PatternRule
from ..core.wave import Wave, WaveCount
from ..config.rules import DIAMETRIC_RULES, FibonacciRange

class DiametricPattern(BasePattern):
    """
    7-leg Diametric pattern (A-B-C-D-E-F-G).
    NEoWave-specific pattern forming diamond or bowtie shape.
    All legs typically subdivide into 3 waves.
    Wave D is often the longest.
    """
    
    def __init__(self):
        super().__init__()
    
    def required_wave_count(self) -> int:
        return 7
    
    def expected_labels(self) -> List[str]:
        return ["A", "B", "C", "D", "E", "F", "G"]
    
    def _initialize_rules(self):
        """Initialize diametric-specific validation rules"""
        
        # MUST rules
        self.rules.append(PatternRule(
            definition=DIAMETRIC_RULES[0],  # seven_legs
            condition=lambda waves: len(waves) == 7
        ))
        
        # SHOULD rules
        self.rules.append(PatternRule(
            definition=DIAMETRIC_RULES[1],  # diamond_shape
            condition=lambda waves: self._check_diamond_shape(waves)
        ))
        
        # PREFER rules
        self.rules.append(PatternRule(
            definition=DIAMETRIC_RULES[2],  # wave_d_longest
            condition=lambda waves: self._is_d_longest(waves)
        ))
        
        self.rules.append(PatternRule(
            definition=DIAMETRIC_RULES[4],  # all_legs_three_waves
            condition=lambda waves: all(self._has_three_wave_structure(w) for w in waves)
        ))
    
    def _has_three_wave_structure(self, wave: Wave) -> bool:
        """Check if wave has 3-wave internal structure"""
        if wave.sub_waves:
            return 2 <= len(wave.sub_waves) <= 4
        return True
    
    def _check_diamond_shape(self, waves: List[Wave]) -> bool:
        """
        Check if pattern forms diamond/bowtie shape.
        Middle waves (C, D, E) should have larger price swings.
        """
        if len(waves) < 7:
            return False
        
        wave_lengths = [abs(w.price_movement) for w in waves]
        
        # Check if middle waves are generally larger
        middle_avg = np.mean([wave_lengths[2], wave_lengths[3], wave_lengths[4]])
        edge_avg = np.mean([wave_lengths[0], wave_lengths[1], wave_lengths[5], wave_lengths[6]])
        
        return middle_avg > edge_avg * 1.1
    
    def _is_d_longest(self, waves: List[Wave]) -> bool:
        """Check if Wave D is the longest"""
        if len(waves) < 7:
            return False
        
        wave_d_length = abs(waves[3].price_movement)
        max_length = max(abs(w.price_movement) for w in waves)
        
        # D should be longest or very close to longest
        return wave_d_length >= max_length * 0.9
    
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate post-diametric thrust targets"""
        waves = wave_count.waves
        
        if len(waves) == 7:
            # Calculate pattern width (max high - min low)
            all_highs = [w.high_price for w in waves]
            all_lows = [w.low_price for w in waves]
            pattern_width = max(all_highs) - min(all_lows)
            
            wave_g_end = waves[6].end_price
            
            # Determine breakout direction (usually continuation)
            direction = 1 if waves[0].price_movement > 0 else -1
            
            # Post-pattern thrust: 0.618-0.786 of pattern width
            wave_count.add_target(
                price=wave_g_end + (pattern_width * 0.618 * direction),
                description="Post-diametric thrust (61.8% of width)",
                probability=0.7
            )
            
            wave_count.add_target(
                price=wave_g_end + (pattern_width * 0.786 * direction),
                description="Post-diametric thrust (78.6% of width)",
                probability=0.6
            )