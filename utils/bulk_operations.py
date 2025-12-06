"""
Bulk operations for reports and watchlists.

Provides functionality for bulk export, import, and data portability.
"""

import logging
import csv
import io
import json
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pathlib import Path
import zipfile

from report_repository import get_all_reports, get_daily_report
from utils.export_utils import export_report_to_csv, export_report_to_pdf, export_market_data_to_csv

logger = logging.getLogger(__name__)


def export_multiple_reports(
    trading_dates: List[str],
    client_id: str,
    format: str = "csv",
    include_audio: bool = False
) -> bytes:
    """
    Export multiple reports in bulk.
    
    Args:
        trading_dates: List of trading dates (ISO format: YYYY-MM-DD)
        client_id: Client ID
        format: Export format ('csv', 'pdf', 'json', 'zip')
        include_audio: Whether to include audio files (only for zip format)
        
    Returns:
        Exported data as bytes
    """
    reports = []
    
    for trading_date_str in trading_dates:
        try:
            report = get_daily_report(trading_date_str)
            if report and report.get("client_id") == client_id:
                reports.append(report)
        except Exception as e:
            logger.warning("Failed to load report for %s: %s", trading_date_str, str(e))
            continue
    
    if not reports:
        raise ValueError("No reports found for the specified dates")
    
    if format == "json":
        return json.dumps(reports, indent=2, default=str).encode('utf-8')
    
    elif format == "zip":
        # Create ZIP archive with multiple files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for report in reports:
                trading_date = report.get("trading_date", "unknown")
                
                # Add CSV
                csv_data = export_report_to_csv(report)
                zip_file.writestr(f"{trading_date}_report.csv", csv_data)
                
                # Add PDF if available
                try:
                    pdf_data = export_report_to_pdf(report)
                    zip_file.writestr(f"{trading_date}_report.pdf", pdf_data)
                except Exception as e:
                    logger.warning("Failed to generate PDF for %s: %s", trading_date, str(e))
                
                # Add JSON
                json_data = json.dumps(report, indent=2, default=str).encode('utf-8')
                zip_file.writestr(f"{trading_date}_report.json", json_data)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    elif format == "csv":
        # Combine all reports into a single CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Trading Date", "Client ID", "Summary", "Key Insights", "Market Context"])
        
        for report in reports:
            insights = report.get("key_insights", [])
            insights_str = "; ".join(insights) if insights else ""
            
            writer.writerow([
                report.get("trading_date", ""),
                report.get("client_id", ""),
                report.get("summary_text", "")[:500],  # Truncate for CSV
                insights_str,
                report.get("market_context", "")[:500]
            ])
        
        return output.getvalue().encode('utf-8')
    
    else:
        raise ValueError(f"Unsupported format: {format}")


def import_watchlist_from_csv(csv_content: bytes) -> List[str]:
    """
    Import watchlist from CSV file.
    
    Expected CSV format:
    - First column: Ticker symbol
    - Optional header row
    
    Args:
        csv_content: CSV file content as bytes
        
    Returns:
        List of ticker symbols
    """
    try:
        csv_str = csv_content.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_str))
        
        tickers = []
        for row in reader:
            if not row:
                continue
            
            # Get first column (ticker)
            ticker = row[0].strip().upper()
            
            # Skip header if it looks like a header
            if ticker.upper() in ['TICKER', 'SYMBOL', 'STOCK', '']:
                continue
            
            # Validate ticker format (1-5 uppercase letters)
            if ticker and len(ticker) <= 5 and ticker.isalpha():
                tickers.append(ticker)
        
        return tickers
        
    except Exception as e:
        logger.error("Failed to import watchlist from CSV: %s", str(e), exc_info=True)
        raise ValueError(f"Failed to parse CSV: {str(e)}") from e


def export_watchlist_to_csv(watchlist: List[str]) -> bytes:
    """
    Export watchlist to CSV format.
    
    Args:
        watchlist: List of ticker symbols
        
    Returns:
        CSV content as bytes
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Ticker"])
    
    # Write tickers
    for ticker in watchlist:
        writer.writerow([ticker])
    
    return output.getvalue().encode('utf-8')


def export_reports_summary(
    start_date: date,
    end_date: date,
    client_id: str
) -> bytes:
    """
    Export a summary of reports for a date range.
    
    Args:
        start_date: Start date
        end_date: End date
        client_id: Client ID
        
    Returns:
        CSV summary as bytes
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Trading Date",
        "Tickers",
        "Summary Length",
        "Key Insights Count",
        "Has Audio",
        "TTS Provider"
    ])
    
    # Iterate through date range
    current_date = start_date
    while current_date <= end_date:
        trading_date_str = current_date.isoformat()
        try:
            report = get_daily_report(trading_date_str)
            if report and report.get("client_id") == client_id:
                tickers = report.get("tickers", [])
                summary = report.get("summary_text", "")
                insights = report.get("key_insights", [])
                
                writer.writerow([
                    trading_date_str,
                    ", ".join(tickers) if tickers else "",
                    len(summary),
                    len(insights),
                    "Yes" if report.get("audio_gcs_path") else "No",
                    report.get("tts_provider", "N/A")
                ])
        except Exception as e:
            logger.warning("Failed to load report for %s: %s", trading_date_str, str(e))
        
        # Move to next day
        from datetime import timedelta
        current_date += timedelta(days=1)
    
    return output.getvalue().encode('utf-8')

