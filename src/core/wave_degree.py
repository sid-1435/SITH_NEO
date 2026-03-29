"""
Wave Degree Configuration and Hierarchical Wave Structures
Supports multi-degree wave analysis per NEoWave methodology.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class WaveDegree(Enum):
    """
    Wave degree hierarchy from largest to smallest.
    Each degree contains waves of the next smaller degree.
    """
    SUPERCYCLE = 0      # Multi-year waves
    CYCLE = 1           # Yearly waves
    PRIMARY = 2         # Monthly waves
    INTERMEDIATE = 3    # Weekly waves
    MINOR = 4           # Daily waves
    MINUTE = 5          # Hourly waves
    MINUETTE = 6        # 15-minute waves
    SUBMINUETTE = 7     # 5-minute waves


class WaveType(Enum):
    """Type of wave movement"""
    MOTIVE = "motive"
    CORRECTIVE = "corrective"


@dataclass
class DegreeConfig:
    """Configuration for each wave degree level"""
    degree: WaveDegree
    name: str
    
    # Pivot detection parameters
    lookback: int
    lookahead: int
    min_price_move_pct: float
    
    # Labels for wave marking
    labels_motive: List[str]
    labels_corrective: List[str]
    
    # Visualization settings
    line_width: int
    line_dash: str  # 'solid', 'dash', 'dot'
    font_size: int
    color: str
    show_by_default: bool


# Default configurations for 3 degrees
DEGREE_CONFIGS: Dict[WaveDegree, DegreeConfig] = {
    WaveDegree.PRIMARY: DegreeConfig(
        degree=WaveDegree.PRIMARY,
        name="Primary",
        lookback=8,
        lookahead=8,
        min_price_move_pct=3.0,
        labels_motive=['1', '2', '3', '4', '5'],
        # Extended to 9 to support Diametric (7) and Symmetrical (9) patterns
        labels_corrective=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'],
        line_width=4,
        line_dash='solid',
        font_size=18,
        color='#58a6ff',  # Blue
        show_by_default=True
    ),
    WaveDegree.INTERMEDIATE: DegreeConfig(
        degree=WaveDegree.INTERMEDIATE,
        name="Intermediate",
        lookback=5,
        lookahead=5,
        min_price_move_pct=1.5,
        labels_motive=['(1)', '(2)', '(3)', '(4)', '(5)'],
        labels_corrective=['(A)', '(B)', '(C)', '(D)', '(E)', '(F)', '(G)', '(H)', '(I)'],
        line_width=2,
        line_dash='solid',
        font_size=14,
        color='#3fb950',  # Green
        show_by_default=True
    ),
    WaveDegree.MINOR: DegreeConfig(
        degree=WaveDegree.MINOR,
        name="Minor",
        lookback=3,
        lookahead=3,
        min_price_move_pct=0.5,
        labels_motive=['i', 'ii', 'iii', 'iv', 'v'],
        labels_corrective=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
        line_width=1,
        line_dash='dot',
        font_size=10,
        color='#d29922',  # Orange
        show_by_default=False
    ),
}


@dataclass
class HierarchicalWave:
    """
    A wave with degree information and subdivision support.
    Each wave can contain sub-waves of a lower degree.
    """
    # Identification
    id: int
    label: str
    degree: WaveDegree
    wave_type: WaveType
    
    # Price and time data
    start_time: Any
    end_time: Any
    start_price: float
    end_price: float
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    
    # Hierarchy
    parent: Optional['HierarchicalWave'] = None
    sub_waves: List['HierarchicalWave'] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    validation_messages: List[str] = field(default_factory=list)
    subdivision_confidence: float = 100.0
    
    @property
    def price_movement(self) -> float:
        """Net price change of this wave"""
        if self.start_price is None or self.end_price is None:
            return 0.0
        return self.end_price - self.start_price
    
    @property
    def price_range(self) -> float:
        """Total price range (high - low)"""
        if self.high_price is None or self.low_price is None:
            return abs(self.price_movement)
        return self.high_price - self.low_price
    
    @property
    def direction(self) -> str:
        """Returns 'up' or 'down'"""
        return 'up' if self.price_movement >= 0 else 'down'
    
    @property
    def has_subdivisions(self) -> bool:
        """Check if this wave has sub-waves"""
        return len(self.sub_waves) > 0
    
    @property
    def expected_subdivision_count(self) -> int:
        """Expected number of subdivisions based on wave type"""
        if self.wave_type == WaveType.MOTIVE:
            return 5
        else:
            return 3
    
    @property
    def subdivision_completeness(self) -> float:
        """
        Percentage of expected subdivisions found.
        Returns 0-100%
        """
        if not self.sub_waves:
            return 0.0
        expected = self.expected_subdivision_count
        actual = len(self.sub_waves)
        return min(100.0, (actual / expected) * 100)
    
    def get_all_descendants(self) -> List['HierarchicalWave']:
        """Get all sub-waves recursively"""
        descendants = []
        for sub in self.sub_waves:
            descendants.append(sub)
            descendants.extend(sub.get_all_descendants())
        return descendants
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'label': self.label,
            'degree': self.degree.name,
            'wave_type': self.wave_type.value,
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'start_price': self.start_price,
            'end_price': self.end_price,
            'price_movement': self.price_movement,
            'direction': self.direction,
            'subdivision_count': len(self.sub_waves),
            'subdivision_confidence': self.subdivision_confidence
        }


@dataclass
class HierarchicalWaveCount:
    """
    Complete wave count with multiple degree levels.
    Contains the full hierarchical structure.
    """
    # Primary structure
    primary_waves: List[HierarchicalWave]
    pattern_name: str
    confidence: float
    description: str = ""
    
    # Degree analysis info
    degrees_analyzed: List[WaveDegree] = field(default_factory=list)
    degree_confidence: Dict[str, float] = field(default_factory=dict)
    
    # Targets and validation
    next_targets: List[Dict] = field(default_factory=list)
    violations: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_waves_by_degree(self, degree: WaveDegree) -> List[HierarchicalWave]:
        """Get all waves of a specific degree"""
        waves = []
        
        def collect(wave: HierarchicalWave):
            if wave.degree == degree:
                waves.append(wave)
            for sub in wave.sub_waves:
                collect(sub)
        
        for primary in self.primary_waves:
            collect(primary)
        
        return waves
    
    def get_all_waves_flat(self) -> List[HierarchicalWave]:
        """Get all waves across all degrees (flattened list)"""
        all_waves = []
        
        def collect(wave: HierarchicalWave):
            all_waves.append(wave)
            for sub in wave.sub_waves:
                collect(sub)
        
        for primary in self.primary_waves:
            collect(primary)
        
        return all_waves
    
    def add_target(self, price: float, description: str, probability: float = 0.5):
        """Add a price target"""
        self.next_targets.append({
            'price': price,
            'description': description,
            'probability': probability
        })
    
    def add_violation(self, rule: str, severity: str, message: str):
        """Add a rule violation"""
        self.violations.append({
            'rule': rule,
            'severity': severity,
            'message': message
        })
    
    @property
    def waves(self) -> List[HierarchicalWave]:
        """Compatibility property - returns primary waves"""
        return self.primary_waves
    
    def get_summary(self) -> str:
        """Get text summary of the wave count"""
        summary = [
            f"Pattern: {self.pattern_name}",
            f"Confidence: {self.confidence:.1f}%",
            f"Primary waves: {len(self.primary_waves)}",
        ]
        
        for degree in self.degrees_analyzed:
            waves = self.get_waves_by_degree(degree)
            conf = self.degree_confidence.get(degree.name, 0)
            summary.append(f"{degree.name}: {len(waves)} waves ({conf:.1f}% confidence)")
        
        return "\n".join(summary)