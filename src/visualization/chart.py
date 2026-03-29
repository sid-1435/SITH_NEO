"""
NEoWave Chart Visualization Module
Renders interactive candlestick charts with NEoWave wave annotations.
"""

import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Optional, Any

# Import wave degree configurations
try:
    from ..core.wave_degree import WaveDegree, DEGREE_CONFIGS, HierarchicalWave, HierarchicalWaveCount
except ImportError:
    # Fallback if wave_degree module not available
    WaveDegree = None
    DEGREE_CONFIGS = None
    HierarchicalWave = None
    HierarchicalWaveCount = None


class ChartRenderer:
    """
    Renders interactive candlestick charts with NEoWave annotations.
    
    Features:
    - Candlestick charts with dark theme
    - Removes gaps for non-trading days
    - Wave structure lines and labels
    - Pattern boundary boxes
    - Fibonacci levels
    - All monowaves visualization
    - Multi-degree hierarchical wave rendering
    """
    
    # Color scheme for wave labels
    WAVE_COLORS: Dict[str, str] = {
        # Motive waves (impulse direction)
        '1': '#3fb950',  # Green
        '3': '#3fb950',
        '5': '#3fb950',
        # Corrective waves
        '2': '#f85149',  # Red
        '4': '#f85149',
        # Corrective pattern waves
        'A': '#58a6ff',  # Blue
        'C': '#58a6ff',
        'E': '#58a6ff',
        'G': '#58a6ff',
        'I': '#58a6ff',
        'B': '#d29922',  # Orange
        'D': '#d29922',
        'F': '#d29922',
        'H': '#d29922',
        # Complex combination waves
        'W': '#a371f7',  # Purple
        'X': '#8b949e',  # Gray
        'Y': '#a371f7',
        'Z': '#a371f7',
        # Intermediate degree labels
        '(1)': '#3fb950',
        '(2)': '#f85149',
        '(3)': '#3fb950',
        '(4)': '#f85149',
        '(5)': '#3fb950',
        '(A)': '#3fb950',
        '(B)': '#d29922',
        '(C)': '#3fb950',
        # Minor degree labels
        'i': '#d29922',
        'ii': '#8b949e',
        'iii': '#d29922',
        'iv': '#8b949e',
        'v': '#d29922',
        'a': '#d29922',
        'b': '#8b949e',
        'c': '#d29922',
    }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    @staticmethod
    def _format_x_value(timestamp: Any, remove_gaps: bool = True) -> Any:
        """
        Format timestamp for x-axis based on gap removal setting.
        
        Args:
            timestamp: Datetime timestamp
            remove_gaps: If True, convert to string for categorical axis
        
        Returns:
            Formatted x-axis value
        """
        if remove_gaps:
            if hasattr(timestamp, 'strftime'):
                return timestamp.strftime('%Y-%m-%d %H:%M')
            return str(timestamp)
        return timestamp
    
    # =========================================================================
    # BASE CHART
    # =========================================================================
    
    @staticmethod
    def render_candlestick(df: pd.DataFrame, 
                           title: str = "Price Chart",
                           height: int = 600,
                           remove_gaps: bool = True) -> go.Figure:
        """
        Render basic candlestick chart with professional dark theme.
        
        Args:
            df: OHLC DataFrame with columns: open, high, low, close
            title: Chart title
            height: Chart height in pixels
            remove_gaps: If True, removes gaps for non-trading days
        
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        # Create x-axis values
        if remove_gaps:
            x_values = df.index.strftime('%Y-%m-%d %H:%M')
        else:
            x_values = df.index
        
        # Add candlestick trace
        fig.add_trace(go.Candlestick(
            x=x_values,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#26a69a',
            increasing_fillcolor='#26a69a',
            decreasing_line_color='#ef5350',
            decreasing_fillcolor='#ef5350',
            whiskerwidth=0.5
        ))
        
        # Professional dark theme layout
        fig.update_layout(
            title=dict(
                text=title, 
                font=dict(color='#58a6ff', size=20, family='Segoe UI'),
                x=0.5,
                xanchor='center'
            ),
            yaxis_title='Price',
            xaxis_title='',
            height=height,
            template='plotly_dark',
            paper_bgcolor='#0d1117',
            plot_bgcolor='#0d1117',
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            xaxis=dict(
                gridcolor='#21262d',
                showgrid=True,
                type='category' if remove_gaps else 'date',
                tickangle=-45,
                nticks=20,
                showticklabels=True,
                tickfont=dict(size=9, color='#8b949e'),
                linecolor='#30363d',
                mirror=True
            ),
            yaxis=dict(
                gridcolor='#21262d',
                showgrid=True,
                tickfont=dict(size=10, color='#8b949e'),
                side='right',
                linecolor='#30363d',
                mirror=True
            ),
            legend=dict(
                bgcolor='rgba(13, 17, 23, 0.8)',
                bordercolor='#30363d',
                borderwidth=1,
                font=dict(color='#c9d1d9', size=10),
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            margin=dict(l=10, r=60, t=80, b=60)
        )
        
        return fig
    
    # =========================================================================
    # PIVOT MARKERS
    # =========================================================================
    
    @staticmethod
    def add_pivots(fig: go.Figure, 
                   pivots: List[Dict], 
                   df: pd.DataFrame, 
                   remove_gaps: bool = True) -> go.Figure:
        """
        Add pivot point markers to the chart.
        
        Args:
            fig: Plotly Figure object
            pivots: List of pivot dictionaries with keys: time, price, type
            df: OHLC DataFrame
            remove_gaps: If True, format timestamps for categorical axis
        
        Returns:
            Updated Figure object
        """
        if not pivots:
            return fig
        
        high_pivots = [p for p in pivots if p.get('type') == 'high']
        low_pivots = [p for p in pivots if p.get('type') == 'low']
        
        # Add high pivot markers
        if high_pivots:
            x_values = [ChartRenderer._format_x_value(p['time'], remove_gaps) for p in high_pivots]
            fig.add_trace(go.Scatter(
                x=x_values,
                y=[p['price'] for p in high_pivots],
                mode='markers',
                name='Swing High',
                marker=dict(
                    symbol='triangle-down',
                    size=10,
                    color='rgba(248, 81, 73, 0.8)',
                    line=dict(width=1, color='white')
                ),
                hovertemplate='<b>High</b>: $%{y:.2f}<extra></extra>',
                showlegend=True
            ))
        
        # Add low pivot markers
        if low_pivots:
            x_values = [ChartRenderer._format_x_value(p['time'], remove_gaps) for p in low_pivots]
            fig.add_trace(go.Scatter(
                x=x_values,
                y=[p['price'] for p in low_pivots],
                mode='markers',
                name='Swing Low',
                marker=dict(
                    symbol='triangle-up',
                    size=10,
                    color='rgba(63, 185, 80, 0.8)',
                    line=dict(width=1, color='white')
                ),
                hovertemplate='<b>Low</b>: $%{y:.2f}<extra></extra>',
                showlegend=True
            ))
        
        return fig
    
    # =========================================================================
    # ALL MONOWAVES (BACKGROUND)
    # =========================================================================
    
    @staticmethod
    def add_all_monowaves(fig: go.Figure, 
                          monowaves: List, 
                          df: pd.DataFrame,
                          remove_gaps: bool = True, 
                          opacity: float = 0.3) -> go.Figure:
        """
        Add ALL monowaves as a light background trace.
        This helps visualize the complete wave structure.
        
        Args:
            fig: Plotly Figure object
            monowaves: List of Monowave objects
            df: OHLC DataFrame
            remove_gaps: If True, format timestamps for categorical axis
            opacity: Opacity of the background trace (0.0 - 1.0)
        
        Returns:
            Updated Figure object
        """
        if not monowaves:
            return fig
        
        x_coords = []
        y_coords = []
        
        # Collect all monowave start points
        for mw in monowaves:
            if hasattr(mw, 'start_time') and hasattr(mw, 'start_price'):
                if mw.start_time is not None and mw.start_price is not None:
                    x_coords.append(ChartRenderer._format_x_value(mw.start_time, remove_gaps))
                    y_coords.append(mw.start_price)
        
        # Add last monowave end point
        if monowaves:
            last = monowaves[-1]
            if hasattr(last, 'end_time') and hasattr(last, 'end_price'):
                if last.end_time is not None and last.end_price is not None:
                    x_coords.append(ChartRenderer._format_x_value(last.end_time, remove_gaps))
                    y_coords.append(last.end_price)
        
        if len(x_coords) >= 2:
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='lines+markers',
                name='All Swings',
                line=dict(
                    color=f'rgba(128, 128, 128, {opacity})', 
                    width=1, 
                    dash='dot'
                ),
                marker=dict(
                    size=4, 
                    color=f'rgba(128, 128, 128, {opacity})',
                    symbol='circle'
                ),
                hovertemplate='$%{y:.2f}<extra></extra>',
                showlegend=True
            ))
        
        return fig
    
    # =========================================================================
    # WAVE STRUCTURE LINES
    # =========================================================================
    
    @staticmethod
    def add_wave_lines(fig: go.Figure, 
                       waves: List, 
                       color: str = '#58a6ff', 
                       width: int = 2, 
                       dash: str = 'solid', 
                       name: str = 'Wave Count',
                       remove_gaps: bool = True) -> go.Figure:
        """
        Add wave structure lines connecting wave endpoints.
        
        Args:
            fig: Plotly Figure object
            waves: List of Wave objects
            color: Line color
            width: Line width
            dash: Line dash style ('solid', 'dash', 'dot', 'dashdot')
            name: Legend name
            remove_gaps: If True, format timestamps for categorical axis
        
        Returns:
            Updated Figure object
        """
        if not waves:
            return fig
        
        x_coords = []
        y_coords = []

        for i, wave in enumerate(waves):
            if not (hasattr(wave, 'start_time') and hasattr(wave, 'start_price')):
                continue
            if wave.start_time is None or wave.start_price is None:
                continue

            # Insert None break between non-contiguous waves
            if x_coords and i > 0:
                prev_wave = waves[i - 1]
                if hasattr(prev_wave, 'end_time') and prev_wave.end_time is not None:
                    prev_end_x = ChartRenderer._format_x_value(prev_wave.end_time, remove_gaps)
                    this_start_x = ChartRenderer._format_x_value(wave.start_time, remove_gaps)
                    if prev_end_x != this_start_x:
                        x_coords.append(None)
                        y_coords.append(None)

            x_coords.append(ChartRenderer._format_x_value(wave.start_time, remove_gaps))
            y_coords.append(wave.start_price)

            if hasattr(wave, 'end_time') and hasattr(wave, 'end_price'):
                if wave.end_time is not None and wave.end_price is not None:
                    x_coords.append(ChartRenderer._format_x_value(wave.end_time, remove_gaps))
                    y_coords.append(wave.end_price)

        # Add trace if we have enough points
        if len(x_coords) >= 2 and len(y_coords) >= 2:
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='lines',
                name=name,
                line=dict(color=color, width=width, dash=dash),
                hovertemplate='$%{y:.2f}<extra></extra>',
                showlegend=True,
                connectgaps=False
            ))
        
        return fig
    
    # =========================================================================
    # WAVE LABELS
    # =========================================================================
    
    @staticmethod
    def add_wave_labels(fig: go.Figure, 
                        waves: List, 
                        offset_pct: float = 1.5,
                        remove_gaps: bool = True) -> go.Figure:
        """
        Add wave labels (1, 2, 3, 4, 5 or A, B, C, etc.) to the chart.
        Labels are placed at wave endpoints with appropriate positioning.
        
        Args:
            fig: Plotly Figure object
            waves: List of Wave objects
            offset_pct: Percentage offset for label placement
            remove_gaps: If True, format timestamps for categorical axis
        
        Returns:
            Updated Figure object
        """
        if not waves:
            return fig
        
        for i, wave in enumerate(waves):
            # Get wave label
            label = wave.label if hasattr(wave, 'label') and wave.label else str(i + 1)
            
            # Skip if no valid end position
            if not hasattr(wave, 'end_time') or not hasattr(wave, 'end_price'):
                continue
            if wave.end_time is None or wave.end_price is None:
                continue
            
            x_pos = ChartRenderer._format_x_value(wave.end_time, remove_gaps)
            y_pos = wave.end_price
            
            # Calculate offset for label placement
            if hasattr(wave, 'price_movement') and wave.price_movement is not None:
                price_range = abs(wave.price_movement)
            elif hasattr(wave, 'start_price') and wave.start_price is not None:
                price_range = abs(wave.end_price - wave.start_price)
            else:
                price_range = y_pos * 0.02
            
            # Ensure minimum offset
            offset = max(price_range * (offset_pct / 100), y_pos * 0.008)
            
            # Position label above or below based on wave direction
            if hasattr(wave, 'price_movement') and wave.price_movement is not None:
                if wave.price_movement > 0:
                    y_pos = wave.end_price + offset
                    y_anchor = 'bottom'
                else:
                    y_pos = wave.end_price - offset
                    y_anchor = 'top'
            else:
                y_anchor = 'middle'
            
            # Get color for this wave label
            label_color = ChartRenderer.WAVE_COLORS.get(label, '#f0e68c')
            
            # Add annotation
            fig.add_annotation(
                x=x_pos,
                y=y_pos,
                text=f"<b>{label}</b>",
                showarrow=False,
                font=dict(size=16, color=label_color, family='Arial Black'),
                bgcolor='rgba(0, 0, 0, 0.85)',
                bordercolor=label_color,
                borderwidth=2,
                borderpad=6,
                yanchor=y_anchor,
                xanchor='center'
            )
        
        return fig
    
    # =========================================================================
    # PATTERN BOX
    # =========================================================================
    
    @staticmethod
    def add_pattern_box(fig: go.Figure, 
                        pattern: Any, 
                        df: pd.DataFrame,
                        remove_gaps: bool = True) -> go.Figure:
        """
        Add a shaded box around the identified pattern with pattern name and confidence.
        
        Args:
            fig: Plotly Figure object
            pattern: WaveCount object with waves and pattern info
            df: OHLC DataFrame
            remove_gaps: If True, format timestamps for categorical axis
        
        Returns:
            Updated Figure object
        """
        # Get waves from pattern
        waves = None
        if hasattr(pattern, 'primary_waves') and pattern.primary_waves:
            waves = pattern.primary_waves
        elif hasattr(pattern, 'waves') and pattern.waves:
            waves = pattern.waves
        
        if not waves:
            return fig
        
        try:
            # Get x range
            x0 = waves[0].start_time if hasattr(waves[0], 'start_time') else None
            x1 = waves[-1].end_time if hasattr(waves[-1], 'end_time') else None
            
            if x0 is None or x1 is None:
                return fig
            
            # Format x values
            x0_formatted = ChartRenderer._format_x_value(x0, remove_gaps)
            x1_formatted = ChartRenderer._format_x_value(x1, remove_gaps)
            
            # Get y range from all wave prices
            all_highs = []
            all_lows = []
            
            for w in waves:
                if hasattr(w, 'high_price') and w.high_price is not None:
                    all_highs.append(w.high_price)
                if hasattr(w, 'low_price') and w.low_price is not None:
                    all_lows.append(w.low_price)
                if hasattr(w, 'start_price') and w.start_price is not None:
                    all_highs.append(w.start_price)
                    all_lows.append(w.start_price)
                if hasattr(w, 'end_price') and w.end_price is not None:
                    all_highs.append(w.end_price)
                    all_lows.append(w.end_price)
            
            if not all_highs or not all_lows:
                return fig
            
            y0 = min(all_lows)
            y1 = max(all_highs)
            
            # Add margin
            margin = (y1 - y0) * 0.05
            y0 -= margin
            y1 += margin
            
            # Add rectangle shape
            fig.add_shape(
                type="rect",
                x0=x0_formatted, x1=x1_formatted,
                y0=y0, y1=y1,
                line=dict(color="rgba(88, 166, 255, 0.6)", width=2, dash="dot"),
                fillcolor="rgba(88, 166, 255, 0.05)"
            )
            
            # Get pattern info
            confidence = pattern.confidence if hasattr(pattern, 'confidence') else 0
            pattern_name = pattern.pattern_name if hasattr(pattern, 'pattern_name') else 'Pattern'
            
            # Determine confidence color
            if confidence >= 70:
                conf_color = '#3fb950'
                conf_text = 'HIGH'
            elif confidence >= 40:
                conf_color = '#d29922'
                conf_text = 'MEDIUM'
            else:
                conf_color = '#f85149'
                conf_text = 'LOW'
            
            # Add pattern name annotation
            fig.add_annotation(
                x=x0_formatted,
                y=y1,
                text=f"<b>{pattern_name}</b><br><span style='color:{conf_color}'>{confidence:.0f}% ({conf_text})</span>",
                showarrow=True,
                arrowhead=2,
                arrowcolor='#58a6ff',
                arrowsize=1,
                arrowwidth=2,
                font=dict(size=11, color='#c9d1d9'),
                bgcolor='rgba(0, 0, 0, 0.9)',
                bordercolor='#58a6ff',
                borderwidth=1,
                borderpad=8,
                ax=-70,
                ay=-50,
                align='left'
            )
            
        except Exception:
            pass
        
        return fig
    
    # =========================================================================
    # FIBONACCI LEVELS
    # =========================================================================
    
    @staticmethod
    def add_fibonacci_levels(fig: go.Figure, 
                             waves: List, 
                             level_type: str = 'retracement') -> go.Figure:
        """
        Add Fibonacci retracement or extension levels.
        
        Args:
            fig: Plotly Figure object
            waves: List of Wave objects
            level_type: 'retracement' or 'extension'
        
        Returns:
            Updated Figure object
        """
        if not waves or len(waves) < 2:
            return fig
        
        try:
            wave1 = waves[0]
            
            if not hasattr(wave1, 'start_price') or not hasattr(wave1, 'end_price'):
                return fig
            if wave1.start_price is None or wave1.end_price is None:
                return fig
            
            high = max(wave1.start_price, wave1.end_price)
            low = min(wave1.start_price, wave1.end_price)
            diff = high - low
            
            if diff <= 0:
                return fig
            
            # Define Fibonacci levels
            if level_type == 'retracement':
                levels = {
                    '0%': high,
                    '23.6%': high - diff * 0.236,
                    '38.2%': high - diff * 0.382,
                    '50%': high - diff * 0.5,
                    '61.8%': high - diff * 0.618,
                    '78.6%': high - diff * 0.786,
                    '100%': low
                }
            else:
                levels = {
                    '0%': wave1.end_price,
                    '61.8%': wave1.end_price + diff * 0.618,
                    '100%': wave1.end_price + diff * 1.0,
                    '161.8%': wave1.end_price + diff * 1.618,
                    '261.8%': wave1.end_price + diff * 2.618
                }
            
            colors = ['#8b949e', '#d29922', '#f0e68c', '#58a6ff', '#a371f7', '#f85149', '#8b949e']
            
            for i, (label, price) in enumerate(levels.items()):
                fig.add_hline(
                    y=price,
                    line_dash="dot",
                    line_color=colors[i % len(colors)],
                    line_width=1,
                    annotation_text=f"Fib {label}: ${price:.2f}",
                    annotation_position="right",
                    annotation_font_size=9,
                    annotation_font_color=colors[i % len(colors)]
                )
                
        except Exception:
            pass
        
        return fig
    
    # =========================================================================
    # PRICE TARGETS
    # =========================================================================
    
    @staticmethod
    def add_price_targets(fig: go.Figure, 
                          targets: List[Dict],
                          remove_gaps: bool = True) -> go.Figure:
        """
        Add price target horizontal lines.
        
        Args:
            fig: Plotly Figure object
            targets: List of target dictionaries with keys: price, description, probability
            remove_gaps: If True, format timestamps for categorical axis
        
        Returns:
            Updated Figure object
        """
        if not targets:
            return fig
        
        for i, target in enumerate(targets):
            price = target.get('price', 0)
            description = target.get('description', f'Target {i+1}')
            probability = target.get('probability', 0.5)
            
            if probability >= 0.7:
                color = '#3fb950'
            elif probability >= 0.5:
                color = '#d29922'
            else:
                color = '#8b949e'
            
            fig.add_hline(
                y=price,
                line_dash="dash",
                line_color=color,
                line_width=2,
                annotation_text=f"Target: ${price:.2f} ({probability*100:.0f}%)",
                annotation_position="left",
                annotation_font_size=10,
                annotation_font_color=color
            )
        
        return fig
    
    # =========================================================================
    # HIERARCHICAL WAVE RENDERING
    # =========================================================================
    
    @staticmethod
    def render_hierarchical_waves(fig: go.Figure,
                                   wave_count: Any,
                                   show_degrees: Dict[str, bool],
                                   remove_gaps: bool = True) -> go.Figure:
        """
        Render waves at multiple degree levels with proper styling.
        
        Args:
            fig: Plotly Figure object
            wave_count: HierarchicalWaveCount object
            show_degrees: Dict of degree name -> bool (show/hide)
            remove_gaps: Remove time gaps
        
        Returns:
            Updated Figure object
        """
        if not wave_count:
            return fig
        
        # Check if wave_count has the method to get waves by degree
        if not hasattr(wave_count, 'get_waves_by_degree'):
            return fig
        
        # Check if DEGREE_CONFIGS is available
        if DEGREE_CONFIGS is None or WaveDegree is None:
            return fig
        
        # Define degree configurations for rendering
        degree_render_configs = {
            'PRIMARY': {
                'degree': WaveDegree.PRIMARY,
                'color': '#58a6ff',
                'line_width': 4,
                'line_dash': 'solid',
                'font_size': 18,
                'name': 'Primary'
            },
            'INTERMEDIATE': {
                'degree': WaveDegree.INTERMEDIATE,
                'color': '#3fb950',
                'line_width': 2,
                'line_dash': 'solid',
                'font_size': 14,
                'name': 'Intermediate'
            },
            'MINOR': {
                'degree': WaveDegree.MINOR,
                'color': '#d29922',
                'line_width': 1,
                'line_dash': 'dot',
                'font_size': 10,
                'name': 'Minor'
            }
        }
        
        # Render each degree level
        for degree_name, config in degree_render_configs.items():
            # Check if this degree should be shown
            show_key = f'show_{degree_name.lower()}'
            if not show_degrees.get(show_key, False):
                continue
            
            try:
                # Get waves of this degree
                waves = wave_count.get_waves_by_degree(config['degree'])
                
                if not waves:
                    continue
                
                # Add wave lines
                fig = ChartRenderer._add_hierarchical_wave_lines(
                    fig=fig,
                    waves=waves,
                    color=config['color'],
                    line_width=config['line_width'],
                    line_dash=config['line_dash'],
                    name=f"{config['name']} Waves",
                    remove_gaps=remove_gaps
                )
                
                # Add wave labels
                fig = ChartRenderer._add_hierarchical_wave_labels(
                    fig=fig,
                    waves=waves,
                    color=config['color'],
                    font_size=config['font_size'],
                    remove_gaps=remove_gaps
                )
            except Exception:
                pass
        
        return fig
    
    @staticmethod
    def _add_hierarchical_wave_lines(fig: go.Figure,
                                      waves: List,
                                      color: str,
                                      line_width: int,
                                      line_dash: str,
                                      name: str,
                                      remove_gaps: bool = True) -> go.Figure:
        """
        Add wave lines for a specific degree level.

        FIX: Previously all waves were joined into one continuous polyline,
        which connected visually separate patterns with a spurious diagonal
        line and made it look like patterns only appeared in one region.
        Now we insert a None break whenever a wave's start does not match
        the previous wave's end, so each pattern segment is drawn
        independently within the same legend trace.
        """
        if not waves:
            return fig

        x_coords = []
        y_coords = []

        for i, wave in enumerate(waves):
            if not (hasattr(wave, 'start_time') and hasattr(wave, 'start_price')):
                continue
            if wave.start_time is None or wave.start_price is None:
                continue

            # Detect discontinuity: if this wave's start doesn't follow the
            # previous wave's end, insert a None break to lift the pen.
            if x_coords:
                prev_wave = waves[i - 1] if i > 0 else None
                if prev_wave and hasattr(prev_wave, 'end_time') and prev_wave.end_time is not None:
                    prev_end_x = ChartRenderer._format_x_value(prev_wave.end_time, remove_gaps)
                    this_start_x = ChartRenderer._format_x_value(wave.start_time, remove_gaps)
                    if prev_end_x != this_start_x:
                        x_coords.append(None)
                        y_coords.append(None)

            x_coords.append(ChartRenderer._format_x_value(wave.start_time, remove_gaps))
            y_coords.append(wave.start_price)

            # After the last point of each wave, add its end point
            if hasattr(wave, 'end_time') and hasattr(wave, 'end_price'):
                if wave.end_time is not None and wave.end_price is not None:
                    x_coords.append(ChartRenderer._format_x_value(wave.end_time, remove_gaps))
                    y_coords.append(wave.end_price)

        if len(x_coords) >= 2:
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='lines',
                name=name,
                line=dict(
                    color=color,
                    width=line_width,
                    dash=line_dash
                ),
                hovertemplate='$%{y:.2f}<extra></extra>',
                showlegend=True,
                connectgaps=False  # Respect the None breaks
            ))

        return fig
    
    @staticmethod
    def _add_hierarchical_wave_labels(fig: go.Figure,
                                       waves: List,
                                       color: str,
                                       font_size: int,
                                       remove_gaps: bool = True) -> go.Figure:
        """Add wave labels for a specific degree level"""
        if not waves:
            return fig
        
        for wave in waves:
            if not hasattr(wave, 'end_time') or not hasattr(wave, 'end_price'):
                continue
            if wave.end_time is None or wave.end_price is None:
                continue
            
            x_pos = ChartRenderer._format_x_value(wave.end_time, remove_gaps)
            y_pos = wave.end_price
            
            # Calculate offset based on wave direction
            if hasattr(wave, 'price_movement') and wave.price_movement is not None:
                offset = abs(wave.price_movement) * 0.02
                if wave.price_movement > 0:
                    y_pos += offset
                    y_anchor = 'bottom'
                else:
                    y_pos -= offset
                    y_anchor = 'top'
            else:
                y_anchor = 'middle'
            
            # Get label
            label = wave.label if hasattr(wave, 'label') else '?'
            
            fig.add_annotation(
                x=x_pos,
                y=y_pos,
                text=f"<b>{label}</b>",
                showarrow=False,
                font=dict(
                    size=font_size,
                    color=color,
                    family='Arial Black'
                ),
                bgcolor='rgba(0, 0, 0, 0.8)',
                bordercolor=color,
                borderwidth=1,
                borderpad=4,
                yanchor=y_anchor,
                xanchor='center'
            )
        
        return fig
    
    # =========================================================================
    # COMPLETE ANALYSIS RENDER
    # =========================================================================
    
    @staticmethod
    def render_complete_analysis(df: pd.DataFrame, 
                                 analysis_result: Dict[str, Any],
                                 show_pivots: bool = True,
                                 show_waves: bool = True,
                                 show_labels: bool = True,
                                 show_pattern_box: bool = True,
                                 show_fibonacci: bool = False,
                                 show_alternatives: bool = False,
                                 show_all_monowaves: bool = True,
                                 show_targets: bool = False,
                                 remove_gaps: bool = True,
                                 show_primary: bool = True,
                                 show_intermediate: bool = True,
                                 show_minor: bool = False) -> go.Figure:
        """
        Render complete NEoWave analysis with hierarchical support.
        
        Args:
            df: OHLC DataFrame
            analysis_result: Analysis result dictionary
            show_pivots: Show pivot markers
            show_waves: Show wave lines
            show_labels: Show wave labels
            show_pattern_box: Show pattern boundary box
            show_fibonacci: Show Fibonacci levels
            show_alternatives: Show alternative patterns
            show_all_monowaves: Show all detected swings
            show_targets: Show price targets
            remove_gaps: Remove weekend/holiday gaps
            show_primary: Show primary degree waves
            show_intermediate: Show intermediate degree waves
            show_minor: Show minor degree waves
        
        Returns:
            Plotly Figure object
        """
        # Create base candlestick chart
        fig = ChartRenderer.render_candlestick(
            df, 
            title="NEoWave Analysis", 
            remove_gaps=remove_gaps
        )
        
        # Return base chart if no valid analysis
        if not analysis_result or not analysis_result.get('success'):
            return fig
        
        # Layer 1: All monowaves as background
        if show_all_monowaves and 'monowaves' in analysis_result and analysis_result['monowaves']:
            fig = ChartRenderer.add_all_monowaves(
                fig, 
                analysis_result['monowaves'], 
                df, 
                remove_gaps=remove_gaps, 
                opacity=0.2
            )
        
        # Layer 2: Pivot markers
        if show_pivots and 'pivots' in analysis_result and analysis_result['pivots']:
            fig = ChartRenderer.add_pivots(
                fig, 
                analysis_result['pivots'], 
                df, 
                remove_gaps=remove_gaps
            )
        
        # Get primary pattern
        primary = analysis_result.get('primary_pattern')
        
        if primary:
            # Check if hierarchical analysis
            is_hierarchical = analysis_result.get('hierarchical', False)
            
            if is_hierarchical and hasattr(primary, 'get_waves_by_degree'):
                # Hierarchical rendering with degree toggles
                show_degrees = {
                    'show_primary': show_primary,
                    'show_intermediate': show_intermediate,
                    'show_minor': show_minor
                }
                
                if show_waves or show_labels:
                    fig = ChartRenderer.render_hierarchical_waves(
                        fig=fig,
                        wave_count=primary,
                        show_degrees=show_degrees,
                        remove_gaps=remove_gaps
                    )
            else:
                # Fallback to original rendering
                waves = None
                if hasattr(primary, 'primary_waves') and primary.primary_waves:
                    waves = primary.primary_waves
                elif hasattr(primary, 'waves') and primary.waves:
                    waves = primary.waves
                
                if waves:
                    if show_waves:
                        pattern_name = primary.pattern_name if hasattr(primary, 'pattern_name') else 'Pattern'
                        fig = ChartRenderer.add_wave_lines(
                            fig, 
                            waves, 
                            color='#58a6ff', 
                            width=3, 
                            name=f"{pattern_name} Wave Count",
                            remove_gaps=remove_gaps
                        )
                    
                    if show_labels:
                        fig = ChartRenderer.add_wave_labels(
                            fig, 
                            waves, 
                            remove_gaps=remove_gaps
                        )
            
            # Pattern box
            if show_pattern_box:
                fig = ChartRenderer.add_pattern_box(
                    fig, 
                    primary, 
                    df, 
                    remove_gaps=remove_gaps
                )
            
            # Fibonacci levels
            waves_for_fib = None
            if hasattr(primary, 'primary_waves') and primary.primary_waves:
                waves_for_fib = primary.primary_waves
            elif hasattr(primary, 'waves') and primary.waves:
                waves_for_fib = primary.waves
            
            if show_fibonacci and waves_for_fib:
                fig = ChartRenderer.add_fibonacci_levels(fig, waves_for_fib)
            
            # Price targets
            if show_targets and hasattr(primary, 'next_targets') and primary.next_targets:
                fig = ChartRenderer.add_price_targets(
                    fig, 
                    primary.next_targets, 
                    remove_gaps=remove_gaps
                )
        
        # Alternative patterns
        if show_alternatives:
            alt_patterns = analysis_result.get('patterns', [])[1:3]
            alt_colors = ['#d29922', '#a371f7']
            
            for i, alt in enumerate(alt_patterns):
                waves = None
                if hasattr(alt, 'primary_waves') and alt.primary_waves:
                    waves = alt.primary_waves
                elif hasattr(alt, 'waves') and alt.waves:
                    waves = alt.waves
                
                if waves:
                    alt_name = alt.pattern_name if hasattr(alt, 'pattern_name') else 'Alt'
                    alt_conf = alt.confidence if hasattr(alt, 'confidence') else 0
                    
                    fig = ChartRenderer.add_wave_lines(
                        fig, 
                        waves,
                        color=alt_colors[i % len(alt_colors)], 
                        width=2, 
                        dash='dash',
                        name=f"Alt: {alt_name} ({alt_conf:.0f}%)",
                        remove_gaps=remove_gaps
                    )
        
        return fig