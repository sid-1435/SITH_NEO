from typing import List
from .base import BasePattern, PatternRule
from ..core.wave import Wave, WaveCount
from ..config.rules import FLAT_RULES, FibonacciRange, FIB_EXTENSION_61_161

class FlatPattern(BasePattern):
    """
    3-wave flat correction (3-3-5 structure).
    Sideways corrective pattern.
    Rules:
    - Wave B retraces 90-140% of Wave A (can exceed 100%)
    - Wave C typically 0.618-1.618× Wave A
    - Internal structure is 3-3-5
    Subtypes: Regular, Expanded, Running
    """
    
    def __init__(self):
        super().__init__()
    
    def required_wave_count(self) -> int:
        return 3
    
    def expected_labels(self) -> List[str]:
        return ["A", "B", "C"]
    
    def _initialize_rules(self):
        """Initialize flat-specific validation rules"""
        
        # SHOULD rules
        self.rules.append(PatternRule(
            definition=FLAT_RULES[0],  # wave_b_retracement
            condition=lambda waves: self.fibonacci_check(
                waves[1], waves[0], 
                FibonacciRange(0.90, 1.40)
            )
        ))
        
        self.rules.append(PatternRule(
            definition=FLAT_RULES[1],  # wave_c_termination
            condition=lambda waves: self.fibonacci_check(waves[2], waves[0], FIB_EXTENSION_61_161)
        ))
        
        # PREFER rules - internal structure
        self.rules.append(PatternRule(
            definition=FLAT_RULES[2],  # wave_a_three_waves
            condition=lambda waves: self._has_three_wave_structure(waves[0])
        ))
        
        self.rules.append(PatternRule(
            definition=FLAT_RULES[3],  # wave_b_three_waves
            condition=lambda waves: self._has_three_wave_structure(waves[1])
        ))
        
        self.rules.append(PatternRule(
            definition=FLAT_RULES[4],  # wave_c_five_waves
            condition=lambda waves: self._has_five_wave_structure(waves[2])
        ))
    
    def _has_three_wave_structure(self, wave: Wave) -> bool:
        """Check for 3-wave structure"""
        if wave.sub_waves:
            return 2 <= len(wave.sub_waves) <= 4
        return True
    
    def _has_five_wave_structure(self, wave: Wave) -> bool:
        """Check for 5-wave structure"""
        if wave.sub_waves:
            return len(wave.sub_waves) >= 4
        return True
    
    def determine_subtype(self, waves: List[Wave]) -> str:
        """
        Determine flat subtype based on wave relationships.
        - Regular: B ≈ A, C ≈ A
        - Expanded: B > A, C > A
        - Running: B > A, C < A
        """
        if len(waves) < 3:
            return "unknown"
        
        wave_a_length = abs(waves[0].price_movement)
        wave_b_length = abs(waves[1].price_movement)
        wave_c_length = abs(waves[2].price_movement)
        
        b_ratio = wave_b_length / wave_a_length if wave_a_length > 0 else 0
        c_ratio = wave_c_length / wave_a_length if wave_a_length > 0 else 0
        
        if b_ratio > 1.05 and c_ratio > 1.05:
            return "expanded"
        elif b_ratio > 1.05 and c_ratio < 0.95:
            return "running"
        else:
            return "regular"
    
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate projected targets"""
        waves = wave_count.waves
        
        if len(waves) == 3:
            # Determine subtype
            subtype = self.determine_subtype(waves)
            wave_count.description += f" ({subtype})"
            
            # Pattern complete - project reversal
            wave_a_length = abs(waves[0].price_movement)
            wave_c_end = waves[2].end_price
            direction = -1 if waves[0].price_movement > 0 else 1
            
            wave_count.add_target(
                price=wave_c_end + (wave_a_length * 0.618 * direction),
                description="61.8% retrace of flat",
                probability=0.6
            )
            
            wave_count.add_target(
                price=wave_c_end + (wave_a_length * 1.0 * direction),
                description="100% retrace of flat",
                probability=0.7
            )
        
        elif len(waves) == 2:
            # Projecting Wave C
            wave_a_length = abs(waves[0].price_movement)
            wave_b_end = waves[1].end_price
            direction = 1 if waves[0].price_movement > 0 else -1
            
            wave_count.add_target(
                price=wave_b_end + (wave_a_length * 0.618 * direction),
                description="Wave C = 0.618 × Wave A",
                probability=0.5
            )
            
            wave_count.add_target(
                price=wave_b_end + (wave_a_length * 1.0 * direction),
                description="Wave C = 1.0 × Wave A",
                probability=0.7
            )
            
            wave_count.add_target(
                price=wave_b_end + (wave_a_length * 1.272 * direction),
                description="Wave C = 1.272 × Wave A",
                probability=0.6
            )