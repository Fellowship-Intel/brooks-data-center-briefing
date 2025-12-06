"""
Advanced data visualization components for market data.

Provides enhanced charts and analytics beyond basic Streamlit charts.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def render_performance_chart(
    market_data: List[Dict[str, Any]],
    title: str = "Ticker Performance",
    height: int = 400
) -> None:
    """
    Render an interactive performance chart showing price changes and volume.
    
    Args:
        market_data: List of market data dictionaries
        title: Chart title
        height: Chart height in pixels
    """
    if not market_data:
        st.info("No market data available for chart.")
        return
    
    df = pd.DataFrame(market_data)
    
    if df.empty or 'ticker' not in df.columns:
        st.info("Invalid market data format.")
        return
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Price Change (%)", "Volume vs Average Volume")
    )
    
    # Sort by absolute percent change
    if 'percent_change' in df.columns:
        df_sorted = df.copy()
        df_sorted['abs_change'] = df_sorted['percent_change'].abs()
        df_sorted = df_sorted.sort_values('abs_change', ascending=False)
        
        # Top 10 movers
        top_movers = df_sorted.head(10)
        
        # Color bars based on positive/negative change
        colors = ['#10b981' if x >= 0 else '#ef4444' for x in top_movers['percent_change']]
        
        # Price change chart
        fig.add_trace(
            go.Bar(
                x=top_movers['ticker'],
                y=top_movers['percent_change'],
                name='Price Change %',
                marker_color=colors,
                text=[f"{x:.2f}%" for x in top_movers['percent_change']],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Change: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Volume comparison chart
        if 'volume' in top_movers.columns and 'average_volume' in top_movers.columns:
            fig.add_trace(
                go.Bar(
                    x=top_movers['ticker'],
                    y=top_movers['volume'],
                    name='Volume',
                    marker_color='#10b981',
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=top_movers['ticker'],
                    y=top_movers['average_volume'],
                    name='Avg Volume',
                    marker_color='#64748b',
                    opacity=0.5
                ),
                row=2, col=1
            )
    
    # Update layout
    fig.update_layout(
        title=title,
        height=height,
        showlegend=True,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#f1f5f9'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Change (%)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(title_text="Ticker", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)


def render_volume_analysis(
    market_data: List[Dict[str, Any]],
    title: str = "Volume Analysis",
    height: int = 350
) -> None:
    """
    Render volume analysis chart comparing current volume to average.
    
    Args:
        market_data: List of market data dictionaries
        title: Chart title
        height: Chart height in pixels
    """
    if not market_data:
        st.info("No market data available for chart.")
        return
    
    df = pd.DataFrame(market_data)
    
    if df.empty or 'volume' not in df.columns or 'average_volume' not in df.columns:
        st.info("Volume data not available.")
        return
    
    # Calculate volume ratio
    df['volume_ratio'] = df['volume'] / df['average_volume']
    df_sorted = df.sort_values('volume_ratio', ascending=False).head(10)
    
    fig = go.Figure()
    
    # Add volume bars
    fig.add_trace(go.Bar(
        x=df_sorted['ticker'],
        y=df_sorted['volume'],
        name='Current Volume',
        marker_color='#10b981',
        text=[f"{x:,.0f}" for x in df_sorted['volume']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>'
    ))
    
    # Add average volume line
    fig.add_trace(go.Scatter(
        x=df_sorted['ticker'],
        y=df_sorted['average_volume'],
        mode='lines+markers',
        name='Average Volume',
        line=dict(color='#64748b', width=2, dash='dash'),
        marker=dict(size=8, color='#64748b'),
        hovertemplate='<b>%{x}</b><br>Avg Volume: %{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#f1f5f9'),
        xaxis_title="Ticker",
        yaxis_title="Volume",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_price_movement_scatter(
    market_data: List[Dict[str, Any]],
    title: str = "Price Movement vs Volume",
    height: int = 400
) -> None:
    """
    Render a scatter plot showing price movement vs volume.
    
    Args:
        market_data: List of market data dictionaries
        title: Chart title
        height: Chart height in pixels
    """
    if not market_data:
        st.info("No market data available for chart.")
        return
    
    df = pd.DataFrame(market_data)
    
    if df.empty or 'percent_change' not in df.columns or 'volume' not in df.columns:
        st.info("Required data columns not available.")
        return
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='percent_change',
        y='volume',
        size='volume',
        color='percent_change',
        hover_data=['ticker', 'company_name'],
        color_continuous_scale=['#ef4444', '#64748b', '#10b981'],
        title=title,
        labels={
            'percent_change': 'Price Change (%)',
            'volume': 'Volume',
            'ticker': 'Ticker'
        }
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="#64748b", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="#64748b", opacity=0.5)
    
    fig.update_layout(
        height=height,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#f1f5f9'),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_market_sentiment_indicator(
    market_data: List[Dict[str, Any]],
    title: str = "Market Sentiment",
    height: int = 300
) -> None:
    """
    Render a market sentiment indicator showing bullish vs bearish stocks.
    
    Args:
        market_data: List of market data dictionaries
        title: Chart title
        height: Chart height in pixels
    """
    if not market_data:
        st.info("No market data available for chart.")
        return
    
    df = pd.DataFrame(market_data)
    
    if df.empty or 'percent_change' not in df.columns:
        st.info("Price change data not available.")
        return
    
    # Categorize stocks
    bullish = len(df[df['percent_change'] > 0])
    bearish = len(df[df['percent_change'] < 0])
    neutral = len(df[df['percent_change'] == 0])
    
    # Create gauge chart
    total = len(df)
    bullish_pct = (bullish / total * 100) if total > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=bullish_pct,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#10b981" if bullish_pct >= 50 else "#ef4444"},
            'steps': [
                {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.2)"},
                {'range': [50, 100], 'color': "rgba(16, 185, 129, 0.2)"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(
        height=height,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#f1f5f9')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show breakdown
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bullish", bullish, f"{bullish_pct:.1f}%")
    with col2:
        st.metric("Bearish", bearish, f"{(bearish/total*100):.1f}%" if total > 0 else "0%")
    with col3:
        st.metric("Neutral", neutral, f"{(neutral/total*100):.1f}%" if total > 0 else "0%")


def render_comparative_analysis(
    market_data: List[Dict[str, Any]],
    compare_field: str = "percent_change",
    title: str = "Comparative Analysis",
    height: int = 400
) -> None:
    """
    Render a comparative analysis chart for multiple metrics.
    
    Args:
        market_data: List of market data dictionaries
        compare_field: Field to compare (e.g., 'percent_change', 'volume')
        title: Chart title
        height: Chart height in pixels
    """
    if not market_data:
        st.info("No market data available for chart.")
        return
    
    df = pd.DataFrame(market_data)
    
    if df.empty or compare_field not in df.columns:
        st.info(f"Field '{compare_field}' not available in data.")
        return
    
    # Sort and get top 10
    df_sorted = df.nlargest(10, compare_field)
    
    fig = go.Figure()
    
    # Create horizontal bar chart for better readability
    fig.add_trace(go.Bar(
        x=df_sorted[compare_field],
        y=df_sorted['ticker'],
        orientation='h',
        marker=dict(
            color=df_sorted[compare_field],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title=compare_field.replace('_', ' ').title())
        ),
        text=[f"{x:.2f}" for x in df_sorted[compare_field]],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>%{x:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0)',
        plot_bgcolor='rgba(15, 23, 42, 0)',
        font=dict(color='#f1f5f9'),
        xaxis_title=compare_field.replace('_', ' ').title(),
        yaxis_title="Ticker",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

