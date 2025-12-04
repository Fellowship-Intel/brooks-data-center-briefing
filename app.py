"""
Main Streamlit application for Brooks Data Center Daily Briefing
"""
import streamlit as st
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the python_app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from python_app.types import (
    InputData, DailyReportResponse, MarketData, NewsItem,
    MiniReport, AppMode, ChatMessage
)
from python_app.constants import SAMPLE_INPUT
from python_app.services.gemini_service import (
    generate_daily_report, send_chat_message
)
from python_app.utils import dict_to_market_data, dict_to_news_item


# Page configuration
st.set_page_config(
    page_title="Brooks Data Center Briefing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stApp {
        background-color: #0f172a;
        color: #f1f5f9;
    }
    h1, h2, h3 {
        color: #10b981;
    }
    .stTextInput > div > div > input {
        background-color: #1e293b;
        color: #f1f5f9;
    }
    .stTextArea > div > div > textarea {
        background-color: #1e293b;
        color: #f1f5f9;
    }
    .stSelectbox > div > div > select {
        background-color: #1e293b;
        color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'mode' not in st.session_state:
    st.session_state.mode = AppMode.INPUT
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
if 'market_data_input' not in st.session_state:
    st.session_state.market_data_input = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'is_initializing' not in st.session_state:
    st.session_state.is_initializing = True
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ''


def load_sample_data():
    """Load sample input data."""
    return {
        'trading_date': SAMPLE_INPUT.trading_date,
        'tickers': ', '.join(SAMPLE_INPUT.tickers_tracked),
        'market_json': json.dumps([], indent=2),
        'news_json': json.dumps([], indent=2),
        'macro_context': SAMPLE_INPUT.macro_context,
        'constraints': SAMPLE_INPUT.constraints_or_notes
    }


def parse_json_safely(json_str: str, field_name: str):
    """Safely parse JSON string."""
    if not json_str or not json_str.strip():
        return []
    try:
        parsed = json.loads(json_str)
        if not isinstance(parsed, list):
            raise ValueError(f"{field_name} must be a JSON array")
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {field_name}: {str(e)}")


def render_input_form():
    """Render the input form component."""
    st.title("📊 Daily Briefing Generator")
    st.markdown("Enter market data to generate today's briefing package.")
    
    sample_data = load_sample_data()
    
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            trading_date = st.date_input(
                "Trading Date",
                value=datetime.fromisoformat(sample_data['trading_date']).date(),
                help="Example: 2025-12-01"
            )
        
        with col2:
            tickers = st.text_area(
                "Tickers Tracked",
                value=sample_data['tickers'],
                height=80,
                help="Must always include SMCI, CRVW, NBIS, IREN.",
                placeholder="EQIX, DLR, AMZN, MSFT, NVDA, SMCI, IRM, GDS, CRVW, NBIS, IREN"
            )
        
        market_json_str = st.text_area(
            "Market Data JSON",
            value=sample_data['market_json'],
            height=200,
            help="Full per-ticker market data JSON. Leave as [] to auto-fetch.",
            placeholder='[] (Leave empty to fetch live data via AI)'
        )
        
        news_json_str = st.text_area(
            "News JSON",
            value=sample_data['news_json'],
            height=200,
            help="Array of news items. Leave as [] to auto-fetch.",
            placeholder='[] (Leave empty to fetch live data via AI)'
        )
        
        col3, col4 = st.columns(2)
        with col3:
            macro_context = st.text_area(
                "Macro Context",
                value=sample_data['macro_context'],
                height=120
            )
        with col4:
            constraints = st.text_area(
                "Constraints or Notes",
                value=sample_data['constraints'],
                height=120
            )
        
        submitted = st.form_submit_button(
            "Generate Daily Briefing Package",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            try:
                market_data_list = parse_json_safely(market_json_str, "Market Data JSON")
                news_data_list = parse_json_safely(news_json_str, "News JSON")
                
                # Convert to typed objects
                market_data_objs = [dict_to_market_data(m) for m in market_data_list]
                news_data_objs = [dict_to_news_item(n) for n in news_data_list]
                
                input_data = InputData(
                    trading_date=str(trading_date),
                    tickers_tracked=[t.strip() for t in tickers.split(',') if t.strip()],
                    market_data_json=market_data_objs,
                    news_json=news_data_objs,
                    macro_context=macro_context,
                    constraints_or_notes=constraints
                )
                
                with st.spinner("Generating Analysis..."):
                    response = generate_daily_report(input_data)
                    st.session_state.report_data = response
                    st.session_state.market_data_input = market_data_list
                    
                    # Update market data if AI fetched new data
                    if response.updated_market_data:
                        st.session_state.market_data_input = [
                            {
                                'ticker': m.ticker,
                                'company_name': m.company_name,
                                'previous_close': m.previous_close,
                                'open': m.open,
                                'high': m.high,
                                'low': m.low,
                                'close': m.close,
                                'volume': m.volume,
                                'average_volume': m.average_volume,
                                'percent_change': m.percent_change,
                                'intraday_range': m.intraday_range,
                                'market_cap': m.market_cap
                            }
                            for m in response.updated_market_data
                        ]
                    
                    # Write report output to file
                    result_text = f"""Daily Briefing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Trading Date: {input_data.trading_date}

=== FULL REPORT ===
{response.report_markdown}

=== CORE TICKERS DEEP DIVE ===
{response.core_tickers_in_depth_markdown}

=== AUDIO REPORT ===
{response.audio_report}

=== TOP MOVERS ===
"""
                    for report in response.reports:
                        result_text += f"""
{report.ticker} - {report.company_name}
{report.section_title}
Snapshot: {report.snapshot}
Catalyst: {report.catalyst_and_context}
Trading Lens: {report.day_trading_lens}
Watch Next: {', '.join(report.watch_next_bullets) if report.watch_next_bullets else 'N/A'}
---
"""
                    
                    with open("output.txt", "w", encoding="utf-8") as f:
                        f.write(result_text)
                    
                    st.session_state.mode = AppMode.REPORT
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_audio_player(audio_text: str):
    """Render audio player component."""
    st.markdown("### 🔊 Audio Briefing")
    if audio_text:
        # Streamlit doesn't have built-in TTS, so we'll use a simple text display
        # For full TTS, you'd need to integrate with pyttsx3 or similar
        with st.expander("View Audio Script"):
            st.text(audio_text)
        
        # Option to copy for external TTS
        st.code(audio_text, language=None)
    else:
        st.warning("No audio report available.")


def render_report_view(report_data: DailyReportResponse, market_data: list):
    """Render the report view component."""
    tab1, tab2, tab3 = st.tabs(["Top Movers", "Deep Dive (Core)", "Full Narrative"])
    
    with tab1:
        st.header("Top Movers")
        
        # Chart for top movers
        if market_data:
            import pandas as pd
            df = pd.DataFrame(market_data)
            if not df.empty and 'percent_change' in df.columns:
                df_sorted = df.copy()
                df_sorted['abs_change'] = df_sorted['percent_change'].abs()
                top_movers = df_sorted.nlargest(5, 'abs_change')
                
                st.bar_chart(
                    top_movers.set_index('ticker')[['volume', 'average_volume']],
                    height=300
                )
        
        # Display mini reports
        if report_data.reports:
            cols = st.columns(min(3, len(report_data.reports)))
            for idx, report in enumerate(report_data.reports[:3]):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"### {report.ticker}")
                        st.caption(report.company_name)
                        st.markdown(f"**{report.section_title}**")
                        st.markdown(f"**Snapshot:** {report.snapshot}")
                        st.markdown(f"**Catalyst:** {report.catalyst_and_context}")
                        st.markdown(f"**Trading Lens:** {report.day_trading_lens}")
                        if report.watch_next_bullets:
                            st.markdown("**Watch Next:**")
                            for bullet in report.watch_next_bullets:
                                st.markdown(f"- {bullet}")
                        st.divider()
        else:
            st.info("No ticker reports generated.")
    
    with tab2:
        st.header("Core Tickers Deep Dive")
        if report_data.core_tickers_in_depth_markdown:
            st.markdown(report_data.core_tickers_in_depth_markdown)
        else:
            st.info("No deep dive content available.")
    
    with tab3:
        st.header("Full Narrative")
        if report_data.report_markdown:
            st.markdown(report_data.report_markdown)
        else:
            st.info("No narrative content available.")


def render_chat_interface():
    """Render the chat interface component."""
    st.sidebar.header("💬 Analyst Q&A")
    st.sidebar.caption("Ask about today's data")
    
    # Display messages
    for msg in st.session_state.chat_messages:
        with st.sidebar.chat_message(msg.role):
            st.markdown(msg.text)
    
    # Chat input
    user_input = st.sidebar.chat_input("Ask a follow-up...")
    
    if user_input:
        user_msg = ChatMessage(role='user', text=user_input)
        st.session_state.chat_messages.append(user_msg)
        
        with st.sidebar.chat_message('user'):
            st.markdown(user_input)
        
        with st.sidebar.chat_message('model'):
            try:
                with st.spinner("Thinking..."):
                    response = send_chat_message(user_input)
                    bot_msg = ChatMessage(role='model', text=response)
                    st.session_state.chat_messages.append(bot_msg)
                    st.markdown(response)
                    
                    # Write chat response to file
                    result_text = f"Q: {user_input}\nA: {response}\n\n"
                    with open("output.txt", "a", encoding="utf-8") as f:
                        f.write(result_text)
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_messages.append(
                    ChatMessage(role='model', text=error_msg)
                )


# Main app logic
if st.session_state.is_initializing:
    st.session_state.is_initializing = False
    try:
        with st.spinner("Initializing Market Intelligence..."):
            response = generate_daily_report(SAMPLE_INPUT)
            st.session_state.report_data = response
            st.session_state.mode = AppMode.REPORT
            if response.updated_market_data:
                st.session_state.market_data_input = [
                    {
                        'ticker': m.ticker,
                        'company_name': m.company_name,
                        'previous_close': m.previous_close,
                        'open': m.open,
                        'high': m.high,
                        'low': m.low,
                        'close': m.close,
                        'volume': m.volume,
                        'average_volume': m.average_volume,
                        'percent_change': m.percent_change,
                        'intraday_range': m.intraday_range,
                        'market_cap': m.market_cap
                    }
                    for m in response.updated_market_data
                ]
            
            # Write initial report output to file
            result_text = f"""Daily Briefing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Trading Date: {SAMPLE_INPUT.trading_date}

=== FULL REPORT ===
{response.report_markdown}

=== CORE TICKERS DEEP DIVE ===
{response.core_tickers_in_depth_markdown}

=== AUDIO REPORT ===
{response.audio_report}

=== TOP MOVERS ===
"""
            for report in response.reports:
                result_text += f"""
{report.ticker} - {report.company_name}
{report.section_title}
Snapshot: {report.snapshot}
Catalyst: {report.catalyst_and_context}
Trading Lens: {report.day_trading_lens}
Watch Next: {', '.join(report.watch_next_bullets) if report.watch_next_bullets else 'N/A'}
---
"""
            
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write(result_text)
    except Exception as e:
        st.error(f"Auto-initialization failed: {str(e)}")
        st.session_state.mode = AppMode.INPUT


# Render based on mode
if st.session_state.mode == AppMode.INPUT:
    render_input_form()
else:
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("Daily Briefing for Michael Brooks")
    with col2:
        if st.button("🔄 New Report"):
            st.session_state.mode = AppMode.INPUT
            st.session_state.report_data = None
            st.session_state.chat_messages = []
            st.rerun()
    
    if st.session_state.report_data:
        # Audio player
        render_audio_player(st.session_state.report_data.audio_report)
        st.divider()
        
        # Main report
        render_report_view(
            st.session_state.report_data,
            st.session_state.market_data_input
        )
        
        # Chat interface in sidebar
        render_chat_interface()

