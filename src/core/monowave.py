from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import numpy as np

@dataclass
class Monowave:
    """
    Represents a single monowave - the atomic unit of NEoWave analysis.
    A monowave is the price movement between two consecutive pivots.
    """
    id: int
    start_time: datetime
    end_time: datetime
    start_price: float
    end_price: float
    high_price: float
    low_price: float
    
    # NEoWave specific
    high_first: bool  # Did high occur before low in this segment?
    
    # Derived properties
    @property
    def direction(self) -> str:
        """Returns 'up' or 'down'"""
        return 'up' if self.end_price > self.start_price else 'down'
    
    @property
    def price_movement(self) -> float:
        """Net price change"""
        return self.end_price - self.start_price
    
    @property
    def price_range(self) -> float:
        """Total price range (high - low)"""
        return self.high_price - self.low_price
    
    @property
    def time_duration(self) -> int:
        """Duration in number of periods"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def slope(self) -> float:
        """Price change per unit time"""
        duration = self.time_duration
        return self.price_movement / duration if duration > 0 else 0
    
    def retracement_of(self, previous: 'Monowave') -> float:
        """
        Calculate what % of the previous monowave this one retraces.
        Returns value between 0 and 1+ (can exceed 1 in running corrections)
        """
        if previous.price_movement == 0:
            return 0
        return abs(self.price_movement) / abs(previous.price_movement)
    
    def extension_of(self, reference: 'Monowave') -> float:
        """
        Calculate Fibonacci extension ratio relative to reference wave.
        """
        if reference.price_movement == 0:
            return 0
        return abs(self.price_movement) / abs(reference.price_movement)
    
    def time_ratio_to(self, reference: 'Monowave') -> float:
        """
        Calculate time duration ratio relative to reference wave.
        """
        ref_duration = reference.time_duration
        return self.time_duration / ref_duration if ref_duration > 0 else 0
    
    def __repr__(self):
        return (f"Monowave({self.id}: {self.direction}, "
                f"${self.start_price:.2f}→${self.end_price:.2f}, "
                f"{self.time_duration}s)")


class MonowaveConstructor:
    """
    Constructs monowaves from OHLC data and pivot points.
    """
    
    def __init__(self, df, pivots):
        """
        Args:
            df: DataFrame with OHLC data
            pivots: List of pivot points (datetime, price, type)
        """
        self.df = df
        self.pivots = sorted(pivots, key=lambda x: x['time'])
        
    def construct(self) -> List[Monowave]:
        """
        Build monowave sequence from pivots.
        """
        monowaves = []
        
        for i in range(len(self.pivots) - 1):
            pivot_start = self.pivots[i]
            pivot_end = self.pivots[i + 1]
            
            # Get data slice between pivots
            mask = (self.df.index >= pivot_start['time']) & \
                   (self.df.index <= pivot_end['time'])
            segment = self.df[mask]
            
            if len(segment) == 0:
                continue
            
            # Determine if high came first
            high_first = self._determine_high_first(segment, pivot_start, pivot_end)
            
            monowave = Monowave(
                id=i,
                start_time=pivot_start['time'],
                end_time=pivot_end['time'],
                start_price=pivot_start['price'],
                end_price=pivot_end['price'],
                high_price=segment['high'].max(),
                low_price=segment['low'].min(),
                high_first=high_first
            )
            
            monowaves.append(monowave)
        
        return monowaves
    
    def _determine_high_first(self, segment, pivot_start, pivot_end) -> bool:
        """
        Determine whether high or low occurred first in the segment.
        Uses heuristic based on candle direction when tick data unavailable.
        """
        if len(segment) == 0:
            return True
        
        first_candle = segment.iloc[0]
        
        # Heuristic: if bullish candle, assume high came after open
        # if bearish candle, assume low came after open
        if first_candle['close'] > first_candle['open']:
            # Bullish - high likely came first
            return True
        elif first_candle['close'] < first_candle['open']:
            # Bearish - low likely came first
            return False
        else:
            # Doji - use previous trend or default to True
            if len(segment) > 1:
                return segment.iloc[1]['close'] > segment.iloc[1]['open']
            return True