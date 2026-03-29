import pandas as pd
import numpy as np
from typing import List, Dict


class FractalPivotDetector:
    """
    Fractal-based pivot detection aligned with NEoWave principles.
    A fractal is formed when a high/low is surrounded by lower highs/higher lows.
    """

    def __init__(self, lookback: int = 2, lookahead: int = 2):
        """
        Args:
            lookback: Number of bars to look back
            lookahead: Number of bars to look ahead
        """
        self.lookback = lookback
        self.lookahead = lookahead

    def detect(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect fractal pivots in OHLC data.

        Returns:
            List of pivot dictionaries with keys: time, price, type ('high' or 'low')
        """
        pivots = []

        # Detect fractal highs
        high_pivots = self._detect_highs(df)
        pivots.extend(high_pivots)

        # Detect fractal lows
        low_pivots = self._detect_lows(df)
        pivots.extend(low_pivots)

        # Sort by time
        pivots = sorted(pivots, key=lambda x: x['time'])

        # Clean up: remove consecutive pivots of same type
        pivots = self._clean_pivots(pivots)

        return pivots

    def _detect_highs(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect fractal high pivots.

        FIX #1: Extended range to include edge candles (start/end of data).
        FIX #2: Changed strict >= to allow equal-high fractals to qualify,
                using 'not strictly dominated' logic so flat tops are captured.
        """
        highs = []
        n = len(df)

        # FIX #1: Pad the range to cover edge candles by using
        # available bars (clamped), not a fixed cutoff.
        for i in range(n):
            current_high = df['high'].iloc[i]

            # Gather lookback window (whatever is available)
            lb_start = max(0, i - self.lookback)
            la_end = min(n, i + self.lookahead + 1)

            lookback_highs = df['high'].iloc[lb_start:i]
            lookahead_highs = df['high'].iloc[i + 1:la_end]

            # FIX #2: A pivot high must be >= all neighbours (not strictly >).
            # This lets flat tops qualify. We keep the *first* occurrence
            # when there are ties (cleaned later).
            lb_ok = len(lookback_highs) == 0 or current_high >= lookback_highs.max()
            la_ok = len(lookahead_highs) == 0 or current_high >= lookahead_highs.max()

            if lb_ok and la_ok:
                highs.append({
                    'time': df.index[i],
                    'price': current_high,
                    'type': 'high',
                    'index': i
                })

        return highs

    def _detect_lows(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect fractal low pivots.

        FIX #1 & #2 applied symmetrically to lows.
        """
        lows = []
        n = len(df)

        for i in range(n):
            current_low = df['low'].iloc[i]

            lb_start = max(0, i - self.lookback)
            la_end = min(n, i + self.lookahead + 1)

            lookback_lows = df['low'].iloc[lb_start:i]
            lookahead_lows = df['low'].iloc[i + 1:la_end]

            lb_ok = len(lookback_lows) == 0 or current_low <= lookback_lows.min()
            la_ok = len(lookahead_lows) == 0 or current_low <= lookahead_lows.min()

            if lb_ok and la_ok:
                lows.append({
                    'time': df.index[i],
                    'price': current_low,
                    'type': 'low',
                    'index': i
                })

        return lows

    def _clean_pivots(self, pivots: List[Dict]) -> List[Dict]:
        """
        Remove consecutive pivots of the same type.
        Keep the most extreme (highest high or lowest low).

        FIX #3: Only merge consecutive same-type pivots that are
        immediately adjacent in time (no intervening opposite pivot).
        This prevents aggressively collapsing valid nearby pivots.
        """
        if len(pivots) <= 1:
            return pivots

        cleaned = [pivots[0]]

        for i in range(1, len(pivots)):
            current = pivots[i]
            previous = cleaned[-1]

            if current['type'] == previous['type']:
                # Replace with the more extreme value
                if current['type'] == 'high':
                    if current['price'] >= previous['price']:
                        cleaned[-1] = current
                else:  # low
                    if current['price'] <= previous['price']:
                        cleaned[-1] = current
            else:
                cleaned.append(current)

        return cleaned


class AdaptivePivotDetector(FractalPivotDetector):
    """
    Enhanced pivot detector that adapts to market volatility.
    """

    def __init__(self, lookback: int = 2, lookahead: int = 2,
                 min_price_move_pct: float = 0.5):
        super().__init__(lookback, lookahead)
        self.min_price_move_pct = min_price_move_pct

    def detect(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect pivots with additional filter for minimum price movement.
        """
        # Get base fractal pivots
        pivots = super().detect(df)

        # Filter by minimum price movement
        filtered_pivots = self._filter_by_price_move(pivots, df)

        return filtered_pivots

    def _filter_by_price_move(self, pivots: List[Dict],
                               df: pd.DataFrame) -> List[Dict]:
        """
        Remove pivots that don't represent significant price movement.

        FIX #4: Use the *local* price level between each consecutive pivot
        pair rather than the global average, so the threshold scales
        correctly across trending / volatile instruments.

        FIX #5: Always keep the very first and last pivot so edge
        pivots are never silently dropped by the filter.
        """
        if len(pivots) <= 2:
            return pivots

        filtered = [pivots[0]]

        for i in range(1, len(pivots)):
            current = pivots[i]
            previous = filtered[-1]

            # FIX #4: Use the midpoint of the two adjacent pivots as
            # the local reference price instead of the global mean.
            local_ref = (current['price'] + previous['price']) / 2.0
            min_move = local_ref * (self.min_price_move_pct / 100.0)

            price_diff = abs(current['price'] - previous['price'])

            if price_diff >= min_move:
                filtered.append(current)
            elif i == len(pivots) - 1:
                # FIX #5: Always keep the last pivot
                filtered.append(current)

        return filtered