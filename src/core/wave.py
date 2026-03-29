from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
from .monowave import Monowave

class WaveType(Enum):
    """Types of waves in NEoWave"""
    MOTIVE = "motive"
    CORRECTIVE = "corrective"
    COMPLEX = "complex"

class WaveLabel(Enum):
    """Standard wave labels"""
    # Motive labels
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    
    # Corrective labels
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    
    # Complex labels
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"

@dataclass
class Wave:
    """
    Represents a complete wave structure (can contain multiple monowaves).
    """
    label: str
    wave_type: WaveType
    monowaves: List[Monowave]
    degree: int = 0  # Wave degree (0=smallest, higher=larger timeframe)
    
    # Pattern information
    pattern_name: Optional[str] = None
    pattern_complete: bool = False
    
    # Relationships
    parent_wave: Optional['Wave'] = None
    sub_waves: List['Wave'] = field(default_factory=list)
    
    @property
    def start_time(self):
        return self.monowaves[0].start_time if self.monowaves else None
    
    @property
    def end_time(self):
        return self.monowaves[-1].end_time if self.monowaves else None
    
    @property
    def start_price(self):
        return self.monowaves[0].start_price if self.monowaves else None
    
    @property
    def end_price(self):
        return self.monowaves[-1].end_price if self.monowaves else None
    
    @property
    def price_movement(self):
        if not self.monowaves:
            return 0
        return self.end_price - self.start_price
    
    @property
    def time_duration(self):
        if not self.monowaves:
            return 0
        return sum(m.time_duration for m in self.monowaves)
    
    @property
    def high_price(self):
        if not self.monowaves:
            return None
        return max(m.high_price for m in self.monowaves)
    
    @property
    def low_price(self):
        if not self.monowaves:
            return None
        return min(m.low_price for m in self.monowaves)
    
    def fibonacci_relationship(self, reference: 'Wave') -> float:
        """Calculate Fibonacci ratio to reference wave"""
        if not reference or reference.price_movement == 0:
            return 0
        return abs(self.price_movement) / abs(reference.price_movement)
    
    def time_relationship(self, reference: 'Wave') -> float:
        """Calculate time ratio to reference wave"""
        if not reference or reference.time_duration == 0:
            return 0
        return self.time_duration / reference.time_duration
    
    def __repr__(self):
        return (f"Wave({self.label}, {self.wave_type.value}, "
                f"${self.start_price:.2f}→${self.end_price:.2f})")


@dataclass
class WaveCount:
    """
    Represents a complete wave count interpretation of the data.
    """
    waves: List[Wave]
    pattern_name: str
    confidence: float = 0.0
    
    # Metadata
    description: str = ""
    next_targets: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Rule violations
    violations: List[Dict] = field(default_factory=list)
    
    def add_violation(self, rule_name: str, severity: str, message: str):
        """Add a rule violation"""
        self.violations.append({
            'rule': rule_name,
            'severity': severity,
            'message': message
        })
    
    def add_target(self, price: float, description: str, probability: float = 1.0):
        """Add a price target"""
        self.next_targets.append({
            'price': price,
            'description': description,
            'probability': probability
        })
    
    def __repr__(self):
        return (f"WaveCount({self.pattern_name}, "
                f"confidence={self.confidence:.1f}%, "
                f"{len(self.waves)} waves)")