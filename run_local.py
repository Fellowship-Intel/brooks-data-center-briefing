"""
Standalone command-line version of the Brooks Data Center Briefing app.
Runs locally without requiring a web browser or URL.
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Load .env file manually if not already set
if not os.getenv("GEMINI_API_KEY") and not os.getenv("API_KEY"):
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        try:
            # Read file and handle BOM (Byte Order Mark) if present
            content = env_path.read_text(encoding='utf-8-sig')  # utf-8-sig strips BOM
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # Remove quotes if present
                    if key == "GEMINI_API_KEY" or key == "API_KEY":
                        os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not read .env file: {e}\n")
    
    # Also try python-dotenv if available
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, encoding='utf-8-sig')
    except ImportError:
        pass  # python-dotenv not installed
    except Exception:
        pass  # dotenv failed, but we already tried manual loading

# Add the python_app directory to the path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from python_app.types import InputData, DailyReportResponse
from python_app.constants import SAMPLE_INPUT
from python_app.services.gemini_service import generate_daily_report, send_chat_message


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}\n")


def display_report(report: DailyReportResponse):
    """Display the report in the terminal."""
    print_header("DAILY BRIEFING REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Full Report
    if report.report_markdown:
        print_section("FULL REPORT")
        print(report.report_markdown)
    
    # Top Movers
    if report.reports:
        print_section("TOP MOVERS")
        for idx, mini_report in enumerate(report.reports[:3], 1):
            print(f"\n[{idx}] {mini_report.ticker} - {mini_report.company_name}")
            print(f"    {mini_report.section_title}")
            print(f"\n    Snapshot: {mini_report.snapshot}")
            print(f"    Catalyst: {mini_report.catalyst_and_context}")
            print(f"    Trading Lens: {mini_report.day_trading_lens}")
            if mini_report.watch_next_bullets:
                print(f"    Watch Next:")
                for bullet in mini_report.watch_next_bullets:
                    print(f"      • {bullet}")
            print()
    
    # Deep Dive
    if report.core_tickers_in_depth_markdown:
        print_section("CORE TICKERS DEEP DIVE")
        print(report.core_tickers_in_depth_markdown)
    
    # Audio Report
    if report.audio_report:
        print_section("AUDIO REPORT")
        print(report.audio_report)
    
    print("\n" + "=" * 80 + "\n")


def interactive_chat():
    """Interactive chat loop."""
    print_header("ANALYST Q&A")
    print("Ask questions about the report. Type 'exit' or 'quit' to end the chat.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nEnding chat session. Goodbye!\n")
                break
            
            if not user_input:
                continue
            
            print("Analyst: ", end="", flush=True)
            response = send_chat_message(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nChat interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


def main():
    """Main application entry point."""
    print_header("BROOKS DATA CENTER BRIEFING - LOCAL MODE")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY or API_KEY not found in environment variables.")
        print("Please set it in your .env file or as an environment variable.")
        print(f"Current working directory: {os.getcwd()}")
        print(f".env file exists: {Path('.env').exists()}\n")
        sys.exit(1)
    
    try:
        # Generate initial report
        print("Generating daily briefing report...")
        print("This may take a minute...\n")
        
        response = generate_daily_report(SAMPLE_INPUT)
        
        # Display the report
        display_report(response)
        
        # Write to output.txt
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
        
        # Write to output.txt in the same directory as the script
        output_path = Path(__file__).parent / "output.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result_text)
        
        print("✓ Report saved to output.txt\n")
        
        # Offer interactive chat
        while True:
            choice = input("Would you like to ask questions about this report? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                interactive_chat()
                break
            elif choice in ['n', 'no']:
                print("\nThank you for using Brooks Data Center Briefing!\n")
                break
            else:
                print("Please enter 'y' or 'n'")
        
    except KeyboardInterrupt:
        print("\n\nApplication interrupted. Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

