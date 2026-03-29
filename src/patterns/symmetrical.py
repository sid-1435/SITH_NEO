from typing import List
import numpy as np
from .base import BasePattern, PatternRule
from ..core.wave import Wave, WaveCount
from ..config.rules import SYMMETRICAL_RULES

class SymmetricalPattern(BasePattern):
    """
    9-leg Symmetrical pattern (A-B-C-D-E-F-G-H-I).
    Most complex NEoWave corrective pattern.
    All legs should be relatively equal in price and time.
    All legs typically subdivide into 3 waves.
    """
    
    def __init__(self):
        super().__init__()
    
    def required_wave_count(self) -> int:
        return 9
    
    def expected_labels(self) -> List[str]:
        return ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
    
    def _initialize_rules(self):
        """Initialize symmetrical-specific validation rules"""
        
        # MUST rules
        self.rules.append(PatternRule(
            definition=SYMMETRICAL_RULES[0],  # nine_legs
            condition=lambda waves: len(waves) == 9
        ))
        
        # SHOULD rules
        self.rules.append(PatternRule(
            definition=SYMMETRICAL_RULES[1],  # leg_symmetry
            condition=lambda waves: self._check_symmetry(waves)
        ))
        
        # PREFER rules
        self.rules.append(PatternRule(
            definition=SYMMETRICAL_RULES[3],  # all_legs_three_waves
            condition=lambda waves: all(self._has_three_wave_structure(w) for w in waves)
        ))
    
    def _has_three_wave_structure(self, wave: Wave) -> bool:
        """Check if wave has 3-wave internal structure"""
        if wave.sub_waves:
            return 2 <= len(wave.sub_waves) <= 4
        return True
    
    def _check_symmetry(self, waves: List[Wave]) -> bool:
        """
        Check if legs are relatively equal in price and time.
        """
        if len(waves) < 9:
            return False
        
        # Price symmetry
        price_lengths = [abs(w.price_movement) for w in waves]
        price_avg = np.mean(price_lengths)
        price_std = np.std(price_lengths)
        price_cv = price_std / price_avg if price_avg > 0 else float('inf')
        
        # Time symmetry
        time_durations = [w.time_duration for w in waves]
        time_avg = np.mean(time_durations)
        time_std = np.std(time_durations)
        time_cv = time_std / time_avg if time_avg > 0 else float('inf')
        
        # Coefficient of variation should be low for symmetry (< 0.5)
        return price_cv < 0.5 and time_cv < 0.5
    
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate post-symmetrical pattern targets"""
        waves = wave_count.waves
        
        if len(waves) == 9:
            # Calculate pattern width
            all_highs = [w.high_price for w in waves]
            all_lows = [w.low_price for w in waves]
            pattern_width = max(all_highs) - min(all_lows)
            
            wave_i_end = waves[8].end_price
            
            # Determine breakout direction
            direction = 1 if waves[0].price_movement > 0 else -1
            
            # Post-pattern move typically 0.618 of pattern width
            wave_count.add_target(
                price=wave_i_end + (pattern_width * 0.618 * direction),
                description="Post-symmetrical thrust (61.8% of width)",
                probability=0.6
            )
            
            wave_count.add_target(
                price=wave_i_end + (pattern_width * 1.0 * direction),
                description="Post-symmetrical thrust (100% of width)",
                probability=0.5
            )