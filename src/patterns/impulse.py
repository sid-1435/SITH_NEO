"""
Impulse Pattern Implementation
NEoWave-compliant impulse validation with strict rules.
"""

from typing import List
from .base import BasePattern, PatternRule
from ..core.wave import Wave, WaveCount, WaveType
from ..config.rules import (
    RuleDefinition,
    Severity,
    FIB_RETRACEMENT_50_78, 
    FIB_RETRACEMENT_38_62, 
    FIB_EXTENSION_161_261, 
    FIB_EXTENSION_61_161
)


class ImpulsePattern(BasePattern):
    """
    5-wave impulse pattern - the most common motive wave structure.
    
    CRITICAL RULES:
    1. Wave 2 CANNOT go beyond Wave 1's starting point (origin)
    2. Wave 3 CANNOT be the shortest among waves 1, 3, 5
    3. Wave 4 CANNOT overlap Wave 1 price territory
    4. Wave 4 CANNOT go beyond Wave 3's starting point
    5. Wave 5 should exceed Wave 3 endpoint (truncation is rare)
    
    GUIDELINES:
    - Wave 2 typically retraces 50-78.6% of Wave 1
    - Wave 3 is often extended (1.618-2.618x Wave 1)
    - Wave 4 typically retraces 38.2-61.8% of Wave 3
    - Waves 2 and 4 should alternate in structure
    """
    
    def __init__(self):
        super().__init__()
    
    def required_wave_count(self) -> int:
        return 5
    
    def expected_labels(self) -> List[str]:
        return ["1", "2", "3", "4", "5"]
    
    def _initialize_rules(self):
        """Initialize impulse-specific validation rules"""
        
        # =====================================================================
        # MUST RULES - Pattern INVALID if violated
        # =====================================================================
        
        # Rule 1: Wave 2 cannot go beyond Wave 1's origin (CRITICAL!)
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave2_cannot_exceed_wave1_origin",
                severity=Severity.MUST,
                description="Wave 2 cannot retrace beyond Wave 1's starting point"
            ),
            condition=lambda waves: self._wave2_within_wave1_origin(waves)
        ))
        
        # Rule 2: Wave 3 cannot be the shortest
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave3_not_shortest",
                severity=Severity.MUST,
                description="Wave 3 cannot be the shortest motive wave (1, 3, 5)"
            ),
            condition=lambda waves: not self._is_wave3_shortest(waves)
        ))
        
        # Rule 3: Wave 4 cannot overlap Wave 1
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave4_no_overlap",
                severity=Severity.MUST,
                description="Wave 4 cannot enter Wave 1 price territory"
            ),
            condition=lambda waves: not self._check_wave4_overlaps_wave1(waves)
        ))
        
        # Rule 4: Wave 4 cannot go beyond Wave 3's origin
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave4_cannot_exceed_wave3_origin",
                severity=Severity.MUST,
                description="Wave 4 cannot retrace beyond Wave 3's starting point"
            ),
            condition=lambda waves: self._wave4_within_wave3_origin(waves)
        ))
        
        # Rule 5: Wave 3 must exceed Wave 1 endpoint
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave3_exceeds_wave1",
                severity=Severity.MUST,
                description="Wave 3 must exceed Wave 1 endpoint"
            ),
            condition=lambda waves: self._wave_exceeds_previous(waves, 2, 0)
        ))
        
        # =====================================================================
        # SHOULD RULES - Strong preferences
        # =====================================================================
        
        # Rule 6: Wave 5 should exceed Wave 3 endpoint (truncation is rare)
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave5_exceeds_wave3",
                severity=Severity.SHOULD,
                description="Wave 5 should exceed Wave 3 endpoint (truncation is rare)"
            ),
            condition=lambda waves: self._wave_exceeds_previous(waves, 4, 2)
        ))
        
        # Rule 7: Wave 2 retracement
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave2_retracement",
                severity=Severity.SHOULD,
                description="Wave 2 typically retraces 50-78.6% of Wave 1",
                fibonacci_range=FIB_RETRACEMENT_50_78
            ),
            condition=lambda waves: self.fibonacci_check(waves[1], waves[0], FIB_RETRACEMENT_50_78)
        ))
        
        # Rule 8: Wave 4 retracement
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave4_retracement",
                severity=Severity.SHOULD,
                description="Wave 4 typically retraces 38.2-61.8% of Wave 3",
                fibonacci_range=FIB_RETRACEMENT_38_62
            ),
            condition=lambda waves: self.fibonacci_check(waves[3], waves[2], FIB_RETRACEMENT_38_62)
        ))
        
        # Rule 9: Alternation between waves 2 and 4
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="alternation",
                severity=Severity.SHOULD,
                description="Waves 2 and 4 should alternate in structure (sharp vs sideways)"
            ),
            condition=lambda waves: self._check_alternation(waves[1], waves[3])
        ))
        
        # =====================================================================
        # PREFER RULES - Mild preferences
        # =====================================================================
        
        # Rule 10: Wave 3 extension
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave3_extension",
                severity=Severity.PREFER,
                description="Wave 3 is often extended (1.618-2.618× Wave 1)",
                fibonacci_range=FIB_EXTENSION_161_261
            ),
            condition=lambda waves: self.fibonacci_check(waves[2], waves[0], FIB_EXTENSION_161_261)
        ))
        
        # Rule 11: Wave 5 typical length
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave5_typical_length",
                severity=Severity.PREFER,
                description="Wave 5 is typically 0.618-1.618× Wave 1",
                fibonacci_range=FIB_EXTENSION_61_161
            ),
            condition=lambda waves: self.fibonacci_check(waves[4], waves[0], FIB_EXTENSION_61_161)
        ))
    
    # =========================================================================
    # CRITICAL RULE CHECK METHODS
    # =========================================================================
    
    def _wave2_within_wave1_origin(self, waves: List[Wave]) -> bool:
        """
        CRITICAL: Wave 2 cannot go beyond Wave 1's starting point.
        
        In an uptrend:
        - Wave 1 goes UP from start_price to end_price
        - Wave 2 retraces DOWN but CANNOT go below Wave 1's start_price
        
        In a downtrend:
        - Wave 1 goes DOWN from start_price to end_price
        - Wave 2 retraces UP but CANNOT go above Wave 1's start_price
        """
        if len(waves) < 2:
            return True
        
        wave1 = waves[0]
        wave2 = waves[1]
        
        wave1_origin = wave1.start_price
        
        if wave1_origin is None or wave2.end_price is None:
            return True
        
        is_uptrend = self._is_uptrend(waves)
        
        if is_uptrend:
            # Wave 2's lowest point cannot go below Wave 1's start
            wave2_extreme = wave2.low_price if wave2.low_price else wave2.end_price
            return wave2_extreme >= wave1_origin
        else:
            # Wave 2's highest point cannot go above Wave 1's start
            wave2_extreme = wave2.high_price if wave2.high_price else wave2.end_price
            return wave2_extreme <= wave1_origin
    
    def _wave4_within_wave3_origin(self, waves: List[Wave]) -> bool:
        """
        CRITICAL: Wave 4 cannot go beyond Wave 3's starting point.
        """
        if len(waves) < 4:
            return True
        
        wave3 = waves[2]
        wave4 = waves[3]
        
        wave3_origin = wave3.start_price
        
        if wave3_origin is None or wave4.end_price is None:
            return True
        
        is_uptrend = self._is_uptrend(waves)
        
        if is_uptrend:
            wave4_extreme = wave4.low_price if wave4.low_price else wave4.end_price
            return wave4_extreme >= wave3_origin
        else:
            wave4_extreme = wave4.high_price if wave4.high_price else wave4.end_price
            return wave4_extreme <= wave3_origin
    
    def _is_wave3_shortest(self, waves: List[Wave]) -> bool:
        """Check if Wave 3 is the shortest among motive waves"""
        if len(waves) < 5:
            return False
        
        try:
            w1_length = abs(waves[0].price_movement) if waves[0].price_movement else 0
            w3_length = abs(waves[2].price_movement) if waves[2].price_movement else 0
            w5_length = abs(waves[4].price_movement) if waves[4].price_movement else 0
            
            return w3_length < w1_length and w3_length < w5_length
        except:
            return False
    
    def _check_wave4_overlaps_wave1(self, waves: List[Wave]) -> bool:
        """Check if Wave 4 overlaps Wave 1 (NOT allowed in impulse)"""
        if len(waves) < 4:
            return False
        
        try:
            wave1 = waves[0]
            wave4 = waves[3]
            
            w1_high = wave1.high_price or max(wave1.start_price or 0, wave1.end_price or 0)
            w1_low = wave1.low_price or min(wave1.start_price or float('inf'), wave1.end_price or float('inf'))
            
            w4_high = wave4.high_price or max(wave4.start_price or 0, wave4.end_price or 0)
            w4_low = wave4.low_price or min(wave4.start_price or float('inf'), wave4.end_price or float('inf'))
            
            is_uptrend = self._is_uptrend(waves)
            
            if is_uptrend:
                # In uptrend, Wave 4 low should not go into Wave 1's high
                return w4_low < w1_high
            else:
                # In downtrend, Wave 4 high should not go into Wave 1's low
                return w4_high > w1_low
        except:
            return False
    
    def _wave_exceeds_previous(self, waves: List[Wave], current_idx: int, previous_idx: int) -> bool:
        """Check if current wave exceeds previous wave's endpoint"""
        if len(waves) <= max(current_idx, previous_idx):
            return True
        
        try:
            current = waves[current_idx]
            previous = waves[previous_idx]
            
            if current.end_price is None or previous.end_price is None:
                return True
            
            is_uptrend = self._is_uptrend(waves)
            
            if is_uptrend:
                return current.end_price > previous.end_price
            else:
                return current.end_price < previous.end_price
        except:
            return True
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _is_uptrend(self, waves: List[Wave]) -> bool:
        """Determine if the impulse is in an uptrend or downtrend"""
        if not waves:
            return True
        
        wave1 = waves[0]
        if wave1.start_price is None or wave1.end_price is None:
            return True
        
        return wave1.end_price > wave1.start_price
    
    def _check_alternation(self, wave2: Wave, wave4: Wave) -> bool:
        """
        Check if waves 2 and 4 alternate in structure.
        Simple heuristic: they should differ significantly in time or depth.
        """
        try:
            w2_duration = wave2.time_duration if hasattr(wave2, 'time_duration') and wave2.time_duration else 1
            w4_duration = wave4.time_duration if hasattr(wave4, 'time_duration') and wave4.time_duration else 1
            
            time_ratio = w2_duration / w4_duration if w4_duration > 0 else 1
            
            # Consider alternating if time ratio is significantly different from 1:1
            return time_ratio < 0.6 or time_ratio > 1.6
        except:
            return True
    
    # =========================================================================
    # TARGET CALCULATION
    # =========================================================================
    
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate projected targets"""
        waves = wave_count.waves
        
        if len(waves) == 5:
            # Impulse complete - project correction targets
            try:
                total_impulse = abs(waves[4].end_price - waves[0].start_price)
                wave_5_end = waves[4].end_price
                direction = -1 if self._is_uptrend(waves) else 1
                
                wave_count.add_target(
                    price=wave_5_end + (total_impulse * 0.382 * direction),
                    description="38.2% retracement of impulse",
                    probability=0.7
                )
                
                wave_count.add_target(
                    price=wave_5_end + (total_impulse * 0.5 * direction),
                    description="50% retracement of impulse",
                    probability=0.6
                )
                
                wave_count.add_target(
                    price=wave_5_end + (total_impulse * 0.618 * direction),
                    description="61.8% retracement of impulse",
                    probability=0.5
                )
            except:
                pass
        
        elif len(waves) == 4:
            # Projecting Wave 5
            try:
                wave_1_length = abs(waves[0].price_movement)
                wave_3_end = waves[2].end_price
                wave_4_end = waves[3].end_price
                direction = 1 if self._is_uptrend(waves) else -1
                
                # Minimum: Wave 5 must exceed Wave 3
                wave_count.add_target(
                    price=wave_3_end + (wave_1_length * 0.05 * direction),
                    description="Minimum Wave 5 (just beyond Wave 3)",
                    probability=0.95
                )
                
                wave_count.add_target(
                    price=wave_4_end + (wave_1_length * 0.618 * direction),
                    description="Wave 5 = 0.618 × Wave 1",
                    probability=0.6
                )
                
                wave_count.add_target(
                    price=wave_4_end + (wave_1_length * 1.0 * direction),
                    description="Wave 5 = Wave 1 (equality)",
                    probability=0.7
                )
                
                wave_count.add_target(
                    price=wave_4_end + (wave_1_length * 1.618 * direction),
                    description="Wave 5 = 1.618 × Wave 1 (extended)",
                    probability=0.4
                )
            except:
                pass