from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class PatternType(Enum):
    MOTIVE = "motive"
    CORRECTIVE = "corrective"
    COMPLEX = "complex"

class WaveStructure(Enum):
    """Internal structure of pattern legs"""
    FIVE = "5"
    THREE = "3"
    FIVE_THREE_FIVE = "5-3-5"
    THREE_THREE_FIVE = "3-3-5"
    THREE_THREE_THREE_THREE_THREE = "3-3-3-3-3"

@dataclass
class PatternConfig:
    """Configuration for a NEoWave pattern"""
    name: str
    pattern_type: PatternType
    leg_count: int
    labels: List[str]
    description: str
    structure: Optional[WaveStructure] = None
    overlap_allowed: bool = False
    subtypes: List[str] = None
    
    def __post_init__(self):
        if self.subtypes is None:
            self.subtypes = []

# ============================================================================
# MOTIVE PATTERNS
# ============================================================================

IMPULSE = PatternConfig(
    name="Impulse",
    pattern_type=PatternType.MOTIVE,
    leg_count=5,
    labels=["1", "2", "3", "4", "5"],
    description="5-wave trending pattern where wave 3 is never the shortest",
    overlap_allowed=False
)

LEADING_DIAGONAL = PatternConfig(
    name="Leading Diagonal",
    pattern_type=PatternType.MOTIVE,
    leg_count=5,
    labels=["1", "2", "3", "4", "5"],
    description="5-wave diagonal at the start of a trend with overlap allowed",
    overlap_allowed=True
)

TERMINAL_IMPULSE = PatternConfig(
    name="Terminal Impulse",
    pattern_type=PatternType.MOTIVE,
    leg_count=5,
    labels=["1", "2", "3", "4", "5"],
    description="Ending diagonal pattern with overlap allowed",
    overlap_allowed=True
)

# ============================================================================
# CORRECTIVE PATTERNS
# ============================================================================

ZIGZAG = PatternConfig(
    name="Zigzag",
    pattern_type=PatternType.CORRECTIVE,
    leg_count=3,
    labels=["A", "B", "C"],
    description="Sharp 5-3-5 correction",
    structure=WaveStructure.FIVE_THREE_FIVE
)

FLAT = PatternConfig(
    name="Flat",
    pattern_type=PatternType.CORRECTIVE,
    leg_count=3,
    labels=["A", "B", "C"],
    description="Sideways 3-3-5 correction",
    structure=WaveStructure.THREE_THREE_FIVE,
    subtypes=["regular", "expanded", "running"]
)

TRIANGLE = PatternConfig(
    name="Triangle",
    pattern_type=PatternType.CORRECTIVE,
    leg_count=5,
    labels=["A", "B", "C", "D", "E"],
    description="Converging 3-3-3-3-3 pattern",
    structure=WaveStructure.THREE_THREE_THREE_THREE_THREE,
    subtypes=["contracting", "expanding", "neutral"]
)

DIAMETRIC = PatternConfig(
    name="Diametric",
    pattern_type=PatternType.CORRECTIVE,
    leg_count=7,
    labels=["A", "B", "C", "D", "E", "F", "G"],
    description="7-leg diamond/bowtie NEoWave pattern"
)

SYMMETRICAL = PatternConfig(
    name="Symmetrical",
    pattern_type=PatternType.CORRECTIVE,
    leg_count=9,
    labels=["A", "B", "C", "D", "E", "F", "G", "H", "I"],
    description="9-leg symmetrical NEoWave pattern"
)

# ============================================================================
# COMPLEX COMBINATIONS
# ============================================================================

DOUBLE_THREE = PatternConfig(
    name="Double Three",
    pattern_type=PatternType.COMPLEX,
    leg_count=3,
    labels=["W", "X", "Y"],
    description="Two corrective patterns linked by a connector wave"
)

TRIPLE_THREE = PatternConfig(
    name="Triple Three",
    pattern_type=PatternType.COMPLEX,
    leg_count=5,
    labels=["W", "X", "Y", "X", "Z"],
    description="Three corrective patterns linked by connector waves"
)

# ============================================================================
# Pattern Registry
# ============================================================================

ALL_PATTERNS = {
    'impulse': IMPULSE,
    'leading_diagonal': LEADING_DIAGONAL,
    'terminal_impulse': TERMINAL_IMPULSE,
    'zigzag': ZIGZAG,
    'flat': FLAT,
    'triangle': TRIANGLE,
    'diametric': DIAMETRIC,
    'symmetrical': SYMMETRICAL,
    'double_three': DOUBLE_THREE,
    'triple_three': TRIPLE_THREE
}

# Categorized access
MOTIVE_PATTERNS = [IMPULSE, LEADING_DIAGONAL, TERMINAL_IMPULSE]
CORRECTIVE_PATTERNS = [ZIGZAG, FLAT, TRIANGLE, DIAMETRIC, SYMMETRICAL]
COMPLEX_PATTERNS = [DOUBLE_THREE, TRIPLE_THREE]