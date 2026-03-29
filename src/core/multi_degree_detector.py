"""
Multi-Degree Pivot Detection and Hierarchical Wave Building
With integrated pattern validation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .wave_degree import (
    WaveDegree, WaveType, DegreeConfig, DEGREE_CONFIGS,
    HierarchicalWave, HierarchicalWaveCount
)
from .pivot_detector import AdaptivePivotDetector
from .monowave import Monowave, MonowaveConstructor


class MultiDegreePivotDetector:
    """
    Detects pivots at multiple degree levels simultaneously.
    Each degree uses different sensitivity settings.
    """
    
    def __init__(self, degrees: List[WaveDegree] = None):
        self.degrees = degrees or [
            WaveDegree.PRIMARY,
            WaveDegree.INTERMEDIATE,
            WaveDegree.MINOR
        ]
    
    def detect_all(self, df: pd.DataFrame) -> Dict[WaveDegree, List[Dict]]:
        """Detect pivots at all configured degree levels."""
        results = {}
        
        for degree in self.degrees:
            config = DEGREE_CONFIGS.get(degree)
            if not config:
                continue
            
            detector = AdaptivePivotDetector(
                lookback=config.lookback,
                lookahead=config.lookahead,
                min_price_move_pct=config.min_price_move_pct
            )
            
            pivots = detector.detect(df)
            
            for pivot in pivots:
                pivot['degree'] = degree
            
            results[degree] = pivots
        
        return results


class WaveValidator:
    """
    Validates wave structures against Elliott Wave / NEoWave rules.
    This is called DURING wave construction to reject invalid patterns early.
    """
    
    @staticmethod
    def validate_wave_structure(waves: List[HierarchicalWave], 
                                 pattern_type: str = 'impulse') -> Tuple[bool, List[str], float]:
        """
        Validate a wave structure against critical rules.
        
        Args:
            waves: List of HierarchicalWave objects
            pattern_type: 'impulse' or 'diagonal'
        
        Returns:
            Tuple of (is_valid, list_of_violations, confidence_score)
        """
        violations = []
        confidence = 100.0
        
        if len(waves) < 2:
            return True, [], confidence
        
        # Determine trend direction from Wave 1
        is_uptrend = WaveValidator._is_uptrend(waves)
        
        # =================================================================
        # RULE 1: Wave 2 cannot exceed Wave 1's origin (CRITICAL)
        # =================================================================
        if len(waves) >= 2:
            valid, message = WaveValidator._check_wave2_origin(waves, is_uptrend)
            if not valid:
                violations.append(f"CRITICAL: {message}")
                confidence = 0  # Pattern is INVALID
                return False, violations, confidence
        
        # =================================================================
        # RULE 2: Wave 4 cannot exceed Wave 3's origin (CRITICAL)
        # =================================================================
        if len(waves) >= 4:
            valid, message = WaveValidator._check_wave4_origin(waves, is_uptrend)
            if not valid:
                violations.append(f"CRITICAL: {message}")
                confidence = 0
                return False, violations, confidence
        
        # =================================================================
        # RULE 3: Wave 3 must exceed Wave 1's endpoint
        # =================================================================
        if len(waves) >= 3:
            valid, message = WaveValidator._check_wave3_exceeds_wave1(waves, is_uptrend)
            if not valid:
                violations.append(f"CRITICAL: {message}")
                confidence = 0
                return False, violations, confidence
        
        # =================================================================
        # RULE 4: Wave 5 must exceed Wave 3's endpoint (for motive patterns)
        # =================================================================
        if len(waves) >= 5:
            valid, message = WaveValidator._check_wave5_exceeds_wave3(waves, is_uptrend)
            if not valid:
                violations.append(f"WARNING: {message}")
                confidence -= 30  # Significant penalty but not invalid
        
        # =================================================================
        # RULE 5: Wave 3 cannot be the shortest (for impulse)
        # =================================================================
        if len(waves) >= 5 and pattern_type == 'impulse':
            valid, message = WaveValidator._check_wave3_not_shortest(waves)
            if not valid:
                violations.append(f"CRITICAL: {message}")
                confidence = 0
                return False, violations, confidence
        
        # =================================================================
        # RULE 6: Wave 4 overlap rule
        # =================================================================
        if len(waves) >= 4:
            has_overlap = WaveValidator._check_wave4_wave1_overlap(waves, is_uptrend)
            
            if pattern_type == 'impulse' and has_overlap:
                violations.append("CRITICAL: Wave 4 overlaps Wave 1 (not allowed in impulse)")
                confidence = 0
                return False, violations, confidence
            elif pattern_type == 'diagonal' and not has_overlap:
                violations.append("WARNING: Wave 4 should overlap Wave 1 in diagonal")
                confidence -= 20
        
        return len(violations) == 0 or confidence > 0, violations, max(0, confidence)
    
    @staticmethod
    def _is_uptrend(waves: List[HierarchicalWave]) -> bool:
        """Determine if pattern is in uptrend"""
        if not waves or len(waves) == 0:
            return True
        
        wave1 = waves[0]
        if wave1.start_price is None or wave1.end_price is None:
            return True
        
        return wave1.end_price > wave1.start_price
    
    @staticmethod
    def _check_wave2_origin(waves: List[HierarchicalWave], is_uptrend: bool) -> Tuple[bool, str]:
        """
        Check that Wave 2 does not exceed Wave 1's origin.
        """
        wave1 = waves[0]
        wave2 = waves[1]
        
        wave1_origin = wave1.start_price
        
        if wave1_origin is None:
            return True, ""
        
        # Get Wave 2's extreme point
        if is_uptrend:
            # In uptrend, check Wave 2's lowest point
            wave2_extreme = wave2.low_price if wave2.low_price else wave2.end_price
            if wave2_extreme is None:
                return True, ""
            
            if wave2_extreme < wave1_origin:
                return False, f"Wave 2 low ({wave2_extreme:.2f}) went below Wave 1 origin ({wave1_origin:.2f})"
        else:
            # In downtrend, check Wave 2's highest point
            wave2_extreme = wave2.high_price if wave2.high_price else wave2.end_price
            if wave2_extreme is None:
                return True, ""
            
            if wave2_extreme > wave1_origin:
                return False, f"Wave 2 high ({wave2_extreme:.2f}) went above Wave 1 origin ({wave1_origin:.2f})"
        
        return True, ""
    
    @staticmethod
    def _check_wave4_origin(waves: List[HierarchicalWave], is_uptrend: bool) -> Tuple[bool, str]:
        """
        Check that Wave 4 does not exceed Wave 3's origin.
        """
        wave3 = waves[2]
        wave4 = waves[3]
        
        wave3_origin = wave3.start_price
        
        if wave3_origin is None:
            return True, ""
        
        if is_uptrend:
            wave4_extreme = wave4.low_price if wave4.low_price else wave4.end_price
            if wave4_extreme is None:
                return True, ""
            
            if wave4_extreme < wave3_origin:
                return False, f"Wave 4 low ({wave4_extreme:.2f}) went below Wave 3 origin ({wave3_origin:.2f})"
        else:
            wave4_extreme = wave4.high_price if wave4.high_price else wave4.end_price
            if wave4_extreme is None:
                return True, ""
            
            if wave4_extreme > wave3_origin:
                return False, f"Wave 4 high ({wave4_extreme:.2f}) went above Wave 3 origin ({wave3_origin:.2f})"
        
        return True, ""
    
    @staticmethod
    def _check_wave3_exceeds_wave1(waves: List[HierarchicalWave], is_uptrend: bool) -> Tuple[bool, str]:
        """
        Check that Wave 3 exceeds Wave 1's endpoint.
        """
        wave1 = waves[0]
        wave3 = waves[2]
        
        if wave1.end_price is None or wave3.end_price is None:
            return True, ""
        
        if is_uptrend:
            if wave3.end_price <= wave1.end_price:
                return False, f"Wave 3 end ({wave3.end_price:.2f}) did not exceed Wave 1 end ({wave1.end_price:.2f})"
        else:
            if wave3.end_price >= wave1.end_price:
                return False, f"Wave 3 end ({wave3.end_price:.2f}) did not exceed Wave 1 end ({wave1.end_price:.2f})"
        
        return True, ""
    
    @staticmethod
    def _check_wave5_exceeds_wave3(waves: List[HierarchicalWave], is_uptrend: bool) -> Tuple[bool, str]:
        """
        Check that Wave 5 exceeds Wave 3's endpoint.
        """
        wave3 = waves[2]
        wave5 = waves[4]
        
        if wave3.end_price is None or wave5.end_price is None:
            return True, ""
        
        if is_uptrend:
            if wave5.end_price <= wave3.end_price:
                return False, f"Wave 5 end ({wave5.end_price:.2f}) did not exceed Wave 3 end ({wave3.end_price:.2f})"
        else:
            if wave5.end_price >= wave3.end_price:
                return False, f"Wave 5 end ({wave5.end_price:.2f}) did not exceed Wave 3 end ({wave3.end_price:.2f})"
        
        return True, ""
    
    @staticmethod
    def _check_wave3_not_shortest(waves: List[HierarchicalWave]) -> Tuple[bool, str]:
        """
        Check that Wave 3 is not the shortest motive wave.
        """
        w1_len = abs(waves[0].price_movement) if waves[0].price_movement else 0
        w3_len = abs(waves[2].price_movement) if waves[2].price_movement else 0
        w5_len = abs(waves[4].price_movement) if waves[4].price_movement else 0
        
        if w3_len < w1_len and w3_len < w5_len:
            return False, f"Wave 3 ({w3_len:.2f}) is shorter than both Wave 1 ({w1_len:.2f}) and Wave 5 ({w5_len:.2f})"
        
        return True, ""
    
    @staticmethod
    def _check_wave4_wave1_overlap(waves: List[HierarchicalWave], is_uptrend: bool) -> bool:
        """
        Check if Wave 4 overlaps Wave 1's price territory.
        Returns True if there IS overlap.
        """
        wave1 = waves[0]
        wave4 = waves[3]
        
        w1_high = wave1.high_price or max(wave1.start_price or 0, wave1.end_price or 0)
        w1_low = wave1.low_price or min(wave1.start_price or float('inf'), wave1.end_price or float('inf'))
        
        w4_high = wave4.high_price or max(wave4.start_price or 0, wave4.end_price or 0)
        w4_low = wave4.low_price or min(wave4.start_price or float('inf'), wave4.end_price or float('inf'))
        
        if is_uptrend:
            # In uptrend, overlap occurs if Wave 4 low goes below Wave 1 high
            return w4_low < w1_high
        else:
            # In downtrend, overlap occurs if Wave 4 high goes above Wave 1 low
            return w4_high > w1_low


class HierarchicalWaveBuilder:
    """
    Builds hierarchical wave structure from multi-degree pivots.
    Now includes validation to reject invalid wave structures.
    """
    
    def __init__(self, degrees: List[WaveDegree] = None):
        self.degrees = degrees or [
            WaveDegree.PRIMARY,
            WaveDegree.INTERMEDIATE,
            WaveDegree.MINOR
        ]
        self.wave_id_counter = 0
        self.validator = WaveValidator()
    
    def _next_id(self) -> int:
        """Generate unique wave ID"""
        self.wave_id_counter += 1
        return self.wave_id_counter
    
    def build(self, 
              df: pd.DataFrame,
              multi_degree_pivots: Dict[WaveDegree, List[Dict]]) -> Optional[HierarchicalWaveCount]:
        """
        Build and validate hierarchical wave structure.
        """
        self.wave_id_counter = 0
        
        primary_degree = self.degrees[0] if self.degrees else WaveDegree.PRIMARY
        primary_pivots = multi_degree_pivots.get(primary_degree, [])
        
        if len(primary_pivots) < 3:
            return None
        
        # Try to find the best valid wave structure
        best_wave_count = None
        best_confidence = -1
        
        # Try different starting points
        for start_idx in range(max(0, len(primary_pivots) - 10)):
            for wave_count in [5, 3, 7, 9]:  # Try different pattern sizes
                end_idx = start_idx + wave_count + 1
                
                if end_idx > len(primary_pivots):
                    continue
                
                subset_pivots = primary_pivots[start_idx:end_idx]
                
                # Build waves from this subset
                primary_waves = self._build_waves_from_pivots(
                    df=df,
                    pivots=subset_pivots,
                    degree=primary_degree
                )
                
                if not primary_waves:
                    continue
                
                # Determine pattern type
                pattern_type = 'impulse' if len(primary_waves) == 5 else 'corrective'
                
                # VALIDATE the wave structure
                is_valid, violations, confidence = self.validator.validate_wave_structure(
                    primary_waves, 
                    pattern_type=pattern_type
                )
                
                # Skip invalid patterns
                if not is_valid or confidence == 0:
                    continue
                
                # Check if this is better than current best
                if confidence > best_confidence:
                    # Build subdivisions
                    for wave in primary_waves:
                        self._build_subdivisions(
                            df=df,
                            parent_wave=wave,
                            multi_degree_pivots=multi_degree_pivots,
                            current_degree_index=0
                        )
                    
                    # Determine pattern name
                    pattern_name, pattern_conf = self._identify_pattern(primary_waves)
                    
                    # Combine confidences
                    final_confidence = confidence * 0.7 + pattern_conf * 0.3
                    
                    # Calculate degree confidence
                    degree_confidence = self._calculate_degree_confidence(primary_waves)
                    
                    # Create wave count
                    wave_count_obj = HierarchicalWaveCount(
                        primary_waves=primary_waves,
                        pattern_name=pattern_name,
                        confidence=final_confidence,
                        description=self._generate_description(primary_waves, pattern_name, violations),
                        degrees_analyzed=self.degrees,
                        degree_confidence=degree_confidence
                    )
                    
                    # Add violations as warnings
                    for v in violations:
                        wave_count_obj.warnings.append(v)
                    
                    # Calculate targets
                    self._calculate_targets(wave_count_obj)
                    
                    best_wave_count = wave_count_obj
                    best_confidence = final_confidence
        
        # If no valid pattern found, try to create a basic "developing" pattern
        if best_wave_count is None:
            best_wave_count = self._create_developing_pattern(df, primary_pivots, primary_degree)
        
        return best_wave_count
    
    def _create_developing_pattern(self, df: pd.DataFrame, 
                                    pivots: List[Dict], 
                                    degree: WaveDegree) -> Optional[HierarchicalWaveCount]:
        """
        Create a basic pattern when no valid Elliott Wave pattern is found.
        """
        if len(pivots) < 3:
            return None
        
        # Take the most recent pivots
        recent_pivots = pivots[-6:] if len(pivots) >= 6 else pivots
        
        waves = self._build_waves_from_pivots(df, recent_pivots, degree)
        
        if not waves:
            return None
        
        # Don't validate - just mark as developing
        return HierarchicalWaveCount(
            primary_waves=waves,
            pattern_name="Developing",
            confidence=25.0,
            description="No complete valid pattern found. Wave structure is still developing.",
            degrees_analyzed=self.degrees,
            degree_confidence={d.name: 0.0 for d in self.degrees}
        )
    
    def _build_waves_from_pivots(self,
                                  df: pd.DataFrame,
                                  pivots: List[Dict],
                                  degree: WaveDegree) -> List[HierarchicalWave]:
        """Convert pivots to HierarchicalWave objects."""
        if len(pivots) < 2:
            return []
        
        config = DEGREE_CONFIGS.get(degree)
        waves = []
        
        sorted_pivots = sorted(pivots, key=lambda p: p['time'])
        num_waves = len(sorted_pivots) - 1
        
        # Select labels based on wave count
        if num_waves >= 5:
            labels = config.labels_motive[:5]
            wave_types = [WaveType.MOTIVE, WaveType.CORRECTIVE, WaveType.MOTIVE, 
                         WaveType.CORRECTIVE, WaveType.MOTIVE]
        elif num_waves >= 3:
            labels = config.labels_corrective[:3]
            wave_types = [WaveType.MOTIVE, WaveType.CORRECTIVE, WaveType.MOTIVE]
        elif num_waves == 7:
            labels = config.labels_corrective[:7] if len(config.labels_corrective) >= 7 else ['A','B','C','D','E','F','G']
            wave_types = [WaveType.MOTIVE if i % 2 == 0 else WaveType.CORRECTIVE for i in range(7)]
        else:
            labels = config.labels_motive[:num_waves]
            wave_types = [WaveType.MOTIVE if i % 2 == 0 else WaveType.CORRECTIVE 
                         for i in range(num_waves)]
        
        for i in range(min(len(sorted_pivots) - 1, len(labels))):
            start_pivot = sorted_pivots[i]
            end_pivot = sorted_pivots[i + 1]
            
            mask = (df.index >= start_pivot['time']) & (df.index <= end_pivot['time'])
            segment = df[mask]
            
            high_price = segment['high'].max() if len(segment) > 0 else max(start_pivot['price'], end_pivot['price'])
            low_price = segment['low'].min() if len(segment) > 0 else min(start_pivot['price'], end_pivot['price'])
            
            wave = HierarchicalWave(
                id=self._next_id(),
                label=labels[i],
                degree=degree,
                wave_type=wave_types[i] if i < len(wave_types) else WaveType.MOTIVE,
                start_time=start_pivot['time'],
                end_time=end_pivot['time'],
                start_price=start_pivot['price'],
                end_price=end_pivot['price'],
                high_price=high_price,
                low_price=low_price
            )
            
            waves.append(wave)
        
        return waves
    
    def _build_subdivisions(self,
                            df: pd.DataFrame,
                            parent_wave: HierarchicalWave,
                            multi_degree_pivots: Dict[WaveDegree, List[Dict]],
                            current_degree_index: int) -> None:
        """Recursively build subdivisions for a parent wave."""
        if current_degree_index >= len(self.degrees) - 1:
            return
        
        child_degree = self.degrees[current_degree_index + 1]
        child_pivots = multi_degree_pivots.get(child_degree, [])
        
        if not child_pivots:
            return
        
        parent_start = parent_wave.start_time
        parent_end = parent_wave.end_time
        
        relevant_pivots = [
            p for p in child_pivots
            if parent_start <= p['time'] <= parent_end
        ]
        
        if len(relevant_pivots) < 2:
            return
        
        # Add boundary pivots
        start_pivot = {'time': parent_start, 'price': parent_wave.start_price, 'type': 'start', 'degree': child_degree}
        end_pivot = {'time': parent_end, 'price': parent_wave.end_price, 'type': 'end', 'degree': child_degree}
        
        has_start = any(abs((p['time'] - parent_start).total_seconds()) < 60 for p in relevant_pivots)
        has_end = any(abs((p['time'] - parent_end).total_seconds()) < 60 for p in relevant_pivots)
        
        if not has_start:
            relevant_pivots.insert(0, start_pivot)
        if not has_end:
            relevant_pivots.append(end_pivot)
        
        relevant_pivots = sorted(relevant_pivots, key=lambda p: p['time'])
        
        child_waves = self._build_waves_from_pivots(
            df=df,
            pivots=relevant_pivots,
            degree=child_degree
        )
        
        # Validate subdivisions too
        if child_waves:
            is_valid, _, sub_confidence = WaveValidator.validate_wave_structure(
                child_waves, 
                pattern_type='impulse' if parent_wave.wave_type == WaveType.MOTIVE else 'corrective'
            )
            
            parent_wave.subdivision_confidence = sub_confidence
            
            if is_valid:
                for child in child_waves:
                    child.parent = parent_wave
                parent_wave.sub_waves = child_waves
                
                # Recursive
                for child in child_waves:
                    self._build_subdivisions(
                        df=df,
                        parent_wave=child,
                        multi_degree_pivots=multi_degree_pivots,
                        current_degree_index=current_degree_index + 1
                    )
    
    def _identify_pattern(self, waves: List[HierarchicalWave]) -> Tuple[str, float]:
        """Identify pattern type from waves."""
        num_waves = len(waves)
        
        if num_waves == 5:
            if self._check_wave4_overlap_exists(waves):
                return "Diagonal", 70.0
            else:
                return "Impulse", 85.0
        elif num_waves == 3:
            if self._is_zigzag(waves):
                return "Zigzag", 80.0
            else:
                return "Flat", 75.0
        elif num_waves == 7:
            return "Diametric", 70.0
        elif num_waves == 9:
            return "Symmetrical", 65.0
        else:
            return "Developing", 40.0
    
    def _check_wave4_overlap_exists(self, waves: List[HierarchicalWave]) -> bool:
        """Check if Wave 4 overlaps Wave 1"""
        if len(waves) < 4:
            return False
        
        wave1 = waves[0]
        wave4 = waves[3]
        
        w1_range = (min(wave1.start_price or 0, wave1.end_price or 0), 
                   max(wave1.start_price or 0, wave1.end_price or 0))
        w4_range = (min(wave4.start_price or 0, wave4.end_price or 0),
                   max(wave4.start_price or 0, wave4.end_price or 0))
        
        return not (w4_range[0] > w1_range[1] or w4_range[1] < w1_range[0])
    
    def _is_zigzag(self, waves: List[HierarchicalWave]) -> bool:
        """Check if pattern is zigzag"""
        if len(waves) != 3:
            return False
        
        a_length = abs(waves[0].price_movement) if waves[0].price_movement else 0
        b_length = abs(waves[1].price_movement) if waves[1].price_movement else 0
        
        if a_length == 0:
            return False
        
        b_retracement = b_length / a_length
        return 0.3 <= b_retracement <= 0.85
    
    def _calculate_degree_confidence(self, waves: List[HierarchicalWave]) -> Dict[str, float]:
        """Calculate confidence for each degree level."""
        confidence = {}
        
        for degree in self.degrees:
            degree_waves = []
            
            def collect(wave: HierarchicalWave):
                if wave.degree == degree:
                    degree_waves.append(wave)
                for sub in wave.sub_waves:
                    collect(sub)
            
            for wave in waves:
                collect(wave)
            
            if degree_waves:
                avg_confidence = np.mean([w.subdivision_confidence for w in degree_waves])
                confidence[degree.name] = avg_confidence
            else:
                confidence[degree.name] = 0.0
        
        return confidence
    
    def _generate_description(self, waves: List[HierarchicalWave], 
                               pattern_name: str,
                               violations: List[str]) -> str:
        """Generate pattern description."""
        wave_labels = " → ".join([w.label for w in waves])
        
        desc = f"{pattern_name} pattern: {wave_labels}"
        
        if violations:
            desc += f". Issues: {len(violations)}"
        
        return desc
    
    def _calculate_targets(self, wave_count: HierarchicalWaveCount) -> None:
        """Calculate price targets."""
        waves = wave_count.primary_waves
        
        if not waves:
            return
        
        is_uptrend = waves[0].end_price > waves[0].start_price if waves[0].start_price and waves[0].end_price else True
        
        if len(waves) >= 4:
            wave1 = waves[0]
            wave4 = waves[3]
            
            if wave1.price_movement and wave4.end_price:
                w1_length = abs(wave1.price_movement)
                direction = 1 if is_uptrend else -1
                
                wave_count.add_target(
                    price=wave4.end_price + (w1_length * 0.618 * direction),
                    description="Wave 5 = 0.618 × Wave 1",
                    probability=0.6
                )
                
                wave_count.add_target(
                    price=wave4.end_price + (w1_length * 1.0 * direction),
                    description="Wave 5 = Wave 1 (equality)",
                    probability=0.7
                )
                
                if len(waves) >= 3 and waves[2].end_price:
                    # Minimum target: just beyond Wave 3
                    min_target = waves[2].end_price + (w1_length * 0.05 * direction)
                    wave_count.add_target(
                        price=min_target,
                        description="Minimum Wave 5 target",
                        probability=0.9
                    )