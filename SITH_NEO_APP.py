"""
NEoWave Analysis Platform
Professional Elliott Wave Analysis Tool based on Glenn Neely's NEoWave methodology.

Features:
- Multi-degree wave analysis (Primary, Intermediate, Minor)
- Hierarchical wave structure with subdivisions
- Professional dark theme UI
- Interactive charting with Plotly

Author: NEoWave Team
Version: 2.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from src.data.ticker_manager import TickerManager
from src.data.loader import DataLoader
from src.analysis.automated import AutomatedAnalyzer
from src.analysis.semi_manual import SemiManualAnalyzer
from src.visualization.chart import ChartRenderer
from src.core.wave_degree import WaveDegree, DEGREE_CONFIGS


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="NEoWave Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# CUSTOM CSS - PROFESSIONAL DARK THEME
# ============================================================================

def load_custom_css() -> None:
    """Load custom CSS for professional dark theme."""
    st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
            border-right: 1px solid #30363d;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #c9d1d9;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #58a6ff !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        h1 {
            background: linear-gradient(90deg, #58a6ff, #a371f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }
        
        /* Text */
        p, span, label, .stMarkdown {
            color: #c9d1d9 !important;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #58a6ff !important;
            font-size: 1.8rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #8b949e !important;
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > div,
        .stNumberInput > div > div > input {
            background-color: #21262d !important;
            border: 1px solid #30363d !important;
            color: #c9d1d9 !important;
            border-radius: 6px;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            color: white !important;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
            transform: translateY(-1px);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #161b22;
            border-radius: 8px;
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: #8b949e;
            border-radius: 6px;
        }
        
        .stTabs [aria-selected="true"] {
            background: #21262d;
            color: #58a6ff;
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #c9d1d9 !important;
        }
        
        /* Slider */
        .stSlider > div > div > div > div {
            background: #58a6ff;
        }
        
        /* Checkboxes */
        .stCheckbox > label > span {
            color: #c9d1d9 !important;
        }
        
        /* Radio */
        .stRadio > div {
            background: transparent;
        }
        
        /* Dividers */
        hr {
            border-color: #30363d;
        }
        
        /* Dataframes */
        .dataframe {
            background: #21262d !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #161b22;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #484f58;
        }
        
        /* Success/Error/Warning messages */
        .stSuccess {
            background-color: rgba(46, 160, 67, 0.1) !important;
            border: 1px solid #2ea043 !important;
        }
        
        .stError {
            background-color: rgba(248, 81, 73, 0.1) !important;
            border: 1px solid #f85149 !important;
        }
        
        .stWarning {
            background-color: rgba(210, 153, 34, 0.1) !important;
            border: 1px solid #d29922 !important;
        }
        
        .stInfo {
            background-color: rgba(88, 166, 255, 0.1) !important;
            border: 1px solid #58a6ff !important;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom pattern card */
        .pattern-card {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        }
        
        /* Target card */
        .target-card {
            background: linear-gradient(135deg, #21262d 0%, #161b22 100%);
            border: 1px solid #30363d;
            border-left: 4px solid #58a6ff;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
        }
        
        /* Degree indicators */
        .degree-primary {
            color: #58a6ff !important;
            font-weight: bold;
        }
        
        .degree-intermediate {
            color: #3fb950 !important;
        }
        
        .degree-minor {
            color: #d29922 !important;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# TIMEFRAME CONFIGURATION
# ============================================================================

TIMEFRAMES: Dict[str, Dict[str, str]] = {
    "15 Minutes": {"interval": "15m", "period": "5d", "description": "Intraday"},
    "1 Hour": {"interval": "1h", "period": "1mo", "description": "Short-term"},
    "1 Day": {"interval": "1d", "period": "1y", "description": "Daily"},
    "1 Week": {"interval": "1wk", "period": "5y", "description": "Weekly"},
    "1 Month": {"interval": "1mo", "period": "max", "description": "Monthly"}
}


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state() -> None:
    """Initialize all session state variables."""
    defaults = {
        'ticker_manager': None,
        'all_symbols': None,
        'selected_symbol': None,
        'current_data': None,
        'analysis_result': None,
        'semi_manual_analyzer': None,
        'user_pivots': [],
        'analysis_run': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            if key == 'ticker_manager':
                st.session_state[key] = TickerManager()
            elif key == 'all_symbols':
                st.session_state[key] = load_all_symbols()
            elif key == 'semi_manual_analyzer':
                st.session_state[key] = SemiManualAnalyzer()
            else:
                st.session_state[key] = default_value


def load_all_symbols() -> List[str]:
    """Load all symbols from all ticker files."""
    try:
        ticker_manager = TickerManager()
        all_symbols = []
        
        for file in ticker_manager.get_available_files():
            try:
                symbols = ticker_manager.load_tickers(file)
                all_symbols.extend(symbols)
            except Exception:
                pass
        
        return sorted(list(set(all_symbols)))
    except Exception:
        # Fallback symbols if loading fails
        return ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "BTC-USD", "ETH-USD"]


# ============================================================================
# SYMBOL INPUT COMPONENT
# ============================================================================

def render_symbol_input(all_symbols: List[str]) -> Optional[str]:
    """
    Render symbol input with autocomplete-like functionality.
    
    Args:
        all_symbols: List of available symbols
    
    Returns:
        Selected symbol or None
    """
    # Text input for filtering
    search_term = st.text_input(
        "🔍 Search Symbol",
        placeholder="Type to search (e.g., AAPL, BTC)",
        key="symbol_search",
        help="Enter a ticker symbol. Type to filter the list below."
    )
    
    # Filter symbols based on search
    if search_term:
        search_upper = search_term.upper().strip()
        filtered_symbols = [s for s in all_symbols if search_upper in s.upper()]
        
        # Sort: exact match first, then starts with, then contains
        exact = [s for s in filtered_symbols if s.upper() == search_upper]
        starts = [s for s in filtered_symbols if s.upper().startswith(search_upper) and s not in exact]
        contains = [s for s in filtered_symbols if s not in exact and s not in starts]
        filtered_symbols = exact + starts + contains
        
        # Limit display
        filtered_symbols = filtered_symbols[:20]
    else:
        filtered_symbols = all_symbols[:20]
    
    # Add custom symbol option if not in list
    if search_term and search_term.upper() not in [s.upper() for s in filtered_symbols]:
        filtered_symbols = [search_term.upper()] + filtered_symbols
    
    # Selectbox for final selection
    if filtered_symbols:
        selected = st.selectbox(
            "Select Symbol",
            options=filtered_symbols,
            index=0,
            key="symbol_select",
            help="Select from filtered symbols or type a custom symbol above."
        )
        return selected
    else:
        st.warning("No matching symbols found. Enter a valid ticker symbol.")
        return search_term.upper() if search_term else None


# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_market_data(symbol: str, timeframe_config: Dict[str, str]) -> Optional[pd.DataFrame]:
    """
    Fetch market data with error handling.
    
    Args:
        symbol: Ticker symbol
        timeframe_config: Timeframe configuration dictionary
    
    Returns:
        DataFrame with OHLC data or None
    """
    try:
        df = DataLoader.fetch_data(
            symbol=symbol,
            timeframe=timeframe_config['interval'],
            period=timeframe_config['period']
        )
        return df
    except Exception as e:
        st.error(f"❌ Error fetching data: {str(e)}")
        return None


# ============================================================================
# ANALYSIS EXECUTION
# ============================================================================

def run_analysis(df: pd.DataFrame, mode: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the appropriate analysis based on mode.
    
    Args:
        df: OHLC DataFrame
        mode: Analysis mode ("Automated" or "Semi-Manual")
        settings: Analysis settings dictionary
    
    Returns:
        Analysis result dictionary
    """
    try:
        if mode == "Automated":
            # Get degrees to analyze based on settings
            degrees = [WaveDegree.PRIMARY, WaveDegree.INTERMEDIATE, WaveDegree.MINOR]
            
            analyzer = AutomatedAnalyzer(
                pivot_sensitivity=settings.get('pivot_sensitivity', 5),
                min_confidence=settings.get('min_confidence', 30),
                use_adaptive=True,
                degrees=degrees
            )
            
            result = analyzer.analyze(
                df=df,
                max_patterns=settings.get('max_patterns', 3)
            )
            
            return result
        else:
            # Semi-manual mode - return basic structure
            return {
                'success': True,
                'pivots': st.session_state.user_pivots,
                'monowaves': [],
                'waves': [],
                'patterns': [],
                'primary_pattern': None,
                'mode': 'semi-manual'
            }
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"{str(e)}\n{traceback.format_exc()}",
            'pivots': [],
            'monowaves': [],
            'patterns': [],
            'primary_pattern': None
        }


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_metrics(result: Dict[str, Any]) -> None:
    """Display analysis metrics in columns."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pivot_count = len(result.get('pivots', []))
        st.metric(
            label="📍 Pivots Detected",
            value=pivot_count,
            help="Total swing high/low points identified across all degrees"
        )
    
    with col2:
        monowave_count = len(result.get('monowaves', []))
        st.metric(
            label="🌊 Wave Segments",
            value=monowave_count,
            help="Number of individual wave segments"
        )
    
    with col3:
        pattern_count = len(result.get('patterns', []))
        st.metric(
            label="📊 Patterns Found",
            value=pattern_count,
            help="Number of valid pattern interpretations"
        )
    
    with col4:
        primary = result.get('primary_pattern')
        conf = primary.confidence if primary and hasattr(primary, 'confidence') else 0
        st.metric(
            label="🎯 Confidence",
            value=f"{conf:.1f}%",
            help="Confidence level of primary pattern"
        )


def display_degree_metrics(result: Dict[str, Any]) -> None:
    """Display metrics for each wave degree."""
    multi_pivots = result.get('multi_degree_pivots', {})
    
    if not multi_pivots:
        return
    
    st.markdown("#### 📊 Pivots by Degree")
    
    cols = st.columns(len(multi_pivots))
    
    degree_colors = {
        WaveDegree.PRIMARY: "#58a6ff",
        WaveDegree.INTERMEDIATE: "#3fb950",
        WaveDegree.MINOR: "#d29922"
    }
    
    for i, (degree, pivots) in enumerate(multi_pivots.items()):
        with cols[i]:
            color = degree_colors.get(degree, "#8b949e")
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: #21262d; 
                        border-radius: 8px; border-left: 4px solid {color};">
                <p style="margin: 0; color: {color}; font-weight: bold;">{degree.name}</p>
                <p style="margin: 5px 0 0 0; font-size: 1.5rem; color: #c9d1d9;">{len(pivots)}</p>
                <p style="margin: 0; color: #8b949e; font-size: 0.8rem;">pivots</p>
            </div>
            """, unsafe_allow_html=True)


def display_pattern_details(result: Dict[str, Any]) -> None:
    """Display detailed pattern information with hierarchical support."""
    primary = result.get('primary_pattern')
    
    if not primary:
        st.info("ℹ️ No pattern identified. Try adjusting pivot sensitivity or selecting a different timeframe.")
        return
    
    # Confidence indicator
    confidence = primary.confidence if hasattr(primary, 'confidence') else 0
    if confidence >= 70:
        conf_color = "🟢"
        conf_text = "HIGH"
    elif confidence >= 40:
        conf_color = "🟡"
        conf_text = "MEDIUM"
    else:
        conf_color = "🔴"
        conf_text = "LOW"
    
    # Wave labels - support both hierarchical and regular
    wave_labels = ""
    if hasattr(primary, 'primary_waves') and primary.primary_waves:
        labels = [w.label for w in primary.primary_waves if hasattr(w, 'label')]
        wave_labels = " → ".join(labels)
    elif hasattr(primary, 'waves') and primary.waves:
        labels = [w.label for w in primary.waves if hasattr(w, 'label')]
        wave_labels = " → ".join(labels)
    
    # Get pattern name
    pattern_name = primary.pattern_name if hasattr(primary, 'pattern_name') else "Unknown"
    description = primary.description if hasattr(primary, 'description') else ""
    
    # Pattern header
    st.markdown(f"""
    ### 🎯 Primary Pattern: **{pattern_name}**
    
    {conf_color} **Confidence:** {confidence:.1f}% ({conf_text})
    
    🌊 **Primary Wave Structure:** {wave_labels}
    
    📝 {description}
    """)
    
    # Show degree confidence if available
    if hasattr(primary, 'degree_confidence') and primary.degree_confidence:
        st.markdown("#### 📊 Confidence by Degree")
        cols = st.columns(len(primary.degree_confidence))
        
        degree_colors = {
            "PRIMARY": "#58a6ff",
            "INTERMEDIATE": "#3fb950",
            "MINOR": "#d29922"
        }
        
        for i, (degree_name, conf) in enumerate(primary.degree_confidence.items()):
            with cols[i]:
                color = degree_colors.get(degree_name, "#8b949e")
                
                # Determine confidence level
                if conf >= 70:
                    level = "✓"
                elif conf >= 40:
                    level = "~"
                else:
                    level = "?"
                
                st.markdown(f"""
                <div style="text-align: center; padding: 8px; background: #21262d; 
                            border-radius: 6px; border-top: 3px solid {color};">
                    <p style="margin: 0; color: {color}; font-size: 0.9rem;">{degree_name}</p>
                    <p style="margin: 5px 0; font-size: 1.3rem; color: #c9d1d9;">{conf:.0f}% {level}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Detailed tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Targets", "⚠️ Violations", "🔄 Alternatives", 
        "📋 Wave Details", "🌳 Subdivisions"
    ])
    
    with tab1:
        display_targets(primary)
    
    with tab2:
        display_violations(primary)
    
    with tab3:
        display_alternatives(result.get('patterns', [])[1:])
    
    with tab4:
        display_wave_details(primary)
    
    with tab5:
        display_subdivisions(primary)


def display_targets(primary: Any) -> None:
    """Display price targets."""
    targets = []
    if hasattr(primary, 'next_targets'):
        targets = primary.next_targets
    
    if not targets:
        st.info("No price targets calculated for this pattern.")
        return
    
    for i, target in enumerate(targets, 1):
        price = target.get('price', 0)
        description = target.get('description', '')
        probability = target.get('probability', 0) * 100
        
        # Color based on probability
        if probability >= 70:
            prob_color = "#3fb950"
            prob_bg = "rgba(63, 185, 80, 0.1)"
        elif probability >= 50:
            prob_color = "#d29922"
            prob_bg = "rgba(210, 153, 34, 0.1)"
        else:
            prob_color = "#8b949e"
            prob_bg = "rgba(139, 148, 158, 0.1)"
        
        st.markdown(f"""
        <div style="background: {prob_bg}; border-left: 4px solid {prob_color}; 
                    padding: 12px; margin: 8px 0; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #58a6ff;">Target {i}:</strong> 
                    <span style="color: #3fb950; font-size: 1.2rem; font-weight: bold;">${price:.2f}</span>
                </div>
                <span style="color: {prob_color}; font-weight: bold;">{probability:.0f}%</span>
            </div>
            <p style="margin: 8px 0 0 0; color: #8b949e; font-size: 0.9rem;">{description}</p>
        </div>
        """, unsafe_allow_html=True)


def display_violations(primary: Any) -> None:
    """Display rule violations."""
    violations = []
    if hasattr(primary, 'violations'):
        violations = primary.violations
    
    if not violations:
        st.success("✅ No rule violations! Pattern is fully compliant with NEoWave rules.")
        return
    
    for v in violations:
        severity = v.get('severity', 'prefer')
        rule = v.get('rule', 'Unknown Rule')
        message = v.get('message', '')
        
        if severity == 'must':
            st.error(f"🔴 **{rule}**: {message}")
        elif severity == 'should':
            st.warning(f"🟡 **{rule}**: {message}")
        else:
            st.info(f"🔵 **{rule}**: {message}")
    
    # Show warnings if any
    warnings = []
    if hasattr(primary, 'warnings'):
        warnings = primary.warnings
    
    if warnings:
        st.markdown("#### Additional Warnings")
        for warning in warnings:
            st.warning(warning)


def display_alternatives(alternatives: List) -> None:
    """Display alternative pattern interpretations."""
    if not alternatives:
        st.info("No alternative patterns found.")
        return
    
    for alt in alternatives[:5]:
        # Get labels
        alt_labels = ""
        if hasattr(alt, 'primary_waves') and alt.primary_waves:
            alt_labels = " → ".join([w.label for w in alt.primary_waves if hasattr(w, 'label')])
        elif hasattr(alt, 'waves') and alt.waves:
            alt_labels = " → ".join([w.label for w in alt.waves if hasattr(w, 'label')])
        
        # Get confidence
        conf = alt.confidence if hasattr(alt, 'confidence') else 0
        pattern_name = alt.pattern_name if hasattr(alt, 'pattern_name') else "Unknown"
        
        # Confidence color
        if conf >= 50:
            conf_emoji = "🟢"
        elif conf >= 30:
            conf_emoji = "🟡"
        else:
            conf_emoji = "🔴"
        
        with st.expander(f"{conf_emoji} {pattern_name} ({conf:.1f}%)"):
            st.markdown(f"**Wave Structure:** {alt_labels}")
            
            if hasattr(alt, 'description'):
                st.markdown(f"**Description:** {alt.description}")
            
            if hasattr(alt, 'next_targets') and alt.next_targets:
                st.markdown("**Targets:**")
                for t in alt.next_targets[:3]:
                    st.markdown(f"- ${t['price']:.2f} ({t['description']})")


def display_wave_details(primary: Any) -> None:
    """Display wave-by-wave details table."""
    waves = []
    if hasattr(primary, 'primary_waves') and primary.primary_waves:
        waves = primary.primary_waves
    elif hasattr(primary, 'waves') and primary.waves:
        waves = primary.waves
    
    if not waves:
        st.info("No wave details available.")
        return
    
    wave_data = []
    for wave in waves:
        # Extract wave properties safely
        label = wave.label if hasattr(wave, 'label') else '?'
        
        start_price = wave.start_price if hasattr(wave, 'start_price') and wave.start_price else None
        end_price = wave.end_price if hasattr(wave, 'end_price') and wave.end_price else None
        
        start_str = f"${start_price:.2f}" if start_price else "N/A"
        end_str = f"${end_price:.2f}" if end_price else "N/A"
        
        movement = wave.price_movement if hasattr(wave, 'price_movement') and wave.price_movement else 0
        direction = "↑ Up" if movement > 0 else "↓ Down" if movement < 0 else "→ Flat"
        change = f"{movement:+.2f}" if movement else "N/A"
        
        # Subdivision info
        sub_count = len(wave.sub_waves) if hasattr(wave, 'sub_waves') and wave.sub_waves else 0
        sub_conf = wave.subdivision_confidence if hasattr(wave, 'subdivision_confidence') else 0
        
        wave_data.append({
            'Wave': label,
            'Start': start_str,
            'End': end_str,
            'Change': change,
            'Direction': direction,
            'Subdivisions': sub_count,
            'Sub Conf': f"{sub_conf:.0f}%"
        })
    
    df = pd.DataFrame(wave_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def display_subdivisions(primary: Any) -> None:
    """Display subdivision details for hierarchical patterns."""
    waves = []
    if hasattr(primary, 'primary_waves') and primary.primary_waves:
        waves = primary.primary_waves
    elif hasattr(primary, 'waves') and primary.waves:
        waves = primary.waves
    
    if not waves:
        st.info("No subdivision data available.")
        return
    
    has_any_subdivisions = any(
        hasattr(w, 'sub_waves') and w.sub_waves for w in waves
    )
    
    if not has_any_subdivisions:
        st.info("No subdivisions detected. Try increasing pivot sensitivity.")
        return
    
    for wave in waves:
        label = wave.label if hasattr(wave, 'label') else '?'
        sub_count = len(wave.sub_waves) if hasattr(wave, 'sub_waves') and wave.sub_waves else 0
        sub_conf = wave.subdivision_confidence if hasattr(wave, 'subdivision_confidence') else 0
        
        # Expected subdivisions
        expected = 5 if (hasattr(wave, 'wave_type') and str(wave.wave_type) == 'WaveType.MOTIVE') else 3
        completeness = (sub_count / expected * 100) if expected > 0 else 0
        
        # Color based on completeness
        if completeness >= 100:
            status_color = "#3fb950"
            status_text = "Complete"
        elif completeness >= 60:
            status_color = "#d29922"
            status_text = "Partial"
        else:
            status_color = "#8b949e"
            status_text = "Incomplete"
        
        with st.expander(f"Wave {label} - {sub_count}/{expected} subdivisions ({status_text})"):
            if hasattr(wave, 'sub_waves') and wave.sub_waves:
                # Show intermediate subdivisions
                sub_labels = " → ".join([s.label for s in wave.sub_waves])
                
                st.markdown(f"""
                <div style="padding: 10px; background: #21262d; border-radius: 6px; 
                            border-left: 3px solid #3fb950; margin-bottom: 10px;">
                    <p style="margin: 0; color: #3fb950;">
                        <strong>Intermediate:</strong> {sub_labels}
                    </p>
                    <p style="margin: 5px 0 0 0; color: #8b949e; font-size: 0.85rem;">
                        Confidence: {sub_conf:.0f}%
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show minor subdivisions if available
                for sub in wave.sub_waves:
                    if hasattr(sub, 'sub_waves') and sub.sub_waves:
                        minor_labels = " → ".join([m.label for m in sub.sub_waves])
                        minor_conf = sub.subdivision_confidence if hasattr(sub, 'subdivision_confidence') else 0
                        
                        st.markdown(f"""
                        <div style="padding: 8px; margin-left: 20px; background: #161b22; 
                                    border-radius: 4px; border-left: 2px solid #d29922;">
                            <p style="margin: 0; color: #d29922; font-size: 0.9rem;">
                                <strong>{sub.label} → Minor:</strong> {minor_labels}
                            </p>
                            <p style="margin: 3px 0 0 0; color: #8b949e; font-size: 0.8rem;">
                                Confidence: {minor_conf:.0f}%
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("_No subdivisions detected for this wave_")


def display_chart(df: pd.DataFrame, 
                  result: Dict[str, Any], 
                  display_options: Dict[str, bool], 
                  symbol: str, 
                  timeframe: str) -> None:
    """
    Display the analysis chart with hierarchical wave support.
    
    Args:
        df: OHLC DataFrame
        result: Analysis result dictionary
        display_options: Display settings dictionary
        symbol: Ticker symbol
        timeframe: Selected timeframe
    """
    remove_gaps = display_options.get('remove_gaps', True)
    
    try:
        if result and result.get('success') and result.get('primary_pattern'):
            fig = ChartRenderer.render_complete_analysis(
                df=df,
                analysis_result=result,
                show_pivots=display_options.get('show_pivots', True),
                show_waves=display_options.get('show_waves', True),
                show_labels=display_options.get('show_labels', True),
                show_pattern_box=display_options.get('show_pattern_box', True),
                show_fibonacci=display_options.get('show_fibonacci', False),
                show_alternatives=display_options.get('show_alternatives', False),
                show_all_monowaves=display_options.get('show_all_monowaves', True),
                show_targets=display_options.get('show_targets', False),
                remove_gaps=remove_gaps,
                # Degree toggles
                show_primary=display_options.get('show_primary', True),
                show_intermediate=display_options.get('show_intermediate', True),
                show_minor=display_options.get('show_minor', False)
            )
        else:
            fig = ChartRenderer.render_candlestick(
                df=df,
                title=f"{symbol} - {timeframe}",
                remove_gaps=remove_gaps
            )
            
            # Add pivots if available
            if result and result.get('pivots'):
                fig = ChartRenderer.add_pivots(
                    fig, 
                    result['pivots'], 
                    df, 
                    remove_gaps=remove_gaps
                )
            
            # Add all monowaves if available
            if result and result.get('monowaves') and display_options.get('show_all_monowaves', True):
                fig = ChartRenderer.add_all_monowaves(
                    fig,
                    result['monowaves'],
                    df,
                    remove_gaps=remove_gaps
                )
        
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        })
        
    except Exception as e:
        st.error(f"Error rendering chart: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        
        # Fallback to basic chart
        try:
            fig = ChartRenderer.render_candlestick(
                df, 
                title=f"{symbol} - {timeframe}", 
                remove_gaps=remove_gaps
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.error("Unable to render chart. Please try a different symbol or timeframe.")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main() -> None:
    """Main application entry point."""
    
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #30363d; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.8rem; background: linear-gradient(90deg, #58a6ff, #a371f7); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">📊 NEoWave</h1>
            <p style="margin: 5px 0 0 0; color: #8b949e; font-size: 0.9rem;">Multi-Degree Wave Analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Symbol Selection
        st.markdown("### 📈 Symbol")
        selected_symbol = render_symbol_input(st.session_state.all_symbols)
        
        st.markdown("---")
        
        # Timeframe Selection
        st.markdown("### ⏱️ Timeframe")
        selected_timeframe = st.selectbox(
            "Select Timeframe",
            options=list(TIMEFRAMES.keys()),
            index=2,  # Default: 1 Day
            key="timeframe_select",
            help="Choose the chart timeframe for analysis"
        )
        
        st.markdown("---")
        
        # Analysis Mode
        st.markdown("### 🔬 Analysis Mode")
        analysis_mode = st.radio(
            "Select Mode",
            options=["Automated", "Semi-Manual"],
            index=0,
            key="analysis_mode",
            horizontal=True,
            help="Automated: System detects patterns automatically\nSemi-Manual: You mark pivots manually"
        )
        
        st.markdown("---")
        
        # Mode-specific Settings
        if analysis_mode == "Automated":
            st.markdown("### ⚙️ Analysis Settings")
            
            pivot_sensitivity = st.slider(
                "Pivot Sensitivity",
                min_value=1,
                max_value=10,
                value=5,
                key="pivot_sens",
                help="Higher = more pivots detected at each degree level"
            )
            
            min_confidence = st.slider(
                "Min Confidence %",
                min_value=0,
                max_value=100,
                value=30,
                key="min_conf",
                help="Only show patterns above this confidence level"
            )
            
            max_patterns = st.selectbox(
                "Max Alternative Patterns",
                options=[1, 2, 3, 5],
                index=2,
                key="max_pat",
                help="Number of alternative interpretations to show"
            )
            
            settings: Dict[str, Any] = {
                'pivot_sensitivity': pivot_sensitivity,
                'min_confidence': min_confidence,
                'max_patterns': max_patterns
            }
        else:
            settings = {}
            st.info("📌 Semi-manual mode: Manual pivot marking feature coming soon.")
        
        st.markdown("---")
        
        # Display Options
        st.markdown("### 👁️ Display Options")
        
        col1, col2 = st.columns(2)
        with col1:
            show_pivots = st.checkbox("Pivots", value=True, key="show_piv",
                                       help="Show swing markers")
            show_waves = st.checkbox("Waves", value=True, key="show_wav",
                                      help="Show wave lines")
            show_labels = st.checkbox("Labels", value=True, key="show_lab",
                                       help="Show wave labels")
            show_all_monowaves = st.checkbox("All Swings", value=True, key="show_all_mw",
                                              help="Show background swings")
        with col2:
            show_pattern_box = st.checkbox("Box", value=True, key="show_box",
                                            help="Show pattern box")
            show_fibonacci = st.checkbox("Fibonacci", value=False, key="show_fib",
                                          help="Show Fib levels")
            show_alternatives = st.checkbox("Alternatives", value=False, key="show_alt",
                                             help="Show alt patterns")
            remove_gaps = st.checkbox("No Gaps", value=True, key="remove_gaps",
                                       help="Remove weekend gaps")
        
        st.markdown("---")
        
        # Wave Degree Toggles
        st.markdown("### 📊 Wave Degrees")
        st.caption("Toggle visibility of each wave degree level")
        
        show_primary = st.checkbox(
            "🔵 Primary (1-2-3-4-5)", 
            value=True, 
            key="show_primary",
            help="Largest degree - main wave structure"
        )
        
        show_intermediate = st.checkbox(
            "🟢 Intermediate ((1)-(2)-(3))", 
            value=True, 
            key="show_intermediate",
            help="Middle degree - subdivisions of primary"
        )
        
        show_minor = st.checkbox(
            "🟠 Minor (i-ii-iii-iv-v)", 
            value=False, 
            key="show_minor",
            help="Smallest degree - finest detail"
        )
        
        # Build display options dictionary
        display_options: Dict[str, bool] = {
            'show_pivots': show_pivots,
            'show_waves': show_waves,
            'show_labels': show_labels,
            'show_pattern_box': show_pattern_box,
            'show_fibonacci': show_fibonacci,
            'show_alternatives': show_alternatives,
            'show_all_monowaves': show_all_monowaves,
            'remove_gaps': remove_gaps,
            'show_targets': False,
            # Degree toggles
            'show_primary': show_primary,
            'show_intermediate': show_intermediate,
            'show_minor': show_minor
        }
        
        st.markdown("---")
        
        # Run Analysis Button
        run_clicked = st.button(
            "🚀 Run Analysis",
            use_container_width=True,
            type="primary",
            key="run_btn"
        )
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #8b949e; font-size: 0.75rem;">
            <p style="margin: 0;">NEoWave methodology by Glenn Neely</p>
            <p style="margin: 5px 0 0 0;">Multi-Degree Analysis v2.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ========================================================================
    # MAIN CONTENT AREA
    # ========================================================================
    
    # Header
    if selected_symbol:
        st.markdown(f"# {selected_symbol}")
        st.markdown(f"**Timeframe:** {selected_timeframe} | **Mode:** {analysis_mode}")
    else:
        st.markdown("# NEoWave Analyzer")
    
    st.markdown("---")
    
    # Handle Run Button Click
    if run_clicked:
        if not selected_symbol:
            st.error("❌ Please select a symbol first!")
        else:
            st.session_state.selected_symbol = selected_symbol
            
            # Fetch data
            with st.spinner(f"📡 Fetching data for {selected_symbol}..."):
                tf_config = TIMEFRAMES[selected_timeframe]
                df = fetch_market_data(selected_symbol, tf_config)
                
                if df is not None and len(df) > 0:
                    st.session_state.current_data = df
                    
                    # Display data info
                    date_range = f"{df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}"
                    st.success(f"✅ Loaded {len(df)} candles ({date_range})")
                    
                    # Run analysis
                    with st.spinner("🔬 Running multi-degree NEoWave analysis..."):
                        result = run_analysis(df, analysis_mode, settings)
                        st.session_state.analysis_result = result
                        
                        if result.get('success'):
                            pattern_count = len(result.get('patterns', []))
                            
                            # Count pivots by degree
                            multi_pivots = result.get('multi_degree_pivots', {})
                            pivot_summary = ", ".join([
                                f"{d.name}: {len(p)}" 
                                for d, p in multi_pivots.items()
                            ])
                            
                            st.success(f"✅ Analysis complete! Found {pattern_count} pattern(s). Pivots: {pivot_summary}")
                        else:
                            st.warning(f"⚠️ Analysis completed with issues: {result.get('error', 'Unknown')}")
                    
                    st.session_state.analysis_run = True
                else:
                    st.error("❌ No data returned. Please check the symbol and try again.")
                    st.session_state.analysis_run = False
    
    # Display Results
    if st.session_state.current_data is not None and st.session_state.analysis_run:
        df = st.session_state.current_data
        result = st.session_state.analysis_result
        
        # Metrics row
        if result and result.get('success'):
            display_metrics(result)
            
            # Degree-specific metrics
            if result.get('multi_degree_pivots'):
                display_degree_metrics(result)
            
            st.markdown("---")
        
        # Chart
        st.markdown("### 📈 Chart Analysis")
        display_chart(
            df=df,
            result=result,
            display_options=display_options,
            symbol=st.session_state.selected_symbol,
            timeframe=selected_timeframe
        )
        
        # Pattern Details (Automated mode only)
        if analysis_mode == "Automated" and result and result.get('success'):
            st.markdown("---")
            display_pattern_details(result)
        
        # Semi-Manual Controls
        if analysis_mode == "Semi-Manual" and result:
            st.markdown("---")
            st.markdown("### 🖱️ Manual Pivot Entry")
            st.info("🚧 Semi-manual pivot entry feature is under development. Please use Automated mode for now.")
    
    else:
        # Welcome Screen
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <h2 style="color: #58a6ff; margin-bottom: 20px;">Welcome to NEoWave Analyzer</h2>
            <p style="color: #8b949e; font-size: 1.1rem; max-width: 600px; margin: 0 auto 30px auto;">
                Professional Elliott Wave analysis with multi-degree wave detection.
                Analyze Primary, Intermediate, and Minor wave structures simultaneously.
            </p>
            
            <h3 style="color: #c9d1d9; margin-top: 40px;">🚀 Quick Start</h3>
            <ol style="text-align: left; max-width: 450px; margin: 20px auto; color: #8b949e; line-height: 2;">
                <li>Enter a symbol in the sidebar (e.g., AAPL, BTC-USD)</li>
                <li>Select your preferred timeframe</li>
                <li>Adjust pivot sensitivity (higher = more detail)</li>
                <li>Click <strong style="color: #3fb950;">Run Analysis</strong></li>
                <li>Toggle wave degrees to show/hide subdivisions</li>
            </ol>
            
            <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-top: 50px;">
                <div style="text-align: center; max-width: 160px; padding: 20px; background: #21262d; border-radius: 8px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🔵</div>
                    <p style="color: #58a6ff; margin: 0; font-weight: bold;">Primary</p>
                    <p style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">Main wave structure<br>1-2-3-4-5</p>
                </div>
                <div style="text-align: center; max-width: 160px; padding: 20px; background: #21262d; border-radius: 8px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🟢</div>
                    <p style="color: #3fb950; margin: 0; font-weight: bold;">Intermediate</p>
                    <p style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">Subdivisions<br>(1)-(2)-(3)-(4)-(5)</p>
                </div>
                <div style="text-align: center; max-width: 160px; padding: 20px; background: #21262d; border-radius: 8px;">
                    <div style="font-size: 2rem; margin-bottom: 10px;">🟠</div>
                    <p style="color: #d29922; margin: 0; font-weight: bold;">Minor</p>
                    <p style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">Finest detail<br>i-ii-iii-iv-v</p>
                </div>
            </div>
            
            <div style="margin-top: 50px; padding: 20px; background: #21262d; border-radius: 8px; max-width: 500px; margin-left: auto; margin-right: auto;">
                <h4 style="color: #58a6ff; margin: 0 0 10px 0;">📊 Multi-Degree Analysis</h4>
                <p style="color: #8b949e; font-size: 0.9rem; margin: 0;">
                    NEoWave uses hierarchical wave counting where each wave contains subdivisions 
                    of a smaller degree. This app detects all three levels simultaneously and 
                    lets you toggle visibility of each degree.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
