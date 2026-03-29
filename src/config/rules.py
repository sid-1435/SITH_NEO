from dataclasses import dataclass
from typing import Callable, Tuple, Optional

class Severity:
    """Rule severity levels with associated penalty points"""
    MUST = ("must", 100)      # Absolute requirement - pattern invalid if violated
    SHOULD = ("should", 30)   # Strong preference - significant penalty
    PREFER = ("prefer", 10)   # Mild preference - small penalty
    BONUS = ("bonus", -5)     # Optional enhancement - adds to score

@dataclass
class FibonacciRange:
    """Fibonacci ratio range for validations"""
    min_ratio: float
    max_ratio: float
    
    def contains(self, ratio: float) -> bool:
        return self.min_ratio <= ratio <= self.max_ratio

# Common Fibonacci ranges
FIB_RETRACEMENT_38_78 = FibonacciRange(0.382, 0.786)
FIB_RETRACEMENT_50_78 = FibonacciRange(0.500, 0.786)
FIB_RETRACEMENT_38_62 = FibonacciRange(0.382, 0.618)
FIB_EXTENSION_100_161 = FibonacciRange(1.000, 1.618)
FIB_EXTENSION_161_261 = FibonacciRange(1.618, 2.618)
FIB_EXTENSION_61_161 = FibonacciRange(0.618, 1.618)

@dataclass
class RuleDefinition:
    """Definition of a validation rule"""
    name: str
    severity: Tuple[str, int]  # From Severity class
    description: str
    applies_to: Optional[list] = None  # Which waves this applies to
    fibonacci_range: Optional[FibonacciRange] = None
    exception: Optional[str] = None

# ============================================================================
# IMPULSE PATTERN RULES
# ============================================================================

IMPULSE_RULES = [
    RuleDefinition(
        name="wave3_not_shortest",
        severity=Severity.MUST,
        description="Wave 3 cannot be the shortest motive wave (1, 3, 5)",
        applies_to=[1, 3, 5]
    ),
    
    RuleDefinition(
        name="wave4_no_overlap",
        severity=Severity.MUST,
        description="Wave 4 cannot overlap Wave 1 price territory",
        exception="Allowed in diagonal patterns"
    ),
    
    RuleDefinition(
        name="wave2_retracement",
        severity=Severity.SHOULD,
        description="Wave 2 typically retraces 50-78.6% of Wave 1",
        fibonacci_range=FIB_RETRACEMENT_50_78
    ),
    
    RuleDefinition(
        name="wave3_extension",
        severity=Severity.PREFER,
        description="Wave 3 is often extended (1.618-2.618× Wave 1)",
        fibonacci_range=FIB_EXTENSION_161_261
    ),
    
    RuleDefinition(
        name="wave4_retracement",
        severity=Severity.SHOULD,
        description="Wave 4 typically retraces 38.2-61.8% of Wave 3",
        fibonacci_range=FIB_RETRACEMENT_38_62
    ),
    
    RuleDefinition(
        name="wave5_extension",
        severity=Severity.PREFER,
        description="Wave 5 is typically 0.618-1.618× Wave 1 when not extended",
        fibonacci_range=FIB_EXTENSION_61_161
    ),
    
    RuleDefinition(
        name="alternation",
        severity=Severity.SHOULD,
        description="Waves 2 and 4 should alternate in structure (sharp vs sideways)"
    ),
]

# ============================================================================
# DIAGONAL PATTERN RULES
# ============================================================================

DIAGONAL_RULES = [
    RuleDefinition(
        name="overlap_required",
        severity=Severity.MUST,
        description="Wave 4 must overlap Wave 1 in diagonals"
    ),
    
    RuleDefinition(
        name="converging_lines",
        severity=Severity.SHOULD,
        description="Trendlines connecting wave endpoints should converge"
    ),
    
    RuleDefinition(
        name="all_waves_subdivide",
        severity=Severity.MUST,
        description="All waves must subdivide into 3-wave structures"
    ),
]

# ============================================================================
# ZIGZAG PATTERN RULES
# ============================================================================

ZIGZAG_RULES = [
    RuleDefinition(
        name="wave_b_retracement",
        severity=Severity.SHOULD,
        description="Wave B retraces 38.2-78.6% of Wave A",
        fibonacci_range=FIB_RETRACEMENT_38_78
    ),
    
    RuleDefinition(
        name="wave_c_extension",
        severity=Severity.SHOULD,
        description="Wave C is typically 0.618-1.618× Wave A",
        fibonacci_range=FIB_EXTENSION_61_161
    ),
    
    RuleDefinition(
        name="wave_a_five_waves",
        severity=Severity.PREFER,
        description="Wave A should subdivide into 5 waves"
    ),
    
    RuleDefinition(
        name="wave_b_three_waves",
        severity=Severity.PREFER,
        description="Wave B should subdivide into 3 waves"
    ),
    
    RuleDefinition(
        name="wave_c_five_waves",
        severity=Severity.PREFER,
        description="Wave C should subdivide into 5 waves"
    ),
]

# ============================================================================
# FLAT PATTERN RULES
# ============================================================================

FLAT_RULES = [
    RuleDefinition(
        name="wave_b_retracement",
        severity=Severity.SHOULD,
        description="Wave B retraces 90-140% of Wave A (can exceed 100%)",
        fibonacci_range=FibonacciRange(0.90, 1.40)
    ),
    
    RuleDefinition(
        name="wave_c_termination",
        severity=Severity.SHOULD,
        description="Wave C typically 0.618-1.618× Wave A",
        fibonacci_range=FIB_EXTENSION_61_161
    ),
    
    RuleDefinition(
        name="wave_a_three_waves",
        severity=Severity.PREFER,
        description="Wave A should subdivide into 3 waves"
    ),
    
    RuleDefinition(
        name="wave_b_three_waves",
        severity=Severity.PREFER,
        description="Wave B should subdivide into 3 waves"
    ),
    
    RuleDefinition(
        name="wave_c_five_waves",
        severity=Severity.PREFER,
        description="Wave C should subdivide into 5 waves"
    ),
]

# ============================================================================
# TRIANGLE PATTERN RULES
# ============================================================================

TRIANGLE_RULES = [
    RuleDefinition(
        name="five_legs",
        severity=Severity.MUST,
        description="Triangle must have exactly 5 legs (A-B-C-D-E)"
    ),
    
    RuleDefinition(
        name="all_legs_three_waves",
        severity=Severity.MUST,
        description="All legs must subdivide into 3 waves"
    ),
    
    RuleDefinition(
        name="converging_lines",
        severity=Severity.SHOULD,
        description="Trendlines should converge (for contracting triangle)",
        exception="Expanding triangles have diverging lines"
    ),
    
    RuleDefinition(
        name="wave_e_undershoot",
        severity=Severity.PREFER,
        description="Wave E often undershoots the trendline"
    ),
    
    RuleDefinition(
        name="time_symmetry",
        severity=Severity.SHOULD,
        description="Legs should take similar amounts of time"
    ),
    
    RuleDefinition(
        name="neutral_triangle_c_longest",
        severity=Severity.PREFER,
        description="In neutral triangles (NEoWave), Wave C is longest",
        exception="Specific to neutral triangle subtype"
    ),
]

# ============================================================================
# DIAMETRIC PATTERN RULES
# ============================================================================

DIAMETRIC_RULES = [
    RuleDefinition(
        name="seven_legs",
        severity=Severity.MUST,
        description="Diametric must have exactly 7 legs (A-B-C-D-E-F-G)"
    ),
    
    RuleDefinition(
        name="diamond_shape",
        severity=Severity.SHOULD,
        description="Pattern should form diamond or bowtie shape"
    ),
    
    RuleDefinition(
        name="wave_d_longest",
        severity=Severity.PREFER,
        description="Wave D is often the longest leg"
    ),
    
    RuleDefinition(
        name="post_pattern_thrust",
        severity=Severity.SHOULD,
        description="Post-pattern thrust is 0.618-0.786 of pattern width",
        fibonacci_range=FibonacciRange(0.618, 0.786)
    ),
    
    RuleDefinition(
        name="all_legs_three_waves",
        severity=Severity.PREFER,
        description="All legs should subdivide into 3 waves"
    ),
]

# ============================================================================
# SYMMETRICAL PATTERN RULES
# ============================================================================

SYMMETRICAL_RULES = [
    RuleDefinition(
        name="nine_legs",
        severity=Severity.MUST,
        description="Symmetrical must have exactly 9 legs (A-B-C-D-E-F-G-H-I)"
    ),
    
    RuleDefinition(
        name="leg_symmetry",
        severity=Severity.SHOULD,
        description="Legs should be relatively equal in price and time"
    ),
    
    RuleDefinition(
        name="highest_complexity",
        severity=Severity.PREFER,
        description="Most complex corrective pattern - rare"
    ),
    
    RuleDefinition(
        name="all_legs_three_waves",
        severity=Severity.PREFER,
        description="All legs should subdivide into 3 waves"
    ),
]

# ============================================================================
# TIME-BASED RULES (Apply to all patterns)
# ============================================================================

TIME_RULES = [
    RuleDefinition(
        name="fibonacci_time_ratios",
        severity=Severity.PREFER,
        description="Pattern duration often in Fibonacci ratios (0.618, 1.0, 1.618, 2.618)"
    ),
    
    RuleDefinition(
        name="corrective_wave_equality",
        severity=Severity.SHOULD,
        description="Corrective waves often equal in time (±20% tolerance)"
    ),
    
    RuleDefinition(
        name="extended_wave_time",
        severity=Severity.PREFER,
        description="Extended wave typically takes the most time"
    ),
]

# ============================================================================
# Rule Registry
# ============================================================================

PATTERN_RULES = {
    'impulse': IMPULSE_RULES,
    'leading_diagonal': DIAGONAL_RULES,
    'terminal_impulse': DIAGONAL_RULES,
    'zigzag': ZIGZAG_RULES,
    'flat': FLAT_RULES,
    'triangle': TRIANGLE_RULES,
    'diametric': DIAMETRIC_RULES,
    'symmetrical': SYMMETRICAL_RULES,
}

# Common Fibonacci ratios for quick reference
FIBONACCI_RATIOS = [0.236, 0.382, 0.500, 0.618, 0.786, 1.000, 1.272, 1.618, 2.000, 2.618, 3.618, 4.236]

def get_closest_fibonacci(ratio: float) -> float:
    """Find the closest Fibonacci ratio to the given ratio"""
    return min(FIBONACCI_RATIOS, key=lambda x: abs(x - ratio))

def is_fibonacci_aligned(ratio: float, tolerance: float = 0.1) -> bool:
    """Check if a ratio is close to a Fibonacci number"""
    closest = get_closest_fibonacci(ratio)
    return abs(ratio - closest) / closest <= tolerance