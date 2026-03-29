import os
import pandas as pd
from typing import List, Dict
from pathlib import Path

class TickerManager:
    """
    Manages ticker symbols loaded from CSV files.
    """
    
    def __init__(self, tickers_folder: str = "tickers"):
        self.tickers_folder = Path(tickers_folder)
        self._ensure_folder_exists()
    
    def _ensure_folder_exists(self):
        """Create tickers folder if it doesn't exist"""
        self.tickers_folder.mkdir(exist_ok=True)
        
        # Create sample CSV files if they don't exist
        sample_files = {
            'stocks.csv': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'AMZN'],
            'crypto.csv': ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'ADA-USD'],
            'forex.csv': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X']
        }
        
        for filename, symbols in sample_files.items():
            filepath = self.tickers_folder / filename
            if not filepath.exists():
                pd.DataFrame({'symbol': symbols}).to_csv(filepath, index=False)
    
    def get_available_files(self) -> List[str]:
        """Get list of available ticker CSV files"""
        csv_files = list(self.tickers_folder.glob("*.csv"))
        return [f.stem for f in csv_files]  # Return without .csv extension
    
    def load_tickers(self, filename: str) -> List[str]:
        """
        Load ticker symbols from a CSV file.
        
        Args:
            filename: Name of CSV file (with or without .csv extension)
        
        Returns:
            List of ticker symbols
        """
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = self.tickers_folder / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Ticker file not found: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            
            # Try to find symbol column (case-insensitive)
            symbol_col = None
            for col in df.columns:
                if col.lower() in ['symbol', 'ticker', 'symbols', 'tickers']:
                    symbol_col = col
                    break
            
            if symbol_col is None:
                # If no header found, assume first column or single column
                symbol_col = df.columns[0]
            
            symbols = df[symbol_col].dropna().astype(str).str.strip().tolist()
            return [s for s in symbols if s]  # Remove empty strings
            
        except Exception as e:
            raise ValueError(f"Error reading ticker file {filename}: {str(e)}")
    
    def add_ticker(self, filename: str, symbol: str):
        """Add a ticker to a CSV file"""
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = self.tickers_folder / filename
        
        # Load existing or create new
        if filepath.exists():
            df = pd.read_csv(filepath)
            if symbol not in df['symbol'].values:
                df = pd.concat([df, pd.DataFrame({'symbol': [symbol]})], ignore_index=True)
        else:
            df = pd.DataFrame({'symbol': [symbol]})
        
        df.to_csv(filepath, index=False)
    
    def remove_ticker(self, filename: str, symbol: str):
        """Remove a ticker from a CSV file"""
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = self.tickers_folder / filename
        
        if filepath.exists():
            df = pd.read_csv(filepath)
            df = df[df['symbol'] != symbol]
            df.to_csv(filepath, index=False)