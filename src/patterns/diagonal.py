"""
Diagonal Pattern Implementation (Leading and Terminal)
NEoWave-compliant diagonal validation with strict rules.
"""

from typing import List
from .base import BasePattern, PatternRule
from ..core.wave import Wave, WaveCount
from ..config.rules import (
    RuleDefinition, 
    Severity, 
    FibonacciRange,
    FIB_RETRACEMENT_50_78,
    FIB_RETRACEMENT_38_62
)


class DiagonalPattern(BasePattern):
    """
    5-wave diagonal pattern (Leading or Terminal).
    
    CRITICAL RULES:
    1. Wave 2 CANNOT go beyond Wave 1's origin (starting point)
    2. Wave 4 CANNOT go beyond Wave 3's origin
    3. Wave 4 MUST overlap Wave 1 (key diagonal characteristic)
    4. Wave 5 MUST exceed Wave 3 endpoint
    5. Wave 3 MUST exceed Wave 1 endpoint
    6. All waves subdivide into 3 waves (3-3-3-3-3)
    7. Trendlines should converge
    8. Wave 5 typically shorter than Wave 3
    9. Wave 3 typically shorter than Wave 1 (contracting diagonal)
    """
    
    def __init__(self, is_leading: bool = True):
        self.is_leading = is_leading
        super().__init__()
    
    def required_wave_count(self) -> int:
        return 5
    
    def expected_labels(self) -> List[str]:
        return ["1", "2", "3", "4", "5"]
    
    def _initialize_rules(self):
        """Initialize diagonal-specific validation rules"""
        
        # =====================================================================
        # MUST RULES - Pattern INVALID if violated
        # =====================================================================
        
        # Rule 1: Wave 2 cannot go beyond Wave 1's origin (CRITICAL!)
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave2_cannot_exceed_wave1_origin",
                severity=Severity.MUST,
                description="Wave 2 cannot retrace beyond Wave 1's starting point (origin)"
            ),
            condition=lambda waves: self._wave2_within_wave1_origin(waves)
        ))
        
        # Rule 2: Wave 4 cannot go beyond Wave 3's origin
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave4_cannot_exceed_wave3_origin",
                severity=Severity.MUST,
                description="Wave 4 cannot retrace beyond Wave 3's starting point (origin)"
            ),
            condition=lambda waves: self._wave4_within_wave3_origin(waves)
        ))
        
        # Rule 3: Wave 4 must overlap Wave 1 (key diagonal characteristic)
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave4_overlaps_wave1",
                severity=Severity.MUST,
                description="Wave 4 must overlap Wave 1 price territory (defining diagonal characteristic)"
            ),
            condition=lambda waves: self._check_wave4_overlaps_wave1(waves)
        ))
        
        # Rule 4: Wave 5 must exceed Wave 3 endpoint (NO TRUNCATION in diagonals)
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave5_exceeds_wave3",
                severity=Severity.MUST,
                description="Wave 5 must exceed Wave 3 endpoint (truncation not allowed in diagonals)"
            ),
            condition=lambda waves: self._wave5_exceeds_wave3(waves)
        ))
        
        # Rule 5: Wave 3 must exceed Wave 1 endpoint
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave3_exceeds_wave1",
                severity=Severity.MUST,
                description="Wave 3 must exceed Wave 1 endpoint"
            ),
            condition=lambda waves: self._wave3_exceeds_wave1(waves)
        ))
        
        # Rule 6: All waves must subdivide into 3-wave structures
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="all_waves_three_wave_structure",
                severity=Severity.SHOULD,
                description="All waves in a diagonal should subdivide into 3 waves"
            ),
            condition=lambda waves: all(self._has_three_wave_structure(w) for w in waves)
        ))
        
        # =====================================================================
        # SHOULD RULES - Strong preferences
        # =====================================================================
        
        # Rule 7: Trendlines should converge
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="converging_trendlines",
                severity=Severity.SHOULD,
                description="Trendlines connecting 1-3-5 and 2-4 should converge"
            ),
            condition=lambda waves: self._check_converging_lines(waves)
        ))
        
        # Rule 8: Wave 5 typically shorter than Wave 3
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave5_shorter_than_wave3",
                severity=Severity.SHOULD,
                description="Wave 5 is typically shorter than Wave 3 in diagonals"
            ),
            condition=lambda waves: self._wave5_shorter_than_wave3(waves)
        ))
        
        # Rule 9: Wave 3 typically shorter than Wave 1
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="wave3_shorter_than_wave1",
                severity=Severity.SHOULD,
                description="Wave 3 is typically shorter than Wave 1 in contracting diagonals"
            ),
            condition=lambda waves: self._wave3_shorter_than_wave1(waves)
        ))
        
        # =====================================================================
        # PREFER RULES - Mild preferences
        # =====================================================================
        
        # Rule 10: Waves get progressively smaller (contracting)
        self.rules.append(PatternRule(
            definition=RuleDefinition(
                name="progressive_contraction",
                severity=Severity.PREFER,
                description="Motive waves (1, 3, 5) should get progressively smaller"
            ),
            condition=lambda waves: self._check_progressive_contraction(waves)
        ))
    
    # =========================================================================
    # CRITICAL RULE CHECK METHODS
    # =========================================================================
    
    def _wave2_within_wave1_origin(self, waves: List[Wave]) -> bool:
        """
        CRITICAL: Wave 2 cannot go beyond Wave 1's starting point.
        
        In an uptrend diagonal:
        - Wave 1 goes UP from start_price to end_price
        - Wave 2 retraces DOWN but CANNOT go below Wave 1's start_price
        
        In a downtrend diagonal:
        - Wave 1 goes DOWN from start_price to end_price
        - Wave 2 retraces UP but CANNOT go above Wave 1's start_price
        """
        if len(waves) < 2:
            return True
        
        wave1 = waves[0]
        wave2 = waves[1]
        
        # Get Wave 1's origin (starting point)
        wave1_origin = wave1.start_price
        
        if wave1_origin is None or wave2.end_price is None:
            return True  # Can't validate
        
        # Determine trend direction
        is_uptrend = self._is_uptrend(waves)
        
        if is_uptrend:
            # In uptrend: Wave 2 low cannot go below Wave 1 start
            wave2_extreme = wave2.low_price if wave2.low_price else wave2.end_price
            return wave2_extreme >= wave1_origin
        else:
            # In downtrend: Wave 2 high cannot go above Wave 1 start
            wave2_extreme = wave2.high_price if wave2.high_price else wave2.end_price
            return wave2_extreme <= wave1_origin
    
    def _wave4_within_wave3_origin(self, waves: List[Wave]) -> bool:
        """
        CRITICAL: Wave 4 cannot go beyond Wave 3's starting point.
        
        Similar logic to Wave 2/Wave 1 relationship.
        """
        if len(waves) < 4:
            return True
        
        wave3 = waves[2]
        wave4 = waves[3]
        
        # Get Wave 3's origin (starting point)
        wave3_origin = wave3.start_price
        
        if wave3_origin is None or wave4.end_price is None:
            return True  # Can't validate
        
        # Determine trend direction
        is_uptrend = self._is_uptrend(waves)
        
        if is_uptrend:
            # In uptrend: Wave 4 low cannot go below Wave 3 start
            wave4_extreme = wave4.low_price if wave4.low_price else wave4.end_price
            return wave4_extreme >= wave3_origin
        else:
            # In downtrend: Wave 4 high cannot go above Wave 3 start
            wave4_extreme = wave4.high_price if wave4.high_price else wave4.end_price
            return wave4_extreme <= wave3_origin
    
    def _check_wave4_overlaps_wave1(self, waves: List[Wave]) -> bool:
        """
        Check if Wave 4 overlaps Wave 1.
        This is a REQUIRED characteristic of diagonals (unlike impulses).
        
        Overlap means Wave 4's price range enters Wave 1's price range.
        """
        if len(waves) < 4:
            return False
        
        wave1 = waves[0]
        wave4 = waves[3]
        
        # Get price ranges
        w1_high = wave1.high_price or max(wave1.start_price or 0, wave1.end_price or 0)
        w1_low = wave1.low_price or min(wave1.start_price or float('inf'), wave1.end_price or float('inf'))
        
        w4_high = wave4.high_price or max(wave4.start_price or 0, wave4.end_price or 0)
        w4_low = wave4.low_price or min(wave4.start_price or float('inf'), wave4.end_price or float('inf'))
        
        # Check if ranges overlap
        # Overlap exists if: NOT (w4_low > w1_high OR w4_high < w1_low)
        return not (w4_low > w1_high or w4_high < w1_low)
    
    def _wave5_exceeds_wave3(self, waves: List[Wave]) -> bool:
        """
        Check if Wave 5 exceeds Wave 3's endpoint.
        CRITICAL: Truncation is NOT allowed in diagonals.
        """
        if len(waves) < 5:
            return True  # Can't validate yet
        
        wave3 = waves[2]
        wave5 = waves[4]
        
        if wave3.end_price is None or wave5.end_price is None:
            return True
        
        is_uptrend = self._is_uptrend(waves)
        
        if is_uptrend:
            # Wave 5 end must be HIGHER than Wave 3 end
            return wave5.end_price > wave3.end_price
        else:
            # Wave 5 end must be LOWER than Wave 3 end
            return wave5.end_price < wave3.end_price
    
    def _wave3_exceeds_wave1(self, waves: List[Wave]) -> bool:
        """
        Check if Wave 3 exceeds Wave 1's endpoint.
        """
        if len(waves) < 3:
            return True
        
        wave1 = waves[0]
        wave3 = waves[2]
        
        if wave1.end_price is None or wave3.end_price is None:
            return True
        
        is_uptrend = self._is_uptrend(waves)
        
        if is_uptrend:
            return wave3.end_price > wave1.end_price
        else:
            return wave3.end_price < wave1.end_price
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _is_uptrend(self, waves: List[Wave]) -> bool:
        """Determine if the diagonal is in an uptrend or downtrend"""
        if not waves:
            return True
        
        wave1 = waves[0]
        if wave1.start_price is None or wave1.end_price is None:
            return True
        
        return wave1.end_price > wave1.start_price
    
    def _has_three_wave_structure(self, wave: Wave) -> bool:
        """Check if wave has 3-wave internal structure"""
        if hasattr(wave, 'sub_waves') and wave.sub_waves:
            return 2 <= len(wave.sub_waves) <= 4
        return True  # Assume OK if no sub-wave data
    
    def _check_converging_lines(self, waves: List[Wave]) -> bool:
        """
        Check if trendlines converge.
        Upper line: connects Wave 1 end, Wave 3 end, Wave 5 end
        Lower line: connects Wave 2 end, Wave 4 end
        In contracting diagonal, these should converge.
        """
        if len(waves) < 5:
            return True
        
        try:
            w1_length = abs(waves[0].price_movement) if waves[0].price_movement else 0
            w3_length = abs(waves[2].price_movement) if waves[2].price_movement else 0
            w5_length = abs(waves[4].price_movement) if waves[4].price_movement else 0
            
            # In a converging diagonal, waves should get smaller
            # Allow 20% tolerance
            return w5_length <= w3_length * 1.2 and w3_length <= w1_length * 1.2
        except:
            return True
    
    def _wave5_shorter_than_wave3(self, waves: List[Wave]) -> bool:
        """Check if Wave 5 is shorter than Wave 3"""
        if len(waves) < 5:
            return True
        
        try:
            w3_length = abs(waves[2].price_movement) if waves[2].price_movement else 0
            w5_length = abs(waves[4].price_movement) if waves[4].price_movement else 0
            
            # Allow 10% tolerance
            return w5_length <= w3_length * 1.1
        except:
            return True
    
    def _wave3_shorter_than_wave1(self, waves: List[Wave]) -> bool:
        """Check if Wave 3 is shorter than Wave 1"""
        if len(waves) < 3:
            return True
        
        try:
            w1_length = abs(waves[0].price_movement) if waves[0].price_movement else 0
            w3_length = abs(waves[2].price_movement) if waves[2].price_movement else 0
            
            # Allow 10% tolerance
            return w3_length <= w1_length * 1.1
        except:
            return True
    
    def _check_progressive_contraction(self, waves: List[Wave]) -> bool:
        """
        Check if motive waves (1, 3, 5) get progressively smaller.
        """
        if len(waves) < 5:
            return True
        
        try:
            w1_length = abs(waves[0].price_movement) if waves[0].price_movement else 0
            w3_length = abs(waves[2].price_movement) if waves[2].price_movement else 0
            w5_length = abs(waves[4].price_movement) if waves[4].price_movement else 0
            
            # Each successive motive wave should be smaller (with 15% tolerance)
            return w3_length <= w1_length * 1.15 and w5_length <= w3_length * 1.15
        except:
            return True
    
    # =========================================================================
    # TARGET CALCULATION
    # =========================================================================
    
    def _calculate_targets(self, wave_count: WaveCount):
        """Calculate targets for diagonal completion"""
        waves = wave_count.waves
        
        if len(waves) == 5:
            # Diagonal complete - expect sharp reversal
            try:
                total_diagonal = abs(waves[4].end_price - waves[0].start_price)
                wave_5_end = waves[4].end_price
                
                # Reverse direction after diagonal
                direction = -1 if self._is_uptrend(waves) else 1
                
                wave_count.add_target(
                    price=wave_5_end + (total_diagonal * 0.618 * direction),
                    description="61.8% retrace of diagonal (common)",
                    probability=0.7
                )
                
                wave_count.add_target(
                    price=wave_5_end + (total_diagonal * 1.0 * direction),
                    description="100% retrace of diagonal (strong reversal)",
                    probability=0.5
                )
                
                wave_count.add_target(
                    price=wave_5_end + (total_diagonal * 1.618 * direction),
                    description="161.8% extension (very strong reversal)",
                    probability=0.3
                )
            except:
                pass
        
        elif len(waves) == 4:
            # Projecting Wave 5
            try:
                wave_1_length = abs(waves[0].price_movement)
                wave_3_length = abs(waves[2].price_movement)
                wave_4_end = waves[3].end_price
                direction = 1 if self._is_uptrend(waves) else -1
                
                # Wave 5 must exceed Wave 3 end - this is minimum target
                wave_3_end = waves[2].end_price
                min_target = wave_3_end + (wave_3_length * 0.01 * direction)  # Just beyond Wave 3
                
                wave_count.add_target(
                    price=min_target,
                    description="Minimum Wave 5 (just beyond Wave 3 - required)",
                    probability=0.95
                )
                
                # Wave 5 typically shorter than Wave 3 in diagonals
                wave_count.add_target(
                    price=wave_4_end + (wave_3_length * 0.618 * direction),
                    description="Wave 5 = 61.8% × Wave 3",
                    probability=0.7
                )
                
                wave_count.add_target(
                    price=wave_4_end + (wave_1_length * 0.618 * direction),
                    description="Wave 5 = 61.8% × Wave 1",
                    probability=0.6
                )
            except:
                pass


class LeadingDiagonalPattern(DiagonalPattern):
    """Leading Diagonal - appears at the start of a trend (Wave 1 or Wave A position)"""
    
    def __init__(self):
        super().__init__(is_leading=True)
        self.name = "Leading Diagonal"


class TerminalDiagonalPattern(DiagonalPattern):
    """Terminal/Ending Diagonal - appears at the end of a trend (Wave 5 or Wave C position)"""
    
    def __init__(self):
        super().__init__(is_leading=False)
        self.name = "Terminal Diagonal"