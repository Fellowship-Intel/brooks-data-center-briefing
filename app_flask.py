"""
DEPRECATED: Flask web application for Brooks Data Center Daily Briefing

This Flask entry point is deprecated. Please use:
- Streamlit UI: `streamlit run app.py` (recommended for desktop web app)
- FastAPI API: `uvicorn app.main:app --reload` (for REST API access)

This file is kept for backward compatibility but will be removed in a future version.
"""
from flask import Flask, render_template, request, jsonify, session
import json
import sys
import os
import re
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

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')


def markdown_to_html(text):
    """Simple markdown to HTML converter."""
    if not text:
        return ""
    
    # Convert markdown to HTML
    html = text
    
    # Headers
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Code blocks
    html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
    
    # Inline code
    html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
    
    # Links
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" class="text-emerald-400 hover:underline">\1</a>', html)
    
    # Lists
    html = re.sub(r'^\* (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
    
    # Paragraphs (double newline)
    paragraphs = html.split('\n\n')
    html = '\n'.join([f'<p>{p.strip()}</p>' if p.strip() and not p.strip().startswith('<') else p for p in paragraphs])
    
    # Line breaks
    html = html.replace('\n', '<br>')
    
    return html


@app.template_filter('markdown')
def markdown_filter(text):
    """Jinja2 filter for markdown."""
    return markdown_to_html(text)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


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


@app.route('/')
def index():
    """Main page - shows input form or report view."""
    # Initialize session state
    if 'mode' not in session:
        session['mode'] = 'input'
        session['report_data'] = None
        session['market_data_input'] = []
        session['chat_messages'] = []
        session['auto_init_attempted'] = False  # Prevent redirect loops
    
    # Auto-generate report on first visit only (prevent loops)
    if (session.get('mode') == 'input' and 
        session.get('report_data') is None and 
        not session.get('auto_init_attempted')):
        session['auto_init_attempted'] = True  # Mark as attempted to prevent retry loops
        try:
            response = generate_daily_report(SAMPLE_INPUT)
            session['report_data'] = {
                'report_markdown': response.report_markdown,
                'core_tickers_in_depth_markdown': response.core_tickers_in_depth_markdown,
                'audio_report': response.audio_report,
                'reports': [
                    {
                        'ticker': r.ticker,
                        'company_name': r.company_name,
                        'section_title': r.section_title,
                        'snapshot': r.snapshot,
                        'catalyst_and_context': r.catalyst_and_context,
                        'day_trading_lens': r.day_trading_lens,
                        'watch_next_bullets': r.watch_next_bullets
                    }
                    for r in response.reports
                ],
                'updated_market_data': [
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
                    for m in (response.updated_market_data or [])
                ]
            }
            session['market_data_input'] = session['report_data']['updated_market_data']
            session['mode'] = 'report'
        except Exception as e:
            print(f"Auto-init failed: {e}")
            session['mode'] = 'input'
            # Keep auto_init_attempted = True to prevent retry loops
    
    if session.get('mode') == 'report' and session.get('report_data'):
        return render_template('report.html', 
                             report_data=session['report_data'],
                             market_data=session.get('market_data_input', []))
    else:
        sample_data = load_sample_data()
        return render_template('input.html', sample_data=sample_data)


@app.route('/generate', methods=['POST'])
def generate_report():
    """Generate a new report from form data."""
    try:
        data = request.json
        
        market_data_list = parse_json_safely(data.get('market_json', '[]'), "Market Data JSON")
        news_data_list = parse_json_safely(data.get('news_json', '[]'), "News JSON")
        
        # Convert to typed objects
        market_data_objs = [dict_to_market_data(m) for m in market_data_list]
        news_data_objs = [dict_to_news_item(n) for n in news_data_list]
        
        input_data = InputData(
            trading_date=data.get('trading_date', SAMPLE_INPUT.trading_date),
            tickers_tracked=[t.strip() for t in data.get('tickers', '').split(',') if t.strip()],
            market_data_json=market_data_objs,
            news_json=news_data_objs,
            macro_context=data.get('macro_context', ''),
            constraints_or_notes=data.get('constraints', '')
        )
        
        response = generate_daily_report(input_data)
        
        # Store in session
        session['report_data'] = {
            'report_markdown': response.report_markdown,
            'core_tickers_in_depth_markdown': response.core_tickers_in_depth_markdown,
            'audio_report': response.audio_report,
            'reports': [
                {
                    'ticker': r.ticker,
                    'company_name': r.company_name,
                    'section_title': r.section_title,
                    'snapshot': r.snapshot,
                    'catalyst_and_context': r.catalyst_and_context,
                    'day_trading_lens': r.day_trading_lens,
                    'watch_next_bullets': r.watch_next_bullets
                }
                for r in response.reports
            ],
            'updated_market_data': [
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
                for m in (response.updated_market_data or [])
            ]
        }
        
        if response.updated_market_data:
            session['market_data_input'] = session['report_data']['updated_market_data']
        else:
            session['market_data_input'] = market_data_list
        
        session['mode'] = 'report'
        
        # Write to output.txt
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
        
        output_path = Path(__file__).parent / "output.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result_text)
        
        return jsonify({
            'success': True,
            'redirect': '/'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        response_text = send_chat_message(message)
        
        # Write to output.txt
        result_text = f"Q: {message}\nA: {response_text}\n\n"
        output_path = Path(__file__).parent / "output.txt"
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(result_text)
        
        return jsonify({
            'success': True,
            'response': response_text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/reset', methods=['POST'])
def reset():
    """Reset session to input mode."""
    session['mode'] = 'input'
    session['report_data'] = None
    session['market_data_input'] = []
    session['chat_messages'] = []
    session['auto_init_attempted'] = False  # Reset flag to allow auto-init again
    return jsonify({'success': True, 'redirect': '/'})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')

