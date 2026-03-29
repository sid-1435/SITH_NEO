#!/usr/bin/env python
"""
Run script for NEoWave Analyzer
"""

import subprocess
import sys
import os

def main():
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--theme.base=dark",
        "--theme.primaryColor=#58a6ff",
        "--theme.backgroundColor=#0d1117",
        "--theme.secondaryBackgroundColor=#161b22",
        "--theme.textColor=#c9d1d9"
    ])

if __name__ == "__main__":
    main()