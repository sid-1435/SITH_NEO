"""Core modules for NEoWave analysis."""

from .monowave import Monowave, MonowaveConstructor
from .pivot_detector import FractalPivotDetector, AdaptivePivotDetector
from .wave import Wave, WaveCount, WaveType as LegacyWaveType
from .wave_degree import (
    WaveDegree, 
    WaveType,
    DegreeConfig, 
    DEGREE_CONFIGS,
    HierarchicalWave, 
    HierarchicalWaveCount
)
from .multi_degree_detector import (
    MultiDegreePivotDetector,
    HierarchicalWaveBuilder,
    WaveValidator
)

__all__ = [
    'Monowave',
    'MonowaveConstructor',
    'FractalPivotDetector',
    'AdaptivePivotDetector',
    'Wave',
    'WaveCount',
    'LegacyWaveType',
    'WaveDegree',
    'WaveType',
    'DegreeConfig',
    'DEGREE_CONFIGS',
    'HierarchicalWave',
    'HierarchicalWaveCount',
    'MultiDegreePivotDetector',
    'HierarchicalWaveBuilder',
    'WaveValidator'
]
