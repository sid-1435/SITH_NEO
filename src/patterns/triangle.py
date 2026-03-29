from typing import List
import numpy as np
from .base import BasePattern, PatternRule
from ..core.wave import Wave, WaveCount
from ..config.rules import TRIANGLE_RULES

class TrianglePattern(BasePattern):
    """
    5-wave triangle pattern (A-B-C-D-E).
    All legs subdivide into 3 waves (3-3-3-3-3).
    Subtypes: Contracting, Expanding, Neutral (NEoWave specific)
    """
    
    def __init__(self):
        super().__init__()
    
    def required_wave_count(self) -> int:
        return 5
    
    def expected_labels(self) -> List[str]:
        return ["A", "B", "C", "D", "E"]
    
    def _initialize_rules(self):
        """Initialize triangle-specific validation rules"""
        
        # MUST rules
        self.rules.append(PatternRule(
            definition=TRIANGLE_RULES[0],  # five_legs
            condition=lambda waves: len(waves) == 5
        ))
        
        self.rules.append(PatternRule(
            definition=TRIANGLE_RULES[1],  # all_legs_three_waves
            condition=lambda waves: all(self._has_three_wave_structure(w) for w in waves)
        ))
        
        # SHOULD rules
        self.rules.append(PatternRule(
            definition=TRIANGLE_RULES[2],  # converging_lines
            condition=lambda waves: self._check_converging_lines(waves)
        ))
        
        self.rules.append(PatternRule(
            definition=TRIANGLE_RULES[4],  # time_symmetry
            condition=lambda waves: self._check_time_symmetry(waves)
        ))
        
        # PREFER rules
        self.rules.append(PatternRule(
            definition=TRIANGLE_RULES[3],  # wave_e_undershoot
            condition=lambda waves: self._check_e_wave_undershoot(waves)
        ))
    
    def _has_three_wave_structure(self, wave: Wave) -> bool:
        """Check if wave has 3-wave internal structure"""
        if wave.sub_waves:
            return 2 <= len(wave.sub_waves) <= 4
        return True
    
    def _check_converging_lines(self, waves: List[Wave]) -> bool:
        """
        Check if trendlines converge.
        Connect highs (A, C, E) and lows (B, D) and check if they converge.
        """
        if len(waves) < 5:
            return False
        
        # Get high points and low points
        high_prices = [waves[0].high_price, waves[2].high_price, waves[4].high_price]
        low_prices = [waves[1].low_price, waves[3].low_price]
        
        # Calculate simple convergence check
        high_range = max(high_prices) - min(high_prices)
        low_range = max(low_prices) - min(low_prices)
        
        # Lines are converging if ranges are decreasing
        return high_range > low_range * 0.5  # Simplified check
    
    def _check_time_symmetry(self, waves: List[Wave]) -> bool:
        """Check if legs take similar amounts of time"""
        if len(waves) < 5:
            return False
        
        durations = [w.time_duration for w in waves]
        avg_duration = np.mean(durations)
        
        # Check if all durations are within 50% of average
        return all(0.5 * avg_duration <= d <= 1.5 * avg_duration for d in durations)
    
    def _check_e_wave_undershoot(self, waves: List[Wave]) -> bool:
        """Check if Wave E undershoots the trendline"""
        if len(waves) < 5:
            return False
        
        # Simplified: E should be smaller than C
        return abs(waves[4].price_movement) < abs(waves[2].price_movement)
    
    def determine_subtype(self, waves: List[Wave]) -> str:
        """
        Determine triangle subtype.
        - Contracting: Lines converge, successive waves get smaller
        - Expanding: Lines diverge, successive waves get larger
        - Neutral: Wave C is longest (NEoWave specific)
        """
        if len(waves) < 5:
            return "unknown"
        
        wave_lengths = [abs(w.price_movement) for w in waves]
        
        # Check if C is longest (Neutral triangle)
        if wave_lengths[2] == max(wave_lengths):
            return "neutral"
        
        # Check if waves are generally decreasing (Contracting)
        if wave_lengths[4] < wave_lengths[0] * 0.8:
            return "contracting"
        
        # Check if waves are generally increasing (Expanding)
        if wave_lengths[4] > wave_lengths[0] * 1.2:
            return "expanding"
        
        return "contracting"  # Default
    
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate post-triangle thrust targets"""
        waves = wave_count.waves
        
        if len(waves) == 5:
            # Determine subtype
            subtype = self.determine_subtype(waves)
            wave_count.description += f" ({subtype})"
            
            # Calculate triangle width (A to C range)
            triangle_width = abs(waves[0].high_price - waves[2].low_price)
            wave_e_end = waves[4].end_price
            
            # Direction of breakout (continuation of prior trend)
            direction = 1 if waves[0].price_movement > 0 else -1
            
            # Post-triangle thrust is typically 0.618-0.786 of widest part
            wave_count.add_target(
                price=wave_e_end + (triangle_width * 0.618 * direction),
                description="Post-triangle thrust (61.8% of width)",
                probability=0.7
            )
            
            wave_count.add_target(
                price=wave_e_end + (triangle_width * 0.786 * direction),
                description="Post-triangle thrust (78.6% of width)",
                probability=0.6
            )