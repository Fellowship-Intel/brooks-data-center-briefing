"""
Main Streamlit application for Brooks Data Center Daily Briefing
"""
import streamlit as st
import json
import sys
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

# Add the python_app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Auto-setup GCP credentials if not already set
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    default_creds_path = Path(__file__).parent / ".secrets" / "app-backend-sa.json"
    if default_creds_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(default_creds_path)

# Set default project ID if not set
if not os.getenv("GCP_PROJECT_ID"):
    os.environ["GCP_PROJECT_ID"] = "mikebrooks"

# Import heavy modules (cached by Python's import system after first load)
import pandas as pd
from python_app.types import (
    InputData, DailyReportResponse, MarketData, NewsItem,
    MiniReport, AppMode, ChatMessage
)
from python_app.constants import SAMPLE_INPUT, DEFAULT_WATCHLIST, DEFAULT_CLIENT_ID
from python_app.services.gemini_service import (
    generate_daily_report, send_chat_message
)
from python_app.utils import dict_to_market_data, dict_to_news_item
from report_service import (
    generate_watchlist_daily_report,
    get_daily_movers_for_watchlist,
    get_audio_bytes_from_gcs,
)
from report_repository import get_daily_report


# Page configuration
st.set_page_config(
    page_title="Brooks Data Center Briefing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS for dark theme with vibrant colors
st.markdown("""
<style>
    /* Base styling with improved text rendering */
    html, body, [class*="css"] {
        font-size: 16pt !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 
                     'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* App background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f1f5f9;
    }
    
    /* Headers with vibrant colors and improved clarity */
    h1, h2, h3, h4, h5, h6 {
        color: #10b981 !important;
        font-weight: 700 !important;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
        letter-spacing: -0.02em;
    }
    
    h1 {
        font-size: 2.5rem;
        border-bottom: 3px solid #10b981;
        padding-bottom: 0.5rem;
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        border-image: linear-gradient(135deg, #10b981 0%, #34d399 100%) 1;
    }
    
    h2 {
        font-size: 2rem;
        color: #34d399 !important;
    }
    
    h3 {
        font-size: 1.5rem;
        color: #6ee7b7 !important;
    }
    
    /* Text inputs with vibrant focus states */
    .stTextInput > div > div > input {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 2px solid #334155 !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem !important;
        font-weight: 500 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3), 0 0 20px rgba(16, 185, 129, 0.2) !important;
        outline: none !important;
    }
    
    /* Text areas with vibrant focus states */
    .stTextArea > div > div > textarea {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 2px solid #334155 !important;
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3), 0 0 20px rgba(16, 185, 129, 0.2) !important;
        outline: none !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div > select {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 0.5rem !important;
    }
    
    /* Buttons with vibrant colors and glow effects */
    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
        color: #0f172a !important;
        border: none !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
        text-shadow: none !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6) !important;
    }
    
    /* Date input */
    .stDateInput > div > div > input {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 0.5rem !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1e293b !important;
    }
    
    /* Logo styling - clean and prominent */
    .stSidebar img {
        max-width: 100% !important;
        height: auto !important;
        margin: 0 auto !important;
        display: block !important;
        border-radius: 0.75rem !important;
        filter: drop-shadow(0 4px 12px rgba(16, 185, 129, 0.3));
        transition: all 0.3s ease !important;
    }
    
    .stSidebar img:hover {
        filter: drop-shadow(0 6px 20px rgba(16, 185, 129, 0.5));
        transform: scale(1.02);
    }
    
    .stSidebar [data-testid="stImage"] {
        padding: 0 !important;
        margin: 0 auto !important;
        background: transparent !important;
    }
    
    /* Logo container styling - clean transparent background */
    .stSidebar [data-testid="stMarkdownContainer"]:has(img) {
        background-color: transparent !important;
        padding: 0.5rem 0 !important;
    }
    
    /* Metrics with vibrant colors */
    [data-testid="stMetricValue"] {
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2rem !important;
        font-weight: 800 !important;
        text-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
    }
    
    [data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
    }
    
    /* Dataframes */
    .stDataFrame {
        background-color: #1e293b !important;
        border-radius: 0.5rem !important;
    }
    
    /* Tabs with vibrant colors */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e293b !important;
        border-radius: 0.5rem !important;
        padding: 0.25rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #cbd5e1 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(52, 211, 153, 0.1) 100%) !important;
        color: #34d399 !important;
        border-bottom: 3px solid #10b981 !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border-radius: 0.5rem !important;
    }
    
    /* Code blocks */
    code {
        background-color: #1e293b !important;
        color: #10b981 !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 0.25rem !important;
    }
    
    pre {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    /* Markdown with improved readability */
    .stMarkdown {
        color: #f1f5f9 !important;
        line-height: 1.7 !important;
        font-weight: 400 !important;
    }
    
    .stMarkdown strong {
        color: #34d399 !important;
        font-weight: 700 !important;
        text-shadow: 0 0 8px rgba(52, 211, 153, 0.3);
    }
    
    .stMarkdown p {
        color: #e2e8f0 !important;
        margin-bottom: 1rem !important;
    }
    
    .stMarkdown li {
        color: #e2e8f0 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Success/Info/Error boxes with vibrant colors */
    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(52, 211, 153, 0.1) 100%) !important;
        border-left: 4px solid #10b981 !important;
        border-radius: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2) !important;
        color: #d1fae5 !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(96, 165, 250, 0.1) 100%) !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2) !important;
        color: #dbeafe !important;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(248, 113, 113, 0.1) 100%) !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2) !important;
        color: #fee2e2 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #10b981 !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
    
    /* Cards/Containers */
    .element-container {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border-radius: 0.75rem !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        border: 1px solid rgba(51, 65, 85, 0.5) !important;
    }
    
    /* Links with vibrant colors */
    a {
        color: #34d399 !important;
        text-decoration: none !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    a:hover {
        color: #10b981 !important;
        text-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        text-decoration: underline !important;
    }
    
    /* Chat messages styling */
    .stChatMessage {
        padding: 1rem !important;
        border-radius: 0.75rem !important;
    }
    
    /* Caption text */
    .stCaption {
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar text */
    .stSidebar .stMarkdown {
        color: #e2e8f0 !important;
    }
    
    /* General text improvements */
    p, span, div {
        color: #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state() -> None:
    """Initialize Streamlit session state with default values."""
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = DEFAULT_WATCHLIST.copy()
    if 'mode' not in st.session_state:
        st.session_state.mode = AppMode.INPUT
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None
    if 'market_data_input' not in st.session_state:
        st.session_state.market_data_input = []
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'is_initializing' not in st.session_state:
        st.session_state.is_initializing = True
    if 'chat_input' not in st.session_state:
        st.session_state.chat_input = ''


@st.cache_data(ttl=3600)  # Cache for 1 hour - speeds up repeated loads
def load_sample_data():
    """Load sample input data - cached for performance."""
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


def render_logo():
    """Render the Fellowship Intelligence logo in the sidebar with clean, colorful styling."""
    logo_path = Path("static/images/logo.png")
    
    with st.sidebar:
        if logo_path.exists():
            # Display logo with clean transparent background (no container needed since logo is transparent)
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0.5rem; margin-bottom: 1.5rem;">
            """, unsafe_allow_html=True)
            
            st.image(
                str(logo_path),
                use_container_width=True
            )
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback: Show text logo if image not found with vibrant colors
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0.5rem; margin-bottom: 1.5rem;">
                <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(52, 211, 153, 0.1) 100%); padding: 1.5rem; border-radius: 0.75rem; border: 2px solid rgba(16, 185, 129, 0.3); box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);">
                    <h2 style="background: linear-gradient(135deg, #10b981 0%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0.5rem 0; font-size: 1.75rem; font-weight: 700; text-shadow: 0 0 20px rgba(16, 185, 129, 0.4);">Fellowship</h2>
                    <h3 style="color: #6ee7b7; margin: 0.5rem 0; font-size: 1.3rem; font-weight: 600;">Intelligence</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")  # Divider


def render_watchlist():
    """Render the watchlist component in the sidebar."""
    with st.sidebar:
        st.subheader("Watchlist")
        
        # Show current watchlist with remove buttons
        for ticker in list(st.session_state.watchlist):
            cols = st.columns([3, 1])
            cols[0].write(ticker)
            if cols[1].button("✕", key=f"remove_{ticker}"):
                st.session_state.watchlist = [
                    t for t in st.session_state.watchlist if t != ticker
                ]
                st.rerun()
        
        # Add new ticker
        new_ticker = st.text_input("Add ticker", key="add_ticker_input").upper().strip()
        if st.button("Add", key="add_ticker_btn") and new_ticker:
            if new_ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker)
                st.rerun()


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


def render_chat_ui() -> None:
    """
    Render the Gemini chat interface inside the current Streamlit container.
    
    Extracted so app.py can simply call this on the 'AI Chat' tab.
    Handles conversation history, user input, and AI responses using the
    existing Gemini chat session.
    """
    st.header("Gemini AI Chat")
    st.caption("Ask Gemini about today's data center and AI markets.")
    
    # Display conversation history
    if st.session_state.chat_messages:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg.role):
                st.markdown(msg.text)
    else:
        # Show welcome message if no conversation history
        st.info("💡 Start a conversation by asking about market data, tickers, or reports.")
    
    # Chat input at the bottom
    user_input = st.chat_input("Ask a question about the market...")
    
    if user_input:
        # Add user message to history
        user_msg = ChatMessage(role='user', text=user_input)
        st.session_state.chat_messages.append(user_msg)
        
        # Display user message immediately
        with st.chat_message('user'):
            st.markdown(user_input)
        
        # Generate and display AI response
        with st.chat_message('model'):
            try:
                with st.spinner("Thinking..."):
                    response = send_chat_message(user_input)
                    bot_msg = ChatMessage(role='model', text=response)
                    st.session_state.chat_messages.append(bot_msg)
                    st.markdown(response)
                    
                    # Write chat response to file for logging
                    result_text = f"Q: {user_input}\nA: {response}\n\n"
                    with open("output.txt", "a", encoding="utf-8") as f:
                        f.write(result_text)
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                # Add error message to chat history
                st.session_state.chat_messages.append(
                    ChatMessage(role='model', text=error_msg)
                )


def get_daily_movers_for_watchlist(
    watchlist: list[str],
    trading_date: date,
) -> pd.DataFrame:
    """
    Get daily movers data for the watchlist tickers.
    
    This function attempts to fetch market data from:
    1. Session state (if available from previous report generation)
    2. Firestore (if a report exists for the trading date)
    3. Returns empty DataFrame with expected columns if no data found
    
    Args:
        watchlist: List of ticker symbols
        trading_date: Trading date to fetch data for
        
    Returns:
        DataFrame with columns: ticker, company_name, previous_close, open, high, low, 
        close, volume, average_volume, percent_change, intraday_range, market_cap
    """
    # First, try to get from session state if available
    if 'market_data_input' in st.session_state and st.session_state.market_data_input:
        market_data = st.session_state.market_data_input
        # Filter to watchlist tickers
        filtered_data = [
            md for md in market_data 
            if md.get('ticker') in watchlist
        ]
        if filtered_data:
            return pd.DataFrame(filtered_data)
    
    # Try to fetch from Firestore if a report exists
    try:
        report = get_daily_report(trading_date.isoformat())
        if report and 'raw_payload' in report:
            raw_payload = report.get('raw_payload', {})
            market_data_list = raw_payload.get('market_data', [])
            if market_data_list:
                # Filter to watchlist tickers
                filtered_data = [
                    md for md in market_data_list
                    if isinstance(md, dict) and md.get('ticker') in watchlist
                ]
                if filtered_data:
                    return pd.DataFrame(filtered_data)
    except Exception:
        # If Firestore fetch fails, continue to return empty DataFrame
        pass
    
    # Return empty DataFrame with expected columns
    return pd.DataFrame(columns=[
        'ticker', 'company_name', 'previous_close', 'open', 'high', 'low',
        'close', 'volume', 'average_volume', 'percent_change', 'intraday_range', 'market_cap'
    ])


def render_dashboard_tab() -> None:
    """Render the Dashboard tab showing daily movers."""
    st.header("Daily Movers - Data Center & AI Sectors")
    
    # Add prominent button to generate daily market report
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Daily Market Report", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                trading_date = date.today()
                
                # Market data: ~1.4s (18% of total)
                status_text.text("📊 Fetching market data...")
                progress_bar.progress(18)
                
                # Gemini text: ~3.2s (42% of total)
                status_text.text("🤖 Generating AI report text...")
                progress_bar.progress(60)
                
                # TTS + Firestore + GCS: ~3.1s (40% of total)
                status_text.text("🎙️ Generating audio and saving report...")
                progress_bar.progress(90)
                
                report = generate_watchlist_daily_report(
                    trading_date=trading_date,
                    client_id=DEFAULT_CLIENT_ID,
                    watchlist=st.session_state.watchlist,
                )
                
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                
                st.success("✅ Daily market report generated successfully!")
                st.info("Check the 'Daily Watchlist Report' tab to view the full report.")
                st.rerun()
            except Exception as e:
                progress_bar.progress(0)
                status_text.empty()
                st.error(f"Error generating report: {str(e)}")
    
    st.markdown("---")
    
    trading_date = st.date_input(
        "Trading date", value=date.today(), key="dashboard_trading_date"
    )
    
    # Get daily movers for watchlist
    movers_df = get_daily_movers_for_watchlist(
        watchlist=st.session_state.watchlist,
        trading_date=trading_date,
    )
    
    st.caption("Ranked by intraday price volatility and volume.")
    
    if not movers_df.empty:
        # Calculate volatility metric (absolute percent change)
        if 'percent_change' in movers_df.columns:
            movers_df = movers_df.copy()
            movers_df['abs_change'] = movers_df['percent_change'].abs()
            movers_df = movers_df.sort_values('abs_change', ascending=False)
        
        st.dataframe(movers_df, use_container_width=True)
        
        # Show chart if we have data
        if 'percent_change' in movers_df.columns and 'volume' in movers_df.columns:
            chart_data = movers_df.set_index('ticker')[['volume', 'percent_change']]
            st.bar_chart(chart_data)
    else:
        st.info("No market data available for the selected date. Generate a report first to populate data.")


def render_watchlist_report_tab() -> None:
    """Render the Daily Watchlist Report tab."""
    st.header("Daily Watchlist Report")
    
    trading_date = st.date_input(
        "Trading date", value=date.today(), key="report_trading_date"
    )
    
    if st.button("Generate today's watchlist report"):
        with st.spinner("Generating report..."):
            try:
                report = generate_watchlist_daily_report(
                    trading_date=trading_date,
                    client_id=DEFAULT_CLIENT_ID,
                    watchlist=st.session_state.watchlist,
                )
                
                summary_text = report.get("summary_text", "")
                key_insights = report.get("key_insights", [])
                audio_gcs_path = report.get("audio_gcs_path")
                
                st.subheader("Summary")
                st.write(summary_text)
                
                if key_insights:
                    st.subheader("Key Insights")
                    for item in key_insights:
                        st.markdown(f"- {item}")
                
                if audio_gcs_path:
                    st.subheader("Audio (3–5 minutes)")

                    try:
                        audio_bytes = get_audio_bytes_from_gcs(audio_gcs_path)
                        st.audio(audio_bytes, format="audio/wav")
                    except Exception as exc:
                        st.error(f"Unable to load audio from GCS: {exc}")
                        st.write(f"GCS path: `{audio_gcs_path}`")
                
                st.success("Report generated successfully!")
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    else:
        st.info("Click the button above to generate a report for your watchlist.")


def render_ai_chat_tab() -> None:
    """Render the AI Chat tab."""
    render_chat_ui()


def main() -> None:
    """Main application entry point."""
    init_session_state()
    
    # Logo in sidebar (at the top) - DISABLED
    # render_logo()
    
    st.title("Brooks Data Center Daily Briefing")
    
    tab_dashboard, tab_report, tab_chat = st.tabs(
        ["Dashboard", "Daily Watchlist Report", "AI Chat"]
    )
    
    with tab_dashboard:
        render_dashboard_tab()
    
    with tab_report:
        render_watchlist_report_tab()
    
    with tab_chat:
        render_ai_chat_tab()
    
    # Watchlist in sidebar (always visible)
    render_watchlist()


if __name__ == "__main__":
    main()

