from typing import List, Dict, Optional, Tuple
import pandas as pd
from ..core.wave import Wave, WaveCount, WaveType
from ..core.monowave import Monowave
from ..engine.pattern_recognizer import PatternRecognizer
from ..engine.confidence_scorer import ConfidenceScorer

class SemiManualAnalyzer:
    """
    Semi-manual NEoWave analysis with user-confirmed pivots.
    """
    
    def __init__(self):
        self.pattern_recognizer = PatternRecognizer()
        self.user_pivots = []
        self.monowaves = []
        self.waves = []
    
    def add_pivot(self, timestamp: pd.Timestamp, price: float, pivot_type: str) -> bool:
        """
        Add a user-confirmed pivot point.
        
        Args:
            timestamp: DateTime of the pivot
            price: Price at the pivot
            pivot_type: 'high' or 'low'
        
        Returns:
            True if pivot was added successfully
        """
        try:
            pivot = {
                'time': timestamp,
                'price': price,
                'type': pivot_type,
                'index': len(self.user_pivots)
            }
            
            # Validate: pivots should alternate between high and low
            if self.user_pivots:
                last_type = self.user_pivots[-1]['type']
                if pivot_type == last_type:
                    return False  # Cannot have consecutive highs or lows
            
            self.user_pivots.append(pivot)
            return True
            
        except Exception as e:
            print(f"Error adding pivot: {e}")
            return False
    
    def remove_last_pivot(self) -> bool:
        """Remove the most recently added pivot"""
        if self.user_pivots:
            self.user_pivots.pop()
            return True
        return False
    
    def clear_pivots(self):
        """Clear all user pivots"""
        self.user_pivots = []
        self.monowaves = []
        self.waves = []
    
    def construct_monowaves(self, df: pd.DataFrame) -> List[Monowave]:
        """
        Construct monowaves from user-confirmed pivots.
        """
        if len(self.user_pivots) < 2:
            return []
        
        from ..core.monowave import MonowaveConstructor
        constructor = MonowaveConstructor(df, self.user_pivots)
        self.monowaves = constructor.construct()
        
        return self.monowaves
    
    def label_waves(self, labels: List[str]) -> List[Wave]:
        """
        Apply user-provided labels to waves.
        
        Args:
            labels: List of wave labels (e.g., ['1', '2', '3', '4', '5'])
        """
        if len(labels) != len(self.monowaves):
            raise ValueError(f"Number of labels ({len(labels)}) must match number of monowaves ({len(self.monowaves)})")
        
        self.waves = []
        
        for i, (monowave, label) in enumerate(zip(self.monowaves, labels)):
            # Determine wave type from label
            if label in ['1', '2', '3', '4', '5']:
                wave_type = WaveType.MOTIVE
            elif label in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                wave_type = WaveType.CORRECTIVE
            else:
                wave_type = WaveType.COMPLEX
            
            wave = Wave(
                label=label,
                wave_type=wave_type,
                monowaves=[monowave]
            )
            
            self.waves.append(wave)
        
        return self.waves
    
    def validate_pattern(self, pattern_name: Optional[str] = None) -> Dict:
        """
        Validate the current wave structure against NEoWave rules.
        
        Args:
            pattern_name: Specific pattern to validate against, or None to auto-detect
        
        Returns:
            Dictionary with validation results
        """
        if not self.waves:
            return {
                'success': False,
                'error': 'No waves to validate. Please label waves first.'
            }
        
        try:
            if pattern_name:
                # Validate against specific pattern
                pattern = self.pattern_recognizer.patterns.get(pattern_name)
                if not pattern:
                    return {
                        'success': False,
                        'error': f'Unknown pattern: {pattern_name}'
                    }
                
                wave_count = pattern.validate(self.waves)
                patterns = [wave_count]
            else:
                # Auto-detect best pattern
                patterns = self.pattern_recognizer.recognize_all(
                    self.waves, 
                    min_confidence=0.0
                )
                patterns = ConfidenceScorer.compare_counts(patterns)
            
            if not patterns:
                return {
                    'success': False,
                    'error': 'No valid pattern found'
                }
            
            primary = patterns[0]
            
            # Build validation report
            report = {
                'success': True,
                'pattern': primary.pattern_name,
                'confidence': primary.confidence,
                'is_valid': primary.confidence > 0,
                'violations': primary.violations,
                'warnings': primary.warnings,
                'targets': primary.next_targets,
                'alternatives': patterns[1:] if len(patterns) > 1 else []
            }
            
            return report
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def suggest_labels(self) -> List[str]:
        """
        Suggest wave labels based on structure.
        Simple heuristic: if 5 waves, suggest impulse; if 3, suggest zigzag.
        """
        num_waves = len(self.monowaves)
        
        if num_waves == 5:
            return ['1', '2', '3', '4', '5']
        elif num_waves == 3:
            return ['A', 'B', 'C']
        elif num_waves == 7:
            return ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        elif num_waves == 9:
            return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        else:
            # Generic numbering
            return [str(i+1) for i in range(num_waves)]
    
    def get_validation_summary(self, validation: Dict) -> str:
        """Generate human-readable validation summary"""
        if not validation['success']:
            return f"❌ Validation failed: {validation.get('error', 'Unknown error')}"
        
        summary = []
        
        if validation['is_valid']:
            summary.append(f"✅ Valid {validation['pattern']} pattern")
            summary.append(f"   Confidence: {validation['confidence']:.1f}%")
        else:
            summary.append(f"❌ Invalid {validation['pattern']} pattern")
            summary.append(f"   Confidence: {validation['confidence']:.1f}%")
        
        if validation['violations']:
            summary.append(f"\n⚠️  Rule Violations:")
            for v in validation['violations']:
                icon = "🔴" if v['severity'] == 'must' else "🟡" if v['severity'] == 'should' else "🟢"
                summary.append(f"   {icon} {v['message']}")
        
        if validation['warnings']:
            summary.append(f"\n⚠️  Warnings:")
            for w in validation['warnings']:
                summary.append(f"   ⚠️  {w}")
        
        if validation['targets']:
            summary.append(f"\n🎯 Price Targets:")
            for t in validation['targets']:
                summary.append(
                    f"   ${t['price']:.2f} - {t['description']} "
                    f"({t['probability']*100:.0f}%)"
                )
        
        if validation['alternatives']:
            summary.append(f"\n🔄 Alternative Interpretations:")
            for alt in validation['alternatives']:
                summary.append(f"   {alt.pattern_name} ({alt.confidence:.1f}%)")
        
        return "\n".join(summary)