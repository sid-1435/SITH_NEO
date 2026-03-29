"""
Multi-Degree Pivot Detection and Hierarchical Wave Building
With integrated pattern validation.

ARCHITECTURE FIX:
The previous version detected pivots at all three degrees independently on
the full dataset, then tried to build patterns from ALL of them at once.
This caused every monowave to be labelled at the same level (A-I repeatedly)
because there was no true hierarchy — subwaves were never actually nested
inside parent waves.

Correct approach (top-down):
  1. Detect PRIMARY pivots (coarsest, fewest points) on the full df.
  2. Build Primary-level wave patterns from those pivots.
  3. For EACH Primary wave, slice df to its time window, detect
     INTERMEDIATE pivots inside that slice, build Intermediate sub-waves.
  4. For EACH Intermediate wave, repeat for MINOR degree.

This guarantees sub-waves are always contained within their parent wave,
and labels reset correctly for each parent segment.
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


# ---------------------------------------------------------------------------
# Pivot detection
# ---------------------------------------------------------------------------

class MultiDegreePivotDetector:
    """
    Detects pivots at multiple degree levels.
    Primary uses the coarsest (largest lookback/min-move) settings.
    Each successive degree is finer.
    """

    def __init__(self, degrees: List[WaveDegree] = None):
        self.degrees = degrees or [
            WaveDegree.PRIMARY,
            WaveDegree.INTERMEDIATE,
            WaveDegree.MINOR
        ]

    def detect_all(self, df: pd.DataFrame) -> Dict[WaveDegree, List[Dict]]:
        """Detect pivots at all configured degree levels on the full dataset."""
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
            for p in pivots:
                p['degree'] = degree
            results[degree] = pivots
        return results

    def detect_for_degree(self, df: pd.DataFrame,
                           degree: WaveDegree) -> List[Dict]:
        """Detect pivots for a single degree on a (possibly sliced) DataFrame."""
        config = DEGREE_CONFIGS.get(degree)
        if not config:
            return []
        detector = AdaptivePivotDetector(
            lookback=config.lookback,
            lookahead=config.lookahead,
            min_price_move_pct=config.min_price_move_pct
        )
        pivots = detector.detect(df)
        for p in pivots:
            p['degree'] = degree
        return pivots


# ---------------------------------------------------------------------------
# Wave validation
# ---------------------------------------------------------------------------

class WaveValidator:
    """
    Validates wave structures against Elliott Wave / NEoWave rules.
    """

    @staticmethod
    def validate_wave_structure(waves: List[HierarchicalWave],
                                 pattern_type: str = 'impulse'
                                 ) -> Tuple[bool, List[str], float]:
        violations = []
        confidence = 100.0

        if len(waves) < 2:
            return True, [], confidence

        is_uptrend = WaveValidator._is_uptrend(waves)

        if len(waves) >= 2:
            valid, msg = WaveValidator._check_wave2_origin(waves, is_uptrend)
            if not valid:
                return False, [f"CRITICAL: {msg}"], 0.0

        if len(waves) >= 4:
            valid, msg = WaveValidator._check_wave4_origin(waves, is_uptrend)
            if not valid:
                return False, [f"CRITICAL: {msg}"], 0.0

        if len(waves) >= 3:
            valid, msg = WaveValidator._check_wave3_exceeds_wave1(waves, is_uptrend)
            if not valid:
                return False, [f"CRITICAL: {msg}"], 0.0

        if len(waves) >= 5:
            valid, msg = WaveValidator._check_wave5_exceeds_wave3(waves, is_uptrend)
            if not valid:
                violations.append(f"WARNING: {msg}")
                confidence -= 30

        if len(waves) >= 5 and pattern_type == 'impulse':
            valid, msg = WaveValidator._check_wave3_not_shortest(waves)
            if not valid:
                return False, [f"CRITICAL: {msg}"], 0.0

        if len(waves) >= 4:
            has_overlap = WaveValidator._check_wave4_wave1_overlap(waves, is_uptrend)
            if pattern_type == 'impulse' and has_overlap:
                return False, ["CRITICAL: Wave 4 overlaps Wave 1"], 0.0
            elif pattern_type == 'diagonal' and not has_overlap:
                violations.append("WARNING: Wave 4 should overlap Wave 1 in diagonal")
                confidence -= 20

        return True, violations, max(0.0, confidence)

    @staticmethod
    def _is_uptrend(waves):
        if not waves:
            return True
        w = waves[0]
        if w.start_price is None or w.end_price is None:
            return True
        return w.end_price > w.start_price

    @staticmethod
    def _check_wave2_origin(waves, is_uptrend):
        w1, w2 = waves[0], waves[1]
        if w1.start_price is None:
            return True, ""
        if is_uptrend:
            extreme = w2.low_price if w2.low_price else w2.end_price
            if extreme and extreme < w1.start_price:
                return False, f"Wave 2 low ({extreme:.2f}) below Wave 1 origin ({w1.start_price:.2f})"
        else:
            extreme = w2.high_price if w2.high_price else w2.end_price
            if extreme and extreme > w1.start_price:
                return False, f"Wave 2 high ({extreme:.2f}) above Wave 1 origin ({w1.start_price:.2f})"
        return True, ""

    @staticmethod
    def _check_wave4_origin(waves, is_uptrend):
        w3, w4 = waves[2], waves[3]
        if w3.start_price is None:
            return True, ""
        if is_uptrend:
            extreme = w4.low_price if w4.low_price else w4.end_price
            if extreme and extreme < w3.start_price:
                return False, f"Wave 4 low ({extreme:.2f}) below Wave 3 origin ({w3.start_price:.2f})"
        else:
            extreme = w4.high_price if w4.high_price else w4.end_price
            if extreme and extreme > w3.start_price:
                return False, f"Wave 4 high ({extreme:.2f}) above Wave 3 origin ({w3.start_price:.2f})"
        return True, ""

    @staticmethod
    def _check_wave3_exceeds_wave1(waves, is_uptrend):
        w1, w3 = waves[0], waves[2]
        if w1.end_price is None or w3.end_price is None:
            return True, ""
        if is_uptrend and w3.end_price <= w1.end_price:
            return False, f"Wave 3 ({w3.end_price:.2f}) did not exceed Wave 1 ({w1.end_price:.2f})"
        if not is_uptrend and w3.end_price >= w1.end_price:
            return False, f"Wave 3 ({w3.end_price:.2f}) did not exceed Wave 1 ({w1.end_price:.2f})"
        return True, ""

    @staticmethod
    def _check_wave5_exceeds_wave3(waves, is_uptrend):
        w3, w5 = waves[2], waves[4]
        if w3.end_price is None or w5.end_price is None:
            return True, ""
        if is_uptrend and w5.end_price <= w3.end_price:
            return False, "Wave 5 did not exceed Wave 3"
        if not is_uptrend and w5.end_price >= w3.end_price:
            return False, "Wave 5 did not exceed Wave 3"
        return True, ""

    @staticmethod
    def _check_wave3_not_shortest(waves):
        w1 = abs(waves[0].price_movement) if waves[0].price_movement else 0
        w3 = abs(waves[2].price_movement) if waves[2].price_movement else 0
        w5 = abs(waves[4].price_movement) if waves[4].price_movement else 0
        if w3 < w1 and w3 < w5:
            return False, f"Wave 3 ({w3:.2f}) is shortest motive wave"
        return True, ""

    @staticmethod
    def _check_wave4_wave1_overlap(waves, is_uptrend):
        w1, w4 = waves[0], waves[3]
        w1h = w1.high_price or max(w1.start_price or 0, w1.end_price or 0)
        w1l = w1.low_price or min(w1.start_price or float('inf'), w1.end_price or float('inf'))
        w4h = w4.high_price or max(w4.start_price or 0, w4.end_price or 0)
        w4l = w4.low_price or min(w4.start_price or float('inf'), w4.end_price or float('inf'))
        return w4l < w1h if is_uptrend else w4h > w1l


# ---------------------------------------------------------------------------
# Hierarchical wave builder  (top-down — the core architectural fix)
# ---------------------------------------------------------------------------

class HierarchicalWaveBuilder:
    """
    Builds hierarchical wave structure correctly, top-down:

      PRIMARY   → detected on full dataset (coarse pivots)
      INTERMEDIATE → detected inside each Primary wave's time window
      MINOR        → detected inside each Intermediate wave's time window

    This is the correct NEoWave methodology. Each sub-degree wave is a
    subdivision of its parent, not an independent scan of the full chart.
    """

    def __init__(self, degrees: List[WaveDegree] = None):
        self.degrees = degrees or [
            WaveDegree.PRIMARY,
            WaveDegree.INTERMEDIATE,
            WaveDegree.MINOR
        ]
        self.wave_id_counter = 0
        self.validator = WaveValidator()
        self._detector = MultiDegreePivotDetector(degrees=self.degrees)

    def _next_id(self) -> int:
        self.wave_id_counter += 1
        return self.wave_id_counter

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def build(self,
              df: pd.DataFrame,
              multi_degree_pivots: Dict[WaveDegree, List[Dict]]
              ) -> Optional[HierarchicalWaveCount]:
        """
        Build the full hierarchical wave structure top-down.
        """
        self.wave_id_counter = 0

        primary_degree = self.degrees[0] if self.degrees else WaveDegree.PRIMARY
        primary_pivots = multi_degree_pivots.get(primary_degree, [])

        if len(primary_pivots) < 3:
            return None

        # Step 1: find all valid Primary-level patterns across the full chart
        primary_segments = self._find_all_valid_patterns(
            df=df,
            pivots=primary_pivots,
            degree=primary_degree
        )

        if not primary_segments:
            return self._create_developing_pattern(df, primary_pivots, primary_degree)

        # Step 2 & 3: for each Primary wave, drill down into sub-degrees
        all_primary_waves: List[HierarchicalWave] = []
        all_violations: List[str] = []
        total_confidence = 0.0

        for waves, confidence, violations in primary_segments:
            for wave in waves:
                # Detect Intermediate (and then Minor) pivots INSIDE this wave
                self._build_subwaves_topdown(df, wave, degree_index=0)

            all_primary_waves.extend(waves)
            all_violations.extend(violations)
            total_confidence += confidence

        avg_confidence = total_confidence / len(primary_segments)
        best_waves = max(primary_segments, key=lambda x: x[1])[0]
        pattern_name, pattern_conf = self._identify_pattern(best_waves)
        final_confidence = avg_confidence * 0.7 + pattern_conf * 0.3

        degree_confidence = self._calculate_degree_confidence(all_primary_waves)

        wave_count_obj = HierarchicalWaveCount(
            primary_waves=all_primary_waves,
            pattern_name=pattern_name,
            confidence=final_confidence,
            description=self._generate_description(
                all_primary_waves, pattern_name, all_violations
            ),
            degrees_analyzed=self.degrees,
            degree_confidence=degree_confidence
        )

        for v in all_violations:
            wave_count_obj.warnings.append(v)

        self._calculate_targets(wave_count_obj)
        return wave_count_obj

    # ------------------------------------------------------------------
    # Top-down subdivision builder
    # ------------------------------------------------------------------

    def _build_subwaves_topdown(self,
                                 df: pd.DataFrame,
                                 parent_wave: HierarchicalWave,
                                 degree_index: int) -> None:
        """
        Recursively build sub-waves inside a parent wave by:
          1. Slicing df to the parent's exact time window.
          2. Re-detecting pivots at the child degree on that slice only.
          3. Finding valid sub-patterns within the slice.
          4. Recursing into each sub-wave for the next finer degree.

        This ensures sub-waves are always physically contained within
        their parent and labels are assigned independently per parent.
        """
        if degree_index >= len(self.degrees) - 1:
            return

        child_degree = self.degrees[degree_index + 1]
        child_config = DEGREE_CONFIGS.get(child_degree)
        if not child_config:
            return

        # Slice OHLC to parent wave's window
        mask = (df.index >= parent_wave.start_time) & (df.index <= parent_wave.end_time)
        segment_df = df[mask]

        min_bars = child_config.lookback + child_config.lookahead + 3
        if len(segment_df) < min_bars:
            return

        # Detect child-degree pivots within this slice
        child_pivots = self._detector.detect_for_degree(segment_df, child_degree)

        if len(child_pivots) < 2:
            return

        # Anchor to parent boundaries
        child_pivots = self._anchor_to_parent(child_pivots, parent_wave, child_degree)

        if len(child_pivots) < 3:
            return

        # Find valid sub-patterns
        sub_segments = self._find_all_valid_patterns(
            df=segment_df,
            pivots=child_pivots,
            degree=child_degree
        )

        if not sub_segments:
            # No valid Elliott pattern — store raw waves for visibility
            raw_waves = self._build_waves_from_pivots(segment_df, child_pivots, child_degree)
            if raw_waves:
                for w in raw_waves:
                    w.parent = parent_wave
                parent_wave.sub_waves = raw_waves
                parent_wave.subdivision_confidence = 30.0
            return

        sub_waves: List[HierarchicalWave] = []
        total_conf = 0.0
        for waves, conf, _ in sub_segments:
            sub_waves.extend(waves)
            total_conf += conf

        for w in sub_waves:
            w.parent = parent_wave

        parent_wave.sub_waves = sub_waves
        parent_wave.subdivision_confidence = total_conf / len(sub_segments)

        # Recurse into each sub-wave
        for sub_wave in sub_waves:
            self._build_subwaves_topdown(df, sub_wave, degree_index + 1)

    def _anchor_to_parent(self,
                           pivots: List[Dict],
                           parent_wave: HierarchicalWave,
                           degree: WaveDegree) -> List[Dict]:
        """
        Ensure the parent wave's start and end prices appear in the pivot
        list so sub-waves are anchored to the parent wave boundaries.
        """
        tolerance = 3600  # 1 hour in seconds

        has_start = any(
            abs((p['time'] - parent_wave.start_time).total_seconds()) < tolerance
            for p in pivots
        )
        has_end = any(
            abs((p['time'] - parent_wave.end_time).total_seconds()) < tolerance
            for p in pivots
        )

        result = list(pivots)

        if not has_start:
            result.insert(0, {
                'time': parent_wave.start_time,
                'price': parent_wave.start_price,
                'type': 'high' if parent_wave.price_movement < 0 else 'low',
                'degree': degree,
                'index': -1
            })

        if not has_end:
            result.append({
                'time': parent_wave.end_time,
                'price': parent_wave.end_price,
                'type': 'low' if parent_wave.price_movement < 0 else 'high',
                'degree': degree,
                'index': -1
            })

        return sorted(result, key=lambda p: p['time'])

    # ------------------------------------------------------------------
    # Greedy pattern finder
    # ------------------------------------------------------------------

    def _find_all_valid_patterns(self,
                                  df: pd.DataFrame,
                                  pivots: List[Dict],
                                  degree: WaveDegree
                                  ) -> List[Tuple[List[HierarchicalWave], float, List[str]]]:
        """
        Greedy left-to-right scan. At each position try 9→7→5→3 wave patterns.
        When a valid one is found, advance past it (sharing last pivot as next start).
        Returns list of (waves, confidence, violations).
        """
        results = []
        start_idx = 0

        while start_idx < len(pivots):
            best = None  # (size, end_idx, waves, confidence, violations)

            for wave_count in [9, 7, 5, 3]:
                end_idx = start_idx + wave_count + 1
                if end_idx > len(pivots):
                    continue

                subset = pivots[start_idx:end_idx]
                waves = self._build_waves_from_pivots(df, subset, degree)
                if not waves:
                    continue

                ptype = 'impulse' if len(waves) == 5 else 'corrective'
                is_valid, violations, confidence = self.validator.validate_wave_structure(
                    waves, pattern_type=ptype
                )

                if not is_valid or confidence == 0:
                    continue

                if best is None or wave_count > best[0]:
                    best = (wave_count, end_idx, waves, confidence, violations)

            if best is not None:
                _, end_idx, waves, confidence, violations = best
                results.append((waves, confidence, violations))
                start_idx = end_idx - 1  # Share last pivot as next start
            else:
                start_idx += 1

        return results

    # ------------------------------------------------------------------
    # Wave construction (FIXED)
    # ------------------------------------------------------------------

    def _build_waves_from_pivots(self,
                                  df: pd.DataFrame,
                                  pivots: List[Dict],
                                  degree: WaveDegree) -> List[HierarchicalWave]:
        """Convert a list of pivots into HierarchicalWave objects."""
        if len(pivots) < 2:
            return []

        config = DEGREE_CONFIGS.get(degree)
        sorted_pivots = sorted(pivots, key=lambda p: p['time'])
        num_waves = len(sorted_pivots) - 1

        # FIX: Check exact counts first to avoid mislabeling
        if num_waves == 9:
            labels = (config.labels_corrective[:9]
                      if len(config.labels_corrective) >= 9
                      else ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'])
            wave_types = [
                WaveType.MOTIVE if i % 2 == 0 else WaveType.CORRECTIVE
                for i in range(9)
            ]
        elif num_waves == 7:
            labels = (config.labels_corrective[:7]
                      if len(config.labels_corrective) >= 7
                      else ['A', 'B', 'C', 'D', 'E', 'F', 'G'])
            wave_types = [
                WaveType.MOTIVE if i % 2 == 0 else WaveType.CORRECTIVE
                for i in range(7)
            ]
        elif num_waves == 5:  # CHANGED: exact match, not >=
            labels = config.labels_motive[:5]
            wave_types = [
                WaveType.MOTIVE, WaveType.CORRECTIVE, WaveType.MOTIVE,
                WaveType.CORRECTIVE, WaveType.MOTIVE
            ]
        elif num_waves == 3:  # CHANGED: exact match, not >=
            labels = config.labels_corrective[:3]
            wave_types = [WaveType.MOTIVE, WaveType.CORRECTIVE, WaveType.MOTIVE]
        else:
            # Fallback for any other count (1, 2, 4, 6, 8, 10+)
            # Use motive labels and alternate types
            labels = (config.labels_motive[:num_waves] 
                      if num_waves <= len(config.labels_motive)
                      else [f"W{i+1}" for i in range(num_waves)])
            wave_types = [
                WaveType.MOTIVE if i % 2 == 0 else WaveType.CORRECTIVE
                for i in range(num_waves)
            ]

        waves = []
        for i in range(min(num_waves, len(labels))):
            sp = sorted_pivots[i]
            ep = sorted_pivots[i + 1]

            mask = (df.index >= sp['time']) & (df.index <= ep['time'])
            seg = df[mask]

            high_price = seg['high'].max() if len(seg) > 0 else max(sp['price'], ep['price'])
            low_price = seg['low'].min() if len(seg) > 0 else min(sp['price'], ep['price'])

            wave = HierarchicalWave(
                id=self._next_id(),
                label=labels[i],
                degree=degree,
                wave_type=wave_types[i] if i < len(wave_types) else WaveType.MOTIVE,
                start_time=sp['time'],
                end_time=ep['time'],
                start_price=sp['price'],
                end_price=ep['price'],
                high_price=high_price,
                low_price=low_price
            )
            waves.append(wave)

        return waves

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _create_developing_pattern(self,
                                    df: pd.DataFrame,
                                    pivots: List[Dict],
                                    degree: WaveDegree) -> Optional[HierarchicalWaveCount]:
        if len(pivots) < 3:
            return None
        recent = pivots[-6:] if len(pivots) >= 6 else pivots
        waves = self._build_waves_from_pivots(df, recent, degree)
        if not waves:
            return None
        return HierarchicalWaveCount(
            primary_waves=waves,
            pattern_name="Developing",
            confidence=25.0,
            description="No complete valid pattern found. Wave structure is still developing.",
            degrees_analyzed=self.degrees,
            degree_confidence={d.name: 0.0 for d in self.degrees}
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _identify_pattern(self, waves: List[HierarchicalWave]) -> Tuple[str, float]:
        n = len(waves)
        if n == 5:
            return ("Diagonal", 70.0) if self._has_wave4_overlap(waves) else ("Impulse", 85.0)
        elif n == 3:
            return ("Zigzag", 80.0) if self._is_zigzag(waves) else ("Flat", 75.0)
        elif n == 7:
            return "Diametric", 70.0
        elif n == 9:
            return "Symmetrical", 65.0
        return "Developing", 40.0

    def _has_wave4_overlap(self, waves):
        if len(waves) < 4:
            return False
        w1, w4 = waves[0], waves[3]
        r1 = (min(w1.start_price or 0, w1.end_price or 0),
               max(w1.start_price or 0, w1.end_price or 0))
        r4 = (min(w4.start_price or 0, w4.end_price or 0),
               max(w4.start_price or 0, w4.end_price or 0))
        return not (r4[0] > r1[1] or r4[1] < r1[0])

    def _is_zigzag(self, waves):
        if len(waves) != 3:
            return False
        a = abs(waves[0].price_movement) if waves[0].price_movement else 0
        b = abs(waves[1].price_movement) if waves[1].price_movement else 0
        if a == 0:
            return False
        return 0.3 <= (b / a) <= 0.85

    def _calculate_degree_confidence(self,
                                      waves: List[HierarchicalWave]) -> Dict[str, float]:
        confidence = {}
        for degree in self.degrees:
            collected: List[HierarchicalWave] = []

            def collect(wave: HierarchicalWave, target=degree, out=collected):
                if wave.degree == target:
                    out.append(wave)
                for sub in wave.sub_waves:
                    collect(sub, target, out)

            for w in waves:
                collect(w)

            confidence[degree.name] = (
                float(np.mean([w.subdivision_confidence for w in collected]))
                if collected else 0.0
            )
        return confidence

    def _generate_description(self, waves, pattern_name, violations):
        labels = " → ".join(w.label for w in waves)
        desc = f"{pattern_name} pattern: {labels}"
        if violations:
            desc += f". Issues: {len(violations)}"
        return desc

    def _calculate_targets(self, wave_count: HierarchicalWaveCount) -> None:
        waves = wave_count.primary_waves
        if not waves:
            return

        is_uptrend = (
            waves[0].end_price > waves[0].start_price
            if waves[0].start_price and waves[0].end_price else True
        )

        if len(waves) >= 4:
            w1, w4 = waves[0], waves[3]
            if w1.price_movement and w4.end_price:
                length = abs(w1.price_movement)
                direction = 1 if is_uptrend else -1
                wave_count.add_target(
                    price=w4.end_price + length * 0.618 * direction,
                    description="Wave 5 = 0.618 × Wave 1",
                    probability=0.6
                )
                wave_count.add_target(
                    price=w4.end_price + length * 1.0 * direction,
                    description="Wave 5 = Wave 1 (equality)",
                    probability=0.7
                )
                if len(waves) >= 3 and waves[2].end_price:
                    wave_count.add_target(
                        price=waves[2].end_price + length * 0.05 * direction,
                        description="Minimum Wave 5 target",
                        probability=0.9
                    )