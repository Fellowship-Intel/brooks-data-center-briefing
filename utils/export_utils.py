"""Export utilities for reports (PDF, CSV)."""
import logging
from typing import Dict, Any, List, Optional
from datetime import date
from pathlib import Path
import csv
import io

logger = logging.getLogger(__name__)


def export_report_to_csv(
    report_data: Dict[str, Any],
    output_path: Optional[Path] = None
) -> bytes:
    """
    Export report data to CSV format.
    
    Args:
        report_data: Dictionary containing report data
        output_path: Optional path to save CSV file. If None, returns bytes.
        
    Returns:
        CSV content as bytes
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Field", "Value"])
        writer.writerow([])
        
        # Write basic report info
        writer.writerow(["Trading Date", report_data.get("trading_date", "N/A")])
        writer.writerow(["Client ID", report_data.get("client_id", "N/A")])
        writer.writerow([])
        
        # Write summary
        summary = report_data.get("summary_text", "")
        if summary:
            writer.writerow(["Summary"])
            # Split summary into lines for readability
            for line in summary.split("\n"):
                writer.writerow(["", line.strip()])
            writer.writerow([])
        
        # Write key insights
        insights = report_data.get("key_insights", [])
        if insights:
            writer.writerow(["Key Insights"])
            for idx, insight in enumerate(insights, 1):
                writer.writerow(["", f"{idx}. {insight}"])
            writer.writerow([])
        
        # Write market context if available
        market_context = report_data.get("market_context", "")
        if market_context:
            writer.writerow(["Market Context"])
            for line in market_context.split("\n"):
                writer.writerow(["", line.strip()])
            writer.writerow([])
        
        # Write tickers if available
        tickers = report_data.get("tickers", [])
        if tickers:
            writer.writerow(["Tickers Tracked"])
            writer.writerow(["", ", ".join(tickers)])
        
        csv_bytes = output.getvalue().encode('utf-8')
        
        if output_path:
            output_path.write_bytes(csv_bytes)
            logger.info("CSV exported to %s", output_path)
        
        return csv_bytes
        
    except Exception as e:
        logger.error("Error exporting to CSV: %s", str(e), exc_info=True)
        raise RuntimeError(f"Failed to export CSV: {str(e)}") from e


def export_report_to_pdf(
    report_data: Dict[str, Any],
    output_path: Optional[Path] = None
) -> bytes:
    """
    Export report data to PDF format.
    
    Uses reportlab for PDF generation with proper error handling.
    
    Args:
        report_data: Dictionary containing report data
        output_path: Optional path to save PDF file. If None, returns bytes.
        
    Returns:
        PDF content as bytes
        
    Raises:
        ImportError: If reportlab is not installed
        RuntimeError: If PDF generation fails
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
    except ImportError:
        raise ImportError(
            "reportlab is required for PDF export. Install it with: pip install reportlab"
        )
    
    try:
        # Create in-memory PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Container for PDF elements
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#10b981',
            spaceAfter=12,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#10b981',
            spaceAfter=8
        )
        
        # Title
        story.append(Paragraph("Daily Trading Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Report metadata
        trading_date = report_data.get("trading_date", "N/A")
        client_id = report_data.get("client_id", "N/A")
        story.append(Paragraph(f"<b>Trading Date:</b> {trading_date}", styles['Normal']))
        story.append(Paragraph(f"<b>Client:</b> {client_id}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Summary
        summary = report_data.get("summary_text", "")
        if summary:
            story.append(Paragraph("Summary", heading_style))
            # Clean HTML and format for PDF
            summary_clean = summary.replace("\n", "<br/>")
            story.append(Paragraph(summary_clean, styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Key Insights
        insights = report_data.get("key_insights", [])
        if insights:
            story.append(Paragraph("Key Insights", heading_style))
            for insight in insights:
                story.append(Paragraph(f"• {insight}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Market Context
        market_context = report_data.get("market_context", "")
        if market_context:
            story.append(Paragraph("Market Context", heading_style))
            context_clean = market_context.replace("\n", "<br/>")
            story.append(Paragraph(context_clean, styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Tickers
        tickers = report_data.get("tickers", [])
        if tickers:
            story.append(Paragraph("Tickers Tracked", heading_style))
            story.append(Paragraph(", ".join(tickers), styles['Normal']))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        if output_path:
            output_path.write_bytes(pdf_bytes)
            logger.info("PDF exported to %s", output_path)
        
        return pdf_bytes
        
    except Exception as e:
        logger.error("Error exporting to PDF: %s", str(e), exc_info=True)
        raise RuntimeError(f"Failed to export PDF: {str(e)}") from e


def export_market_data_to_csv(
    market_data: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> bytes:
    """
    Export market data to CSV format.
    
    Args:
        market_data: List of market data dictionaries
        output_path: Optional path to save CSV file
        
    Returns:
        CSV content as bytes
    """
    try:
        if not market_data:
            raise ValueError("Market data list is empty")
        
        output = io.StringIO()
        
        # Get all unique keys from market data
        fieldnames = set()
        for item in market_data:
            if isinstance(item, dict):
                fieldnames.update(item.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in market_data:
            if isinstance(item, dict):
                writer.writerow(item)
        
        csv_bytes = output.getvalue().encode('utf-8')
        
        if output_path:
            output_path.write_bytes(csv_bytes)
            logger.info("Market data CSV exported to %s", output_path)
        
        return csv_bytes
        
    except Exception as e:
        logger.error("Error exporting market data to CSV: %s", str(e), exc_info=True)
        raise RuntimeError(f"Failed to export market data CSV: {str(e)}") from e

