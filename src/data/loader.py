import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
import streamlit as st

class DataLoader:
    """
    Handles fetching OHLC data from yfinance.
    """
    
    TIMEFRAME_MAPPING = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '4h': '4h',
        '1d': '1d',
        '1wk': '1wk',
        '1mo': '1mo'
    }
    
    @staticmethod
    def fetch_data(symbol: str, 
                   timeframe: str, 
                   period: str = "1y") -> pd.DataFrame:
        """
        Fetch OHLC data from yfinance.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
            timeframe: Interval (e.g., '1h', '1d', '1wk')
            period: Data period (e.g., '1mo', '6mo', '1y', '5y', 'max')
        
        Returns:
            DataFrame with OHLC data
        """
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Map timeframe
            interval = DataLoader.TIMEFRAME_MAPPING.get(timeframe, timeframe)
            
            # Fetch historical data
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                raise ValueError(f"No data retrieved for {symbol}")
            
            # Rename columns to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Ensure required columns exist
            required = ['open', 'high', 'low', 'close']
            for col in required:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Add volume if missing
            if 'volume' not in df.columns:
                df['volume'] = 0
            
            # Add derived columns for NEoWave
            df['high_first'] = df['close'] >= df['open']
            df['low_first'] = df['close'] < df['open']
            df['range'] = df['high'] - df['low']
            df['body'] = abs(df['close'] - df['open'])
            df['direction'] = df['close'] > df['open']
            
            # Clean data
            df = df.dropna(subset=['open', 'high', 'low', 'close'])
            
            return df
            
        except Exception as e:
            raise Exception(f"Error fetching data for {symbol}: {str(e)}")
    
    @staticmethod
    def get_symbol_info(symbol: str) -> dict:
        """Get basic information about a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('shortName', info.get('longName', symbol)),
                'exchange': info.get('exchange', 'Unknown'),
                'currency': info.get('currency', 'USD'),
                'type': info.get('quoteType', 'Unknown')
            }
        except:
            return {
                'symbol': symbol,
                'name': symbol,
                'exchange': 'Unknown',
                'currency': 'USD',
                'type': 'Unknown'
            }