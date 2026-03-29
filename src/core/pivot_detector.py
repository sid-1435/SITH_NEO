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
        """Detect fractal high pivots"""
        highs = []
        
        for i in range(self.lookback, len(df) - self.lookahead):
            current_high = df['high'].iloc[i]
            
            # Check if current high is highest in the window
            lookback_highs = df['high'].iloc[i - self.lookback:i]
            lookahead_highs = df['high'].iloc[i + 1:i + self.lookahead + 1]
            
            if (current_high >= lookback_highs.max() and 
                current_high >= lookahead_highs.max()):
                
                highs.append({
                    'time': df.index[i],
                    'price': current_high,
                    'type': 'high',
                    'index': i
                })
        
        return highs
    
    def _detect_lows(self, df: pd.DataFrame) -> List[Dict]:
        """Detect fractal low pivots"""
        lows = []
        
        for i in range(self.lookback, len(df) - self.lookahead):
            current_low = df['low'].iloc[i]
            
            # Check if current low is lowest in the window
            lookback_lows = df['low'].iloc[i - self.lookback:i]
            lookahead_lows = df['low'].iloc[i + 1:i + self.lookahead + 1]
            
            if (current_low <= lookback_lows.min() and 
                current_low <= lookahead_lows.min()):
                
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
        """
        if len(pivots) <= 1:
            return pivots
        
        cleaned = [pivots[0]]
        
        for i in range(1, len(pivots)):
            current = pivots[i]
            previous = cleaned[-1]
            
            # If same type, keep the more extreme one
            if current['type'] == previous['type']:
                if current['type'] == 'high':
                    if current['price'] > previous['price']:
                        cleaned[-1] = current
                else:  # low
                    if current['price'] < previous['price']:
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
        """
        if len(pivots) <= 2:
            return pivots
        
        # Calculate average price for percentage calculations
        avg_price = df['close'].mean()
        min_move = avg_price * (self.min_price_move_pct / 100)
        
        filtered = [pivots[0]]
        
        for i in range(1, len(pivots)):
            current = pivots[i]
            previous = filtered[-1]
            
            price_diff = abs(current['price'] - previous['price'])
            
            # Keep pivot if it represents significant movement
            if price_diff >= min_move:
                filtered.append(current)
        
        return filtered