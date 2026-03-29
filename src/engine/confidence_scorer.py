import numpy as np
from typing import List, Dict
from ..core.wave import Wave, WaveCount
from ..config.rules import FIBONACCI_RATIOS, is_fibonacci_aligned

class ConfidenceScorer:
    """
    Advanced confidence scoring system for wave counts.
    Considers multiple factors beyond basic rule compliance.
    """
    
    @staticmethod
    def enhance_score(wave_count: WaveCount) -> float:
        """
        Enhance confidence score with additional factors.
        
        Factors considered:
        - Fibonacci alignment
        - Time symmetry
        - Pattern clarity
        - Historical success rate (future enhancement)
        """
        base_score = wave_count.confidence
        
        if base_score == 0:
            return 0
        
        bonuses = 0
        
        # Fibonacci alignment bonus
        fib_bonus = ConfidenceScorer._fibonacci_bonus(wave_count.waves)
        bonuses += fib_bonus
        
        # Time symmetry bonus
        time_bonus = ConfidenceScorer._time_symmetry_bonus(wave_count.waves)
        bonuses += time_bonus
        
        # Pattern clarity bonus
        clarity_bonus = ConfidenceScorer._clarity_bonus(wave_count)
        bonuses += clarity_bonus
        
        # Apply bonuses (max +15 points)
        enhanced_score = min(100, base_score + min(15, bonuses))
        
        return enhanced_score
    
    @staticmethod
    def _fibonacci_bonus(waves: List[Wave]) -> float:
        """
        Award bonus for strong Fibonacci relationships.
        """
        if len(waves) < 3:
            return 0
        
        fib_alignments = 0
        comparisons = 0
        
        # Check wave relationships
        for i in range(1, len(waves)):
            ratio = abs(waves[i].price_movement) / abs(waves[i-1].price_movement) if waves[i-1].price_movement != 0 else 0
            
            if is_fibonacci_aligned(ratio, tolerance=0.1):
                fib_alignments += 1
            comparisons += 1
        
        if comparisons > 0:
            alignment_ratio = fib_alignments / comparisons
            return alignment_ratio * 8  # Max 8 points
        
        return 0
    
    @staticmethod
    def _time_symmetry_bonus(waves: List[Wave]) -> float:
        """
        Award bonus for time symmetry between waves.
        """
        if len(waves) < 3:
            return 0
        
        durations = [w.time_duration for w in waves]
        avg_duration = np.mean(durations)
        std_duration = np.std(durations)
        
        if avg_duration == 0:
            return 0
        
        # Coefficient of variation
        cv = std_duration / avg_duration
        
        # Lower CV = more symmetry
        if cv < 0.2:
            return 5
        elif cv < 0.4:
            return 3
        elif cv < 0.6:
            return 1
        
        return 0
    
    @staticmethod
    def _clarity_bonus(wave_count: WaveCount) -> float:
        """
        Award bonus for pattern clarity (few warnings, clear structure).
        """
        bonus = 0
        
        # Bonus for no warnings
        if len(wave_count.warnings) == 0:
            bonus += 2
        
        # Bonus for few violations
        if len(wave_count.violations) == 0:
            bonus += 3
        elif len(wave_count.violations) <= 2:
            bonus += 1
        
        return bonus
    
    @staticmethod
    def compare_counts(counts: List[WaveCount]) -> List[WaveCount]:
        """
        Compare multiple wave counts and adjust relative confidence.
        """
        if not counts:
            return []
        
        # Enhance all scores
        for count in counts:
            count.confidence = ConfidenceScorer.enhance_score(count)
        
        # Sort by confidence
        counts.sort(key=lambda x: x.confidence, reverse=True)
        
        # Normalize if top score is very high
        if counts[0].confidence > 90:
            # Reduce confidence of alternatives
            for i in range(1, len(counts)):
                counts[i].confidence *= 0.7
        
        return counts