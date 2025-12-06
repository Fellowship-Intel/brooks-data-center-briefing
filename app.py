"""
Main Streamlit application for Brooks Data Center Daily Briefing
"""
import streamlit as st
import json
import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import logging

# Add the python_app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Auto-setup and initialization
from python_app.utils.setup import init_app
init_app()

# Get logger (configured in init_app)
logger = logging.getLogger(__name__)

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
from python_app.components.dashboard import render_dashboard
from python_app.components.status_indicators import render_status_indicators
from python_app.components.progress import create_progress_tracker
from python_app.components.keyboard_shortcuts import render_keyboard_shortcuts_help
from python_app.utils.api_client import (
    generate_report as api_generate_report,
    generate_watchlist_report as api_generate_watchlist_report,
    send_chat_message as api_send_chat_message,
)
from report_service import (
    generate_watchlist_daily_report,
    get_daily_movers_for_watchlist,
    get_audio_bytes_from_gcs,
)
from utils.rate_limiter import (
    _report_generation_limiter,
    check_rate_limit,
)
from report_repository import get_daily_report
from gcp_clients import get_firestore_client
from python_app.utils.auth_handler import handle_auth, get_current_user
from python_app.services.alert_service import AlertService, ConditionType
from python_app.services.market_data_service import fetch_watchlist_intraday_data

# Import error tracking placeholders if needed for types, though init_app handles init
# We define no-op capture_exception/set_user_context locally if import fails
# to satisfy local usage in app.py if any. 
# Checking app.py usage: it imports them from utils.error_tracking in try/except block originally.
# We should probably keep the try/except for the symbols if they are used in app.py logic
try:
    from utils.error_tracking import capture_exception, set_user_context
    _error_tracking_available = True
except ImportError:
    _error_tracking_available = False
    def capture_exception(*args, **kwargs): pass
    def set_user_context(*args, **kwargs): pass


# Enhanced Custom CSS for dark theme with vibrant colors
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    load_css('static/style_enhanced.css')
except FileNotFoundError:
    logger.warning("static/style_enhanced.css not found. Falling back to default styles.")


def init_session_state(client_id: str = DEFAULT_CLIENT_ID) -> None:
    """Initialize Streamlit session state with default values."""
    if "client_id" not in st.session_state:
        st.session_state.client_id = client_id
    
    if "watchlist" not in st.session_state:
        # Try to load from Firestore, fall back to default
        st.session_state.watchlist = _load_watchlist_from_firestore(client_id)
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
    if 'auto_report_loaded' not in st.session_state:
        st.session_state.auto_report_loaded = False
    if 'active_report_date' not in st.session_state:
        st.session_state.active_report_date = None


def load_active_report_automatically() -> None:
    """
    Automatically load the active report based on the report generation schedule.
    
    - If current time is before 3:55am, loads yesterday's report
    - If current time is after 3:55am, loads today's report
    - If today's report doesn't exist after 3:55am, automatically generates it
    """
    # Only load once per session
    if st.session_state.get('auto_report_loaded', False):
        return
    
    # Only load if we don't already have report data
    if st.session_state.get('report_data') is not None:
        st.session_state.auto_report_loaded = True
        return
    
    try:
        from utils.report_date_utils import get_active_report_date, is_after_report_cutoff_time
        from config import get_config
        
        # Note: DailyReportResponse, MiniReport, MarketData are already imported at module level
        # (line 31-33), so we can use them directly without re-importing
        
        config = get_config()
        
        # Determine which report date should be active
        active_date = get_active_report_date(
            hour=config.report_generation_hour,
            minute=config.report_generation_minute,
            timezone_name=config.report_timezone
        )
        
        st.session_state.active_report_date = active_date
        report_date_str = active_date.isoformat()
        
        logger.info(f"Auto-loading report for date: {report_date_str}")
        
        # Try to fetch report from Firestore
        report = get_daily_report(report_date_str)
        
        if report:
            # Mark as loaded
            st.session_state.auto_report_loaded = True
            
            # Convert Firestore report to DailyReportResponse format
            # (imports are now at the top of the function)
            
            # Check if we have raw_payload (preferred - contains full DailyReportResponse)
            if report.get('raw_payload'):
                raw_payload = report['raw_payload']
                
                # Convert reports list
                reports = []
                if 'reports' in raw_payload:
                    reports = [MiniReport(**r) for r in raw_payload['reports']]
                
                # Convert updated_market_data if available
                updated_market_data = None
                if 'updated_market_data' in raw_payload and raw_payload['updated_market_data']:
                    updated_market_data = [MarketData(**m) for m in raw_payload['updated_market_data']]
                
                report_response = DailyReportResponse(
                    report_markdown=raw_payload.get('report_markdown', ''),
                    core_tickers_in_depth_markdown=raw_payload.get('core_tickers_in_depth_markdown', ''),
                    reports=reports,
                    audio_report=raw_payload.get('audio_report', ''),
                    updated_market_data=updated_market_data
                )
                
                st.session_state.report_data = report_response
                
                # Set market data if available
                if updated_market_data:
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
                        for m in updated_market_data
                    ]
                
                # Set mode to REPORT so it displays automatically
                st.session_state.mode = AppMode.REPORT
                
                logger.info(f"Successfully loaded report for {report_date_str} from Firestore")
            else:
                # Fallback: construct from individual fields if raw_payload doesn't exist
                reports = []
                tickers = report.get('tickers', [])
                insights = report.get('key_insights', [])
                
                for idx, insight in enumerate(insights):
                    ticker = tickers[idx] if idx < len(tickers) else 'N/A'
                    reports.append(MiniReport(
                        ticker=ticker,
                        company_name='',
                        section_title='',
                        snapshot=insight,
                        catalyst_and_context='',
                        day_trading_lens='',
                        watch_next_bullets=[]
                    ))
                
                report_response = DailyReportResponse(
                    report_markdown=report.get('summary_text', ''),
                    core_tickers_in_depth_markdown=report.get('market_context', ''),
                    reports=reports,
                    audio_report='',
                    updated_market_data=None
                )
                
                st.session_state.report_data = report_response
                st.session_state.mode = AppMode.REPORT
                logger.info(f"Loaded report for {report_date_str} from Firestore (constructed from fields)")
        else:
            # Report doesn't exist
            # If it's after cutoff time, auto-generate the report
            if is_after_report_cutoff_time(
                hour=config.report_generation_hour,
                minute=config.report_generation_minute,
                timezone_name=config.report_timezone
            ):
                logger.info(f"Report for {report_date_str} not found. Auto-generating...")
                
                # Show progress indicator
                with st.spinner("Auto-generating today's report..."):
                    try:
                        # Generate report using watchlist
                        report = generate_watchlist_daily_report(
                            trading_date=active_date,
                            client_id=st.session_state.get('client_id', DEFAULT_CLIENT_ID),
                            watchlist=st.session_state.watchlist,
                        )
                        
                        # Reload the report we just generated
                        generated_report = get_daily_report(report_date_str)
                        if generated_report and generated_report.get('raw_payload'):
                            raw_payload = generated_report['raw_payload']
                            
                            reports = []
                            if 'reports' in raw_payload:
                                reports = [MiniReport(**r) for r in raw_payload['reports']]
                            
                            updated_market_data = None
                            if 'updated_market_data' in raw_payload and raw_payload['updated_market_data']:
                                updated_market_data = [MarketData(**m) for m in raw_payload['updated_market_data']]
                            
                            report_response = DailyReportResponse(
                                report_markdown=raw_payload.get('report_markdown', ''),
                                core_tickers_in_depth_markdown=raw_payload.get('core_tickers_in_depth_markdown', ''),
                                reports=reports,
                                audio_report=raw_payload.get('audio_report', ''),
                                updated_market_data=updated_market_data
                            )
                            
                            st.session_state.report_data = report_response
                            
                            if updated_market_data:
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
                                    for m in updated_market_data
                                ]
                            
                            st.session_state.mode = AppMode.REPORT
                            st.session_state.auto_report_loaded = True
                            
                            logger.info(f"Successfully auto-generated and loaded report for {report_date_str}")
                            st.success("✅ Today's report has been automatically generated!")
                    except Exception as e:
                        logger.error(f"Failed to auto-generate report: {e}", exc_info=True)
                        # Don't set auto_report_loaded on error so it can retry
                        from utils.user_messages import get_user_friendly_error
                        friendly_message = get_user_friendly_error(e, context={"error_type": "report"})
                        st.warning(friendly_message)
            else:
                # Before cutoff time and no report - this is expected, just mark as attempted
                logger.info(f"No report found for {report_date_str} (before cutoff time - expected)")
                st.session_state.auto_report_loaded = True
                
    except Exception as e:
        logger.warning(f"Failed to auto-load report: {str(e)}", exc_info=True)
        # Don't set auto_report_loaded on error so it can retry on next load
        # Continue without breaking the app - don't show error to user for auto-load failures


@st.cache_data(ttl=3600)  # Cache for 1 hour - speeds up repeated loads
def load_sample_data() -> Dict[str, Any]:
    """Load sample input data - cached for performance."""
    return {
        'trading_date': SAMPLE_INPUT.trading_date,
        'tickers': ', '.join(SAMPLE_INPUT.tickers_tracked),
        'market_json': json.dumps([], indent=2),
        'news_json': json.dumps([], indent=2),
        'macro_context': SAMPLE_INPUT.macro_context,
        'constraints': SAMPLE_INPUT.constraints_or_notes
    }


def parse_json_safely(json_str: str, field_name: str) -> List[Any]:
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


def render_input_form() -> None:
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
                
                # Create progress tracker for report generation
                progress_steps = [
                    "Validating input",
                    "Initializing AI",
                    "Generating report text",
                    "Parsing response",
                    "Preparing report"
                ]
                tracker = create_progress_tracker(progress_steps, show_eta=True)
                
                try:
                    # Step 0: Rate limit check
                    tracker.update(0, "Checking rate limits...", 0.1)
                    try:
                        check_rate_limit(_report_generation_limiter, f"streamlit_report_{DEFAULT_CLIENT_ID}")
                    except RuntimeError as e:
                        tracker.error(f"Rate limit exceeded: {str(e)}")
                        from utils.user_messages import get_user_friendly_message
                        st.error(get_user_friendly_message("rate_limit_exceeded"))
                        return
                    
                    # Step 1: Initialize AI
                    tracker.update(1, "Initializing AI service...", 0.2)
                    
                    # Step 2: Generate report (this is the long step)
                    tracker.update(2, "Generating report with AI...", 0.3)
                    response = generate_daily_report(input_data)
                    
                    # Step 3: Parse response
                    tracker.update(3, "Processing report data...", 0.9)
                    
                    # Step 4: Complete
                    tracker.update(4, "Report ready!", 1.0)
                    tracker.complete("Report generated successfully!")
                    
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
                    tracker.error(f"Error generating report: {str(e)}")
                    from utils.user_messages import get_user_friendly_error
                    st.error(get_user_friendly_error(e, context={"error_type": "report"}))
                    logger.exception("Error in report generation")
                    
            except Exception as e:
                from utils.user_messages import get_user_friendly_error
                st.error(get_user_friendly_error(e))
                logger.exception("Error in form submission")


def render_audio_player(audio_text: str, audio_gcs_path: Optional[str] = None) -> None:
    """
    Render enhanced audio player component with both text and audio playback.
    
    Args:
        audio_text: The audio script text
        audio_gcs_path: Optional GCS path to audio file (gs://bucket/path)
    """
    st.markdown("### 🔊 Audio Briefing")
    
    # Try to display audio player if GCS path is available
    if audio_gcs_path:
        try:
            from utils.audio_utils import get_audio_signed_url, get_audio_bytes_from_gcs_safe
            
            # Try signed URL first (more efficient)
            signed_url = get_audio_signed_url(audio_gcs_path, expiration_minutes=60)
            
            if signed_url:
                st.audio(signed_url, format="audio/wav")
                st.caption(f"📁 Audio file: `{audio_gcs_path}`")
            else:
                # Fallback to downloading bytes
                logger.warning("Signed URL generation failed, falling back to direct download")
                audio_bytes = get_audio_bytes_from_gcs_safe(audio_gcs_path)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")
                    st.caption(f"📁 Audio file: `{audio_gcs_path}`")
                else:
                    st.warning("Unable to load audio file. Showing text script instead.")
                    _render_audio_text_fallback(audio_text, audio_gcs_path)
        except ImportError:
            # Fallback if audio_utils not available
            logger.warning("audio_utils not available, using direct download")
            try:
                audio_bytes = get_audio_bytes_from_gcs(audio_gcs_path)
                st.audio(audio_bytes, format="audio/wav")
            except Exception as e:
                from utils.user_messages import get_user_friendly_message
                st.error(get_user_friendly_message("audio_generation_failed"))
                _render_audio_text_fallback(audio_text, audio_gcs_path)
        except Exception as e:
            logger.error("Error rendering audio player: %s", str(e), exc_info=True)
            from utils.user_messages import get_user_friendly_message
            st.error(get_user_friendly_message("audio_generation_failed"))
            _render_audio_text_fallback(audio_text, audio_gcs_path)
    elif audio_text:
        # No audio file, just show text
        _render_audio_text_fallback(audio_text, None)
    else:
        st.warning("No audio report available.")


def _render_audio_text_fallback(audio_text: str, audio_gcs_path: Optional[str] = None) -> None:
    """Render audio text as fallback when audio file is not available."""
    with st.expander("View Audio Script"):
        st.text(audio_text)
    
    # Option to copy for external TTS
    st.code(audio_text, language=None)
    
    if audio_gcs_path:
        st.info(f"💡 Audio file available at: `{audio_gcs_path}`")


def render_report_view(report_data: DailyReportResponse, market_data: List[Dict[str, Any]]) -> None:
    """Render the report view component with export options."""
    # Export buttons at the top
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            from utils.export_utils import export_report_to_pdf
            # Convert DailyReportResponse to dict for export
            report_dict = {
                "trading_date": date.today().isoformat(),
                "client_id": DEFAULT_CLIENT_ID,
                "summary_text": report_data.report_markdown[:500] if report_data.report_markdown else "",
                "key_insights": [],
                "market_context": report_data.core_tickers_in_depth_markdown[:500] if report_data.core_tickers_in_depth_markdown else "",
                "tickers": [r.ticker for r in report_data.reports] if report_data.reports else []
            }
            pdf_bytes = export_report_to_pdf(report_dict)
            st.download_button(
                label="📄 Export PDF",
                data=pdf_bytes,
                file_name=f"report_{date.today().isoformat()}.pdf",
                mime="application/pdf"
            )
        except ImportError:
            st.info("PDF export: pip install reportlab")
        except Exception as e:
            logger.error("PDF export error: %s", str(e))
    
    with col2:
        try:
            from utils.export_utils import export_market_data_to_csv
            if market_data:
                market_csv_bytes = export_market_data_to_csv(market_data)
                st.download_button(
                    label="📊 Export Market Data CSV",
                    data=market_csv_bytes,
                    file_name=f"market_data_{date.today().isoformat()}.csv",
                    mime="text/csv"
                )
        except Exception as e:
            logger.error("CSV export error: %s", str(e))
    
    st.markdown("---")
    
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
                
                # Use enhanced chart component
                try:
                    from python_app.components.charts import render_performance_chart
                    render_performance_chart(market_data, title="Top Movers Performance", height=400)
                except ImportError:
                    # Fallback to basic chart if plotly not available
                    st.bar_chart(
                        top_movers.set_index('ticker')[['volume', 'average_volume']],
                        height=300
                    )
                    st.info("💡 Install plotly for enhanced charts: pip install plotly")
        
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
        
        # Add audio player if available
        if report_data.audio_report:
            st.divider()
            # Try to get audio GCS path from session state or Firestore
            audio_gcs_path = None
            try:
                # Check if we have a trading date in session
                if 'report_data' in st.session_state and st.session_state.report_data:
                    # Try to get from Firestore
                    from datetime import date as date_type
                    trading_date = date_type.today()
                    report = get_daily_report(trading_date.isoformat())
                    if report and 'audio_gcs_path' in report:
                        audio_gcs_path = report['audio_gcs_path']
            except Exception:
                pass  # Silently fail if we can't get audio path
            
            render_audio_player(report_data.audio_report, audio_gcs_path)


def render_logo() -> None:
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


def render_watchlist() -> None:
    """Render the watchlist component in the sidebar with Firestore persistence."""
    with st.sidebar:
        st.subheader("Watchlist")
        
        # Enhanced watchlist with tabs
        watchlist_tab1, watchlist_tab2 = st.tabs(["Simple", "Advanced"])
        
        with watchlist_tab1:
            # Show current watchlist with remove buttons
            for ticker in list(st.session_state.watchlist):
                cols = st.columns([3, 1])
                cols[0].write(ticker)
                if cols[1].button("✕", key=f"remove_{ticker}"):
                    st.session_state.watchlist = [
                        t for t in st.session_state.watchlist if t != ticker
                    ]
                    _save_watchlist_to_firestore()
                    st.rerun()
            
            # Add new ticker
            new_ticker = st.text_input("Add ticker", key="add_ticker_input").upper().strip()
            if st.button("Add", key="add_ticker_btn") and new_ticker:
                if new_ticker not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_ticker)
                    _save_watchlist_to_firestore()
                    st.rerun()
            
            # Save to Firestore button
            if st.button("💾 Save Watchlist", key="save_watchlist_btn", use_container_width=True):
                if _save_watchlist_to_firestore():
                    st.success("Watchlist saved!")
                else:
                    from utils.user_messages import get_user_friendly_message
                    st.error(get_user_friendly_message("watchlist_save_failed"))
        
        with watchlist_tab2:
            # Enhanced features
            try:
                from python_app.components.watchlist_enhanced import (
                    render_watchlist_categories,
                    render_watchlist_bulk_operations
                )
                
                def update_watchlist(new_watchlist: Optional[List[str]] = None):
                    if new_watchlist:
                        st.session_state.watchlist = new_watchlist
                    _save_watchlist_to_firestore()
                
                render_watchlist_bulk_operations(
                    st.session_state.watchlist,
                    DEFAULT_CLIENT_ID,
                    on_update=update_watchlist
                )
                
                st.divider()
                
                render_watchlist_categories(
                    st.session_state.watchlist,
                    DEFAULT_CLIENT_ID,
                    on_update=lambda: update_watchlist()
                )
            except Exception as e:
                st.info("Enhanced features require Firestore access")


def _save_watchlist_to_firestore() -> bool:
    """Save watchlist to Firestore for persistence."""
    try:
        from report_repository import get_client, create_or_update_client
        
        client_id = DEFAULT_CLIENT_ID
        client = get_client(client_id)
        
        if client:
            # Update existing client with new watchlist
            client["watchlist"] = st.session_state.watchlist
            create_or_update_client(client_id, **client)
        else:
            # Create new client document
            create_or_update_client(
                client_id,
                watchlist=st.session_state.watchlist,
                name="Michael Brooks"
            )
        
        return True
    except Exception as e:
        return False


def _load_watchlist_from_firestore(client_id: str = DEFAULT_CLIENT_ID) -> list[str]:
    """Load watchlist from Firestore if available."""
    try:
        from report_repository import get_client
        
        client = get_client(client_id)
        if client and "watchlist" in client:
            return client["watchlist"]
    except Exception:
        # If Firestore fetch fails, return default
        pass
    
    return DEFAULT_WATCHLIST.copy()


def render_chat_interface() -> None:
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
                from utils.user_messages import get_user_friendly_error
                error_msg = get_user_friendly_error(e)
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
                from utils.user_messages import get_user_friendly_error
                error_msg = get_user_friendly_error(e)
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
            # Create progress tracker
            steps = [
                "Rate limit check",
                "Fetching market data",
                "Generating AI report text",
                "Storing report in Firestore",
                "Generating audio (TTS)",
                "Uploading audio to Cloud Storage",
                "Finalizing report"
            ]
            tracker = create_progress_tracker(steps, show_eta=True)
            
            try:
                trading_date = date.today()
                
                # Step 0: Rate limit check
                tracker.update(0, "Checking rate limits...", 0.05)
                try:
                    check_rate_limit(_report_generation_limiter, f"streamlit_watchlist_{DEFAULT_CLIENT_ID}")
                except RuntimeError as e:
                    tracker.error(f"Rate limit exceeded: {str(e)}")
                    from utils.user_messages import get_user_friendly_message
                    st.error(get_user_friendly_message("rate_limit_exceeded"))
                    return
                
                # Step 1: Market data (happens inside generate_watchlist_daily_report)
                tracker.update(1, "Fetching market data for watchlist...", 0.15)
                
                # Note: generate_watchlist_daily_report does multiple steps internally
                # We'll update progress at key points
                report = generate_watchlist_daily_report(
                    trading_date=trading_date,
                    client_id=DEFAULT_CLIENT_ID,
                    watchlist=st.session_state.watchlist,
                )
                
                # Update progress for remaining steps (they happen in the function)
                tracker.update(2, "AI report text generated", 0.50)
                tracker.update(3, "Report stored in Firestore", 0.70)
                tracker.update(4, "Audio generation complete", 0.85)
                tracker.update(5, "Audio uploaded to Cloud Storage", 0.95)
                tracker.update(6, "Report finalized", 0.98)
                tracker.complete("Report generated successfully!")
                
                # Show notification
                try:
                    from python_app.components.notifications import notify_report_complete
                    notify_report_complete(
                        trading_date=trading_date.isoformat(),
                        client_id=DEFAULT_CLIENT_ID,
                        has_audio=bool(report.get("audio_gcs_path"))
                    )
                except Exception as e:
                    logger.warning("Failed to show notification: %s", str(e))
                
                st.success("✅ Daily market report generated successfully!")
                st.info("Check the 'Daily Watchlist Report' tab to view the full report.")
                st.rerun()
            except Exception as e:
                if _error_tracking_available:
                    capture_exception(
                        e,
                        tags={"component": "dashboard", "action": "generate_report"},
                        context={"watchlist": st.session_state.watchlist}
                    )
                progress_bar.progress(0)
                status_text.empty()
                
                # Show error notification
                try:
                    from python_app.components.notifications import notify_report_error
                    notify_report_error(str(e), trading_date=trading_date.isoformat())
                except Exception:
                    pass  # Notification failure shouldn't break error display
                
                from utils.user_messages import get_user_friendly_error
                st.error(get_user_friendly_error(e, context={"error_type": "report"}))
                logger.error("Report generation error: %s", str(e), exc_info=True)
    
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
        
        # Show enhanced charts if we have data
        if 'percent_change' in movers_df.columns and 'volume' in movers_df.columns:
            try:
                from python_app.components.charts import (
                    render_performance_chart,
                    render_volume_analysis,
                    render_market_sentiment_indicator,
                    render_price_movement_scatter
                )
                
                # Convert DataFrame to list of dicts for chart component
                market_data_list = movers_df.to_dict('records')
                
                # Performance chart
                render_performance_chart(market_data_list, title="Watchlist Performance", height=400)
                
                # Additional charts in tabs
                chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Volume Analysis", "Market Sentiment", "Price Movement"])
                
                with chart_tab1:
                    render_volume_analysis(market_data_list, title="Volume vs Average Volume", height=350)
                
                with chart_tab2:
                    render_market_sentiment_indicator(market_data_list, title="Watchlist Sentiment", height=300)
                
                with chart_tab3:
                    render_price_movement_scatter(market_data_list, title="Price Movement vs Volume", height=400)
                    
            except ImportError:
                # Fallback to basic chart if plotly not available
                chart_data = movers_df.set_index('ticker')[['volume', 'percent_change']]
                st.bar_chart(chart_data)
                st.info("💡 Install plotly for enhanced charts: pip install plotly")
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
                # Rate limit check
                try:
                    check_rate_limit(_report_generation_limiter, f"streamlit_watchlist_{DEFAULT_CLIENT_ID}")
                except RuntimeError as e:
                    from utils.user_messages import get_user_friendly_message
                    st.error(get_user_friendly_message("rate_limit_exceeded"))
                    return
                
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
                    # Use enhanced audio player
                    render_audio_player("", audio_gcs_path)
                
                # Export buttons
                st.divider()
                st.subheader("Export Report")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    try:
                        from utils.export_utils import export_report_to_pdf
                        pdf_bytes = export_report_to_pdf(report)
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_bytes,
                            file_name=f"report_{trading_date.isoformat()}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except ImportError:
                        st.info("PDF export requires: pip install reportlab")
                    except Exception as e:
                        logger.error("PDF export failed: %s", str(e), exc_info=True)
                        from utils.user_messages import get_user_friendly_message
                        st.error(get_user_friendly_message("export_failed"))
                
                with col2:
                    try:
                        from utils.export_utils import export_report_to_csv
                        csv_bytes = export_report_to_csv(report)
                        st.download_button(
                            label="📊 Download CSV",
                            data=csv_bytes,
                            file_name=f"report_{trading_date.isoformat()}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    except Exception as e:
                        logger.error("CSV export failed: %s", str(e), exc_info=True)
                        from utils.user_messages import get_user_friendly_message
                        st.error(get_user_friendly_message("export_failed"))
                
                with col3:
                    # Export market data if available
                    try:
                        movers_df = get_daily_movers_for_watchlist(
                            watchlist=st.session_state.watchlist,
                            trading_date=trading_date,
                        )
                        if not movers_df.empty:
                            from utils.export_utils import export_market_data_to_csv
                            market_data_list = movers_df.to_dict('records')
                            market_csv_bytes = export_market_data_to_csv(market_data_list)
                            st.download_button(
                                label="📈 Download Market Data CSV",
                                data=market_csv_bytes,
                                file_name=f"market_data_{trading_date.isoformat()}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        else:
                            st.info("No market data to export")
                    except Exception as e:
                        logger.error("Market data export failed: %s", str(e), exc_info=True)
                        st.info("Market data export unavailable")
                
                st.success("Report generated successfully!")
            except Exception as e:
                from utils.user_messages import get_user_friendly_error
                st.error(get_user_friendly_error(e, context={"error_type": "report"}))
    else:
        st.info("Click the button above to generate a report for your watchlist.")


def render_report_history_tab() -> None:
    """Render the Report History tab showing past reports."""
    st.header("📚 Report History")
    st.caption("Browse and view past daily reports")
    
    # Add comparison and bookmark tabs
    history_tab1, history_tab2, history_tab3 = st.tabs(["Reports", "Bookmarks", "Compare Reports"])
    
    with history_tab1:
        try:
            from report_repository import list_daily_reports
            from python_app.components.search_filter import render_search_filter_ui
            
            # Basic filter options
            col1, col2 = st.columns(2)
            with col1:
                limit = st.number_input("Number of reports to show", min_value=10, max_value=100, value=50, step=10)
            with col2:
                show_all = st.checkbox("Show all clients", value=False)
            
            # Fetch reports with pagination (client-scoped)
            current_client_id = st.session_state.get('client_id', DEFAULT_CLIENT_ID)
            client_id = None if show_all else current_client_id
            
            # Pagination state
            if 'report_history_page' not in st.session_state:
                st.session_state.report_history_page = None
            
            result = list_daily_reports(
                client_id=client_id,
                limit=limit,
                order_by="trading_date",
                descending=True,
                start_after=st.session_state.report_history_page
            )
            
            reports = result.get("reports", [])
            has_more = result.get("has_more", False)
            error = result.get("error")
            
            if error:
                from utils.user_messages import get_user_friendly_message
                st.error(get_user_friendly_message("report_not_found"))
                return
            
            if not reports:
                st.info("No reports found. Generate a report to see it here.")
                return
            
            # Apply search and filter UI
            try:
                from python_app.components.search_filter import render_search_filter_ui
                filtered_reports = render_search_filter_ui(reports)
            except Exception as e:
                logger.warning("Search/filter UI failed: %s", str(e))
                filtered_reports = reports
            
            st.success(f"Found {len(filtered_reports)} of {len(reports)} report(s)")
            
            # Pagination controls
            if has_more or st.session_state.report_history_page:
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("◀ Previous", disabled=st.session_state.report_history_page is None):
                        # Reset to beginning
                        st.session_state.report_history_page = None
                        st.rerun()
                with col2:
                    if has_more and st.button("Next ▶"):
                        # Move to next page
                        st.session_state.report_history_page = result.get('last_date')
                        st.rerun()
                with col3:
                    if st.session_state.report_history_page:
                        st.caption(f"Showing reports after {st.session_state.report_history_page}")
            
            # Display filtered reports in a scrollable list
            for report in filtered_reports:
                with st.expander(
                    f"📅 {report.get('trading_date', 'Unknown Date')} - {len(report.get('tickers', []))} tickers",
                    expanded=False
                ):
                    # Report metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Trading Date", report.get('trading_date', 'N/A'))
                    with col2:
                        tickers = report.get('tickers', [])
                        st.metric("Tickers", len(tickers))
                    with col3:
                        has_audio = "✅" if report.get('audio_gcs_path') else "❌"
                        st.metric("Audio", has_audio)
                    
                    # Tickers list
                    if tickers:
                        st.caption(f"Tickers: {', '.join(tickers)}")
                    
                    # Summary preview
                    summary = report.get('summary_text', '')
                    if summary:
                        st.subheader("Summary")
                        # Show first 500 chars with option to expand
                        if len(summary) > 500:
                            st.write(summary[:500] + "...")
                            with st.expander("View full summary"):
                                st.write(summary)
                        else:
                            st.write(summary)
                    
                    # Key insights
                    insights = report.get('key_insights', [])
                    if insights:
                        st.subheader("Key Insights")
                        for insight in insights:
                            st.markdown(f"- {insight}")
                    
                    # Actions
                    st.divider()
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        col_view, col_bookmark = st.columns([2, 1])
                        with col_view:
                            if st.button("📄 View Full Report", key=f"view_{report.get('trading_date')}"):
                                st.session_state['selected_report_date'] = report.get('trading_date')
                                st.rerun()
                        with col_bookmark:
                            # Bookmark button
                            try:
                                from python_app.components.report_viewer import render_bookmark_button
                                render_bookmark_button(report.get('trading_date'), DEFAULT_CLIENT_ID)
                            except Exception:
                                pass  # Bookmarking is optional
                    
                    with action_col2:
                        # Export buttons
                        try:
                            from utils.export_utils import export_report_to_csv
                            csv_bytes = export_report_to_csv(report)
                            st.download_button(
                                label="📊 Export CSV",
                                data=csv_bytes,
                                file_name=f"report_{report.get('trading_date', 'unknown')}.csv",
                                mime="text/csv",
                                key=f"csv_{report.get('trading_date')}"
                            )
                        except Exception as e:
                            logger.error("CSV export failed: %s", str(e))
                    
                    with action_col3:
                        # Audio player if available
                        audio_gcs_path = report.get('audio_gcs_path')
                        if audio_gcs_path:
                            if st.button("🔊 Play Audio", key=f"audio_{report.get('trading_date')}"):
                                render_audio_player("", audio_gcs_path)
                        else:
                            st.info("No audio available")
        
        except ImportError:
            from utils.user_messages import get_user_friendly_message
            st.error(get_user_friendly_message("database_connection_failed"))
        except Exception as e:
            logger.error("Error loading report history: %s", str(e), exc_info=True)
            from utils.user_messages import get_user_friendly_message
            st.error(get_user_friendly_message("report_not_found"))
    
    with history_tab2:
        # Bookmarks tab
        try:
            from python_app.components.report_viewer import render_bookmark_management
            render_bookmark_management(DEFAULT_CLIENT_ID)
        except Exception as e:
            from utils.user_messages import get_user_friendly_message
            st.error(get_user_friendly_message("bookmark_failed"))
    
    with history_tab3:
        # Compare Reports tab
        try:
            from python_app.components.report_viewer import render_report_comparison
            
            st.subheader("Compare Two Reports")
            col1, col2 = st.columns(2)
            
            with col1:
                report1_date = st.date_input(
                    "First Report Date",
                    value=date.today() - timedelta(days=1),
                    key="compare_report1"
                )
            
            with col2:
                report2_date = st.date_input(
                    "Second Report Date",
                    value=date.today(),
                    key="compare_report2"
                )
            
            if st.button("Compare Reports", type="primary"):
                if report1_date == report2_date:
                    st.warning("Please select two different dates for comparison.")
                else:
                    render_report_comparison(
                        report1_date.isoformat(),
                        report2_date.isoformat(),
                        DEFAULT_CLIENT_ID
                    )
        except Exception as e:
            from utils.user_messages import get_user_friendly_message
            st.error(get_user_friendly_message("comparison_failed"))


def render_ai_chat_tab() -> None:
    """Render the AI Chat tab."""
    render_chat_ui()


def render_alerts_tab() -> None:
    """Render the Alerts management tab."""
    st.header("🔔 Email Alerts")
    st.caption("Get notified via Email when tickers hit your price targets.")
    
    # Initialize service
    alert_service = AlertService()
    user = get_current_user()
    user_id = user.get('email', 'default_user') if user else 'default_user'
    user_email_default = user.get('email', '') if user else ''
    
    # 1. Create Alert Form
    with st.expander("Create New Alert", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            ticker = st.selectbox("Ticker", options=st.session_state.watchlist)
        with col2:
            condition = st.selectbox(
                "Condition", 
                options=[c.value for c in ConditionType],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        with col3:
            value = st.number_input("Target Value", value=100.0)
            
        email = st.text_input("Email Address", value=user_email_default)
        
        if st.button("Create Alert", type="primary"):
            if not email:
                st.error("Email address is required.")
            else:
                alert_service.create_alert(
                    user_id=user_id,
                    ticker=ticker,
                    condition=ConditionType(condition),
                    value=value,
                    email=email
                )
                st.success(f"Alert created for {ticker}!")
                st.rerun()

    st.divider()

    # 2. List Alerts
    st.subheader("Your Active Alerts")
    alerts = alert_service.get_user_alerts(user_id)
    
    if alerts:
        for alert in alerts:
            col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
            with col1:
                st.write(f"**{alert.ticker}**")
            with col2:
                st.write(f"{alert.condition_type.replace('_', ' ').title()}")
            with col3:
                st.write(f"Target: {alert.target_value}")
            with col4:
                st.write(f"Last Trig: {alert.last_triggered or 'Never'}")
            with col5:
                if st.button("🗑️", key=f"del_{alert.id}"):
                    if alert_service.delete_alert(alert.id):
                        st.success("Deleted")
                        st.rerun()
    else:
        st.info("No active alerts.")

    st.divider()
    
    # 3. Manual Test Trigger
    st.subheader("Debug / Test")
    if st.button("Check Alerts Now"):
        with st.spinner("Fetching market data and checking conditions..."):
            # Fetch data for all tickers in alerts
            # For simplicity, fetch for watchlist + unique alert tickers?
            # Or just fetch for watchlist if alerts are usually subsets of watchlist
            unique_tickers = list(set([a.ticker for a in alerts]))
            if not unique_tickers:
                st.warning("No alerts to check.")
                return
                
            df = fetch_watchlist_intraday_data(unique_tickers, date.today())
            triggered_ids = alert_service.check_market_data(df)
            
            if triggered_ids:
                st.success(f"Triggered {len(triggered_ids)} alerts! Check your email.")
                st.rerun()
            else:
                st.info("No alerts triggered based on current data.")


def main() -> None:
    """Main application entry point."""
    # Validate configuration on startup
    try:
        from utils.config_validator import validate_config
        config = validate_config()
        logger.info("Configuration validated successfully")
        if _error_tracking_available:
            set_user_context(user_id=DEFAULT_CLIENT_ID)
    except Exception as e:
        logger.warning("Configuration validation failed: %s", str(e))
        # Continue anyway - some features may not work
    
    # Check if we're in development mode
    from config import get_config
    app_config = get_config()
    is_development = app_config.show_developer_tools
    
    # Authentication (skip in development mode for easier testing)
    if not is_development:
        try:
            handle_auth()
            # Get user info and set client_id for this session
            user = get_current_user()
            if user:
                session_client_id = user.get('email', DEFAULT_CLIENT_ID)
            else:
                session_client_id = DEFAULT_CLIENT_ID
        except Exception as e:
            logger.warning("Authentication failed, using default client: %s", str(e))
            session_client_id = DEFAULT_CLIENT_ID
    else:
        # Development mode: skip authentication
        session_client_id = DEFAULT_CLIENT_ID
    
    init_session_state(client_id=session_client_id)
    
    # Auto-load active report on app launch
    load_active_report_automatically()
    
    # Logo in sidebar (at the top) - DISABLED
    # render_logo()
    
    # Status indicators in sidebar (only in development)
    with st.sidebar.container():
        if is_development:
            render_status_indicators(show_in_sidebar=True)
            st.sidebar.divider()
            render_keyboard_shortcuts_help()
            
            # Notification settings
            try:
                from python_app.components.notifications import render_notification_settings
                st.sidebar.divider()
                render_notification_settings()
            except Exception:
                pass  # Notifications are optional
    
    st.title("Brooks Data Center Daily Briefing")
    
    tab_dashboard, tab_report, tab_history, tab_chat, tab_alerts, tab_help = st.tabs(
        ["Dashboard", "Daily Watchlist Report", "Report History", "AI Chat", "🔔 Alerts", "Help"]
    )
    
    with tab_dashboard:
        firestore_client = get_firestore_client()
        render_dashboard(firestore_client, st.session_state.get('client_id', DEFAULT_CLIENT_ID))
    
    with tab_report:
        render_watchlist_report_tab()
    
    with tab_history:
        render_report_history_tab()
    
    with tab_chat:
        render_ai_chat_tab()
    
    with tab_alerts:
        render_alerts_tab()
    
    with tab_help:
        try:
            from python_app.components.help_center import render_help_center
            render_help_center()
        except Exception as e:
            from utils.user_messages import get_user_friendly_message
            st.error(get_user_friendly_message("help_center_failed"))
    
    # Watchlist in sidebar (always visible)
    render_watchlist()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        st.error(f"Application error: {str(e)}")
        if os.getenv("ENVIRONMENT", "production").lower() == "development":
            st.exception(e)
        logger.exception("Fatal error in main()")
        st.stop()

