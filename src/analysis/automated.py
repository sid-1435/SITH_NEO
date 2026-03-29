"""
Automated NEoWave Analysis Engine with Multi-Degree Support
"""

from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np

from ..core.wave_degree import (
    WaveDegree, WaveType, DEGREE_CONFIGS,
    HierarchicalWave, HierarchicalWaveCount
)
from ..core.multi_degree_detector import (
    MultiDegreePivotDetector,
    HierarchicalWaveBuilder
)
from ..core.pivot_detector import FractalPivotDetector, AdaptivePivotDetector
from ..core.monowave import MonowaveConstructor, Monowave
from ..core.wave import Wave, WaveCount


class AutomatedAnalyzer:
    """
    Fully automated NEoWave analysis engine with multi-degree support.
    
    Features:
    - 3-degree wave analysis (Primary, Intermediate, Minor)
    - Hierarchical wave structure
    - Subdivision detection and validation
    - Confidence scoring across degrees
    """
    
    def __init__(self, 
                 pivot_sensitivity: int = 5,
                 min_confidence: float = 30.0,
                 use_adaptive: bool = True,
                 degrees: List[WaveDegree] = None):
        """
        Args:
            pivot_sensitivity: Base sensitivity (1-10, affects all degrees)
            min_confidence: Minimum confidence to include pattern
            use_adaptive: Use adaptive pivot detection
            degrees: Degrees to analyze. Default: PRIMARY, INTERMEDIATE, MINOR
        """
        self.pivot_sensitivity = pivot_sensitivity
        self.min_confidence = min_confidence
        self.use_adaptive = use_adaptive
        
        # Configure degrees
        self.degrees = degrees or [
            WaveDegree.PRIMARY,
            WaveDegree.INTERMEDIATE,
            WaveDegree.MINOR
        ]
        
        # Adjust degree configs based on sensitivity
        self._adjust_configs_for_sensitivity()
        
        # Initialize detectors
        self.multi_detector = MultiDegreePivotDetector(degrees=self.degrees)
        self.wave_builder = HierarchicalWaveBuilder(degrees=self.degrees)
    
    def _adjust_configs_for_sensitivity(self) -> None:
        """
        Adjust degree configurations based on pivot sensitivity setting.
        Higher sensitivity = more pivots at each level.
        """
        sensitivity_factor = self.pivot_sensitivity / 5.0  # Normalize to 1.0
        
        for degree, config in DEGREE_CONFIGS.items():
            if degree in self.degrees:
                # Adjust lookback (inverse relationship)
                base_lookback = config.lookback
                adjusted_lookback = max(2, int(base_lookback / sensitivity_factor))
                config.lookback = adjusted_lookback
                config.lookahead = adjusted_lookback
                
                # Adjust minimum price move (inverse relationship)
                base_move = config.min_price_move_pct
                adjusted_move = base_move / sensitivity_factor
                config.min_price_move_pct = max(0.2, adjusted_move)
    
    def analyze(self, df: pd.DataFrame, max_patterns: int = 3) -> Dict[str, Any]:
        """
        Perform complete multi-degree NEoWave analysis.
        
        Args:
            df: OHLC DataFrame
            max_patterns: Maximum alternative patterns to return
        
        Returns:
            Analysis result dictionary with hierarchical wave structure
        """
        try:
            # Step 1: Detect pivots at all degree levels
            multi_degree_pivots = self.multi_detector.detect_all(df)
            
            # Count total pivots
            total_pivots = sum(len(p) for p in multi_degree_pivots.values())
            
            if total_pivots < 3:
                return self._empty_result(
                    "Insufficient pivots detected. Try adjusting sensitivity.",
                    multi_degree_pivots
                )
            
            # Step 2: Build hierarchical wave structure
            wave_count = self.wave_builder.build(df, multi_degree_pivots)
            
            if not wave_count:
                return self._empty_result(
                    "Could not build wave structure.",
                    multi_degree_pivots
                )
            
            # Step 3: Collect all pivots for visualization
            all_pivots = []
            for degree, pivots in multi_degree_pivots.items():
                for pivot in pivots:
                    pivot['degree'] = degree
                    all_pivots.append(pivot)
            
            # Sort by time
            all_pivots.sort(key=lambda p: p['time'])
            
            # Step 4: Create monowaves for "all swings" visualization
            all_monowaves = self._create_monowaves_from_pivots(df, all_pivots)
            
            return {
                'success': True,
                'pivots': all_pivots,
                'monowaves': all_monowaves,
                'waves': wave_count.primary_waves,  # For compatibility
                'patterns': [wave_count],
                'primary_pattern': wave_count,
                'multi_degree_pivots': multi_degree_pivots,
                'hierarchical': True  # Flag for hierarchical mode
            }
            
        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': f"Analysis error: {str(e)}\n{traceback.format_exc()}",
                'pivots': [],
                'monowaves': [],
                'waves': [],
                'patterns': [],
                'primary_pattern': None
            }
    
    def _empty_result(self, error: str, 
                      multi_degree_pivots: Dict = None) -> Dict[str, Any]:
        """Return empty result with error message"""
        all_pivots = []
        if multi_degree_pivots:
            for pivots in multi_degree_pivots.values():
                all_pivots.extend(pivots)
        
        return {
            'success': False,
            'error': error,
            'pivots': all_pivots,
            'monowaves': [],
            'waves': [],
            'patterns': [],
            'primary_pattern': None,
            'multi_degree_pivots': multi_degree_pivots or {}
        }
    
    def _create_monowaves_from_pivots(self, df: pd.DataFrame, 
                                       pivots: List[Dict]) -> List[Monowave]:
        """Create monowave objects from pivots for visualization"""
        if len(pivots) < 2:
            return []
        
        monowaves = []
        sorted_pivots = sorted(pivots, key=lambda p: p['time'])
        
        for i in range(len(sorted_pivots) - 1):
            start_pivot = sorted_pivots[i]
            end_pivot = sorted_pivots[i + 1]
            
            # Get segment data
            mask = (df.index >= start_pivot['time']) & (df.index <= end_pivot['time'])
            segment = df[mask]
            
            high_price = segment['high'].max() if len(segment) > 0 else max(start_pivot['price'], end_pivot['price'])
            low_price = segment['low'].min() if len(segment) > 0 else min(start_pivot['price'], end_pivot['price'])
            
            mw = Monowave(
                id=i,
                start_time=start_pivot['time'],
                end_time=end_pivot['time'],
                start_price=start_pivot['price'],
                end_price=end_pivot['price'],
                high_price=high_price,
                low_price=low_price,
                high_first=end_pivot['price'] > start_pivot['price']
            )
            
            monowaves.append(mw)
        
        return monowaves
    
    def get_analysis_summary(self, result: Dict) -> str:
        """Generate human-readable analysis summary"""
        if not result.get('success'):
            return f"❌ Analysis failed: {result.get('error', 'Unknown error')}"
        
        summary = []
        summary.append("✅ Multi-Degree Analysis Complete")
        summary.append(f"📍 Total pivots: {len(result.get('pivots', []))}")
        
        # Pivots by degree
        multi_pivots = result.get('multi_degree_pivots', {})
        for degree, pivots in multi_pivots.items():
            summary.append(f"   • {degree.name}: {len(pivots)} pivots")
        
        # Pattern info
        pattern = result.get('primary_pattern')
        if pattern:
            summary.append(f"\n🎯 Pattern: {pattern.pattern_name}")
            summary.append(f"   Confidence: {pattern.confidence:.1f}%")
            
            if hasattr(pattern, 'degree_confidence'):
                summary.append("\n📊 Degree Confidence:")
                for degree_name, conf in pattern.degree_confidence.items():
                    summary.append(f"   • {degree_name}: {conf:.1f}%")
            
            if hasattr(pattern, 'primary_waves'):
                labels = " → ".join([w.label for w in pattern.primary_waves])
                summary.append(f"\n🌊 Primary: {labels}")
                
                # Count subdivisions
                for wave in pattern.primary_waves:
                    if wave.sub_waves:
                        sub_labels = " → ".join([s.label for s in wave.sub_waves])
                        summary.append(f"   Wave {wave.label} subdivisions: {sub_labels}")
        
        return "\n".join(summary)