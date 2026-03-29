from typing import List
from .base import BasePattern, PatternRule
from ..core.wave import Wave, WaveCount
from ..config.rules import ZIGZAG_RULES, FIB_RETRACEMENT_38_78, FIB_EXTENSION_61_161

class ZigzagPattern(BasePattern):
    """
    3-wave zigzag correction (5-3-5 structure).
    Sharp corrective pattern.
    Rules:
    - Wave B retraces 38.2-78.6% of Wave A
    - Wave C is typically 0.618-1.618× Wave A
    - Internal structure is 5-3-5
    """
    
    def __init__(self):
        super().__init__()
    
    def required_wave_count(self) -> int:
        return 3
    
    def expected_labels(self) -> List[str]:
        return ["A", "B", "C"]
    
    def _initialize_rules(self):
        """Initialize zigzag-specific validation rules"""
        
        # SHOULD rules
        self.rules.append(PatternRule(
            definition=ZIGZAG_RULES[0],  # wave_b_retracement
            condition=lambda waves: self.fibonacci_check(waves[1], waves[0], FIB_RETRACEMENT_38_78)
        ))
        
        self.rules.append(PatternRule(
            definition=ZIGZAG_RULES[1],  # wave_c_extension
            condition=lambda waves: self.fibonacci_check(waves[2], waves[0], FIB_EXTENSION_61_161)
        ))
        
        # PREFER rules - check internal structure
        # Note: In a full implementation, we'd analyze sub-waves
        # For now, we'll use simplified heuristics
        
        self.rules.append(PatternRule(
            definition=ZIGZAG_RULES[2],  # wave_a_five_waves
            condition=lambda waves: self._has_five_wave_structure(waves[0])
        ))
        
        self.rules.append(PatternRule(
            definition=ZIGZAG_RULES[3],  # wave_b_three_waves
            condition=lambda waves: self._has_three_wave_structure(waves[1])
        ))
        
        self.rules.append(PatternRule(
            definition=ZIGZAG_RULES[4],  # wave_c_five_waves
            condition=lambda waves: self._has_five_wave_structure(waves[2])
        ))
    
    def _has_five_wave_structure(self, wave: Wave) -> bool:
        """
        Simplified check for 5-wave internal structure.
        In full implementation, would recursively analyze sub-waves.
        """
        # Heuristic: if wave has sub_waves and count is close to 5
        if wave.sub_waves:
            return len(wave.sub_waves) >= 4
        # If no sub-wave analysis yet, be lenient
        return True
    
    def _has_three_wave_structure(self, wave: Wave) -> bool:
        """
        Simplified check for 3-wave internal structure.
        """
        if wave.sub_waves:
            return 2 <= len(wave.sub_waves) <= 4
        return True
    
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate projected targets for Wave C completion"""
        waves = wave_count.waves
        
        if len(waves) == 3:
            # Pattern complete - project next move (return to prior trend)
            wave_a_length = abs(waves[0].price_movement)
            wave_c_end = waves[2].end_price
            direction = -1 if waves[0].price_movement > 0 else 1  # Opposite direction
            
            wave_count.add_target(
                price=wave_c_end + (wave_a_length * 0.618 * direction),
                description="61.8% retrace of zigzag",
                probability=0.6
            )
            
            wave_count.add_target(
                price=wave_c_end + (wave_a_length * 1.0 * direction),
                description="100% retrace of zigzag",
                probability=0.8
            )
        
        elif len(waves) == 2:
            # Projecting Wave C
            wave_a_length = abs(waves[0].price_movement)
            wave_b_end = waves[1].end_price
            direction = 1 if waves[0].price_movement > 0 else -1
            
            wave_count.add_target(
                price=wave_b_end + (wave_a_length * 0.618 * direction),
                description="Wave C = 0.618 × Wave A",
                probability=0.6
            )
            
            wave_count.add_target(
                price=wave_b_end + (wave_a_length * 1.0 * direction),
                description="Wave C = 1.0 × Wave A",
                probability=0.8
            )
            
            wave_count.add_target(
                price=wave_b_end + (wave_a_length * 1.618 * direction),
                description="Wave C = 1.618 × Wave A",
                probability=0.5
            )