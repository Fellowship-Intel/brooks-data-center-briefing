"""Email service for automated report delivery."""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending reports via SMTP.
    
    Supports both plain text and HTML emails with attachments.
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: bool = True
    ):
        """
        Initialize email service.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (default: 587)
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: From email address
            use_tls: Use TLS encryption (default: True)
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("EMAIL_FROM")
        self.use_tls = use_tls
        
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.from_email]):
            logger.warning(
                "Email service not fully configured. "
                "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and EMAIL_FROM environment variables."
            )
    
    def is_configured(self) -> bool:
        """Check if email service is fully configured."""
        return all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.from_email
        ])
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send email with optional HTML body and attachments.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            attachments: Optional list of attachments with 'filename' and 'content' (bytes)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("Email service not configured. Cannot send email.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text part
            text_part = MIMEText(body_text, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    filename = attachment.get('filename', 'attachment')
                    content = attachment.get('content')
                    if content:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(content)
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg, from_addr=self.from_email, to_addrs=to_emails)
            
            logger.info("Email sent successfully to %s", ', '.join(to_emails))
            return True
            
        except Exception as e:
            logger.error("Failed to send email: %s", str(e), exc_info=True)
            return False
    
    def send_report_email(
        self,
        to_emails: List[str],
        report_data: Dict[str, Any],
        trading_date: str,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send daily report email.
        
        Args:
            to_emails: List of recipient email addresses
            report_data: Report data dictionary
            trading_date: Trading date string
            attachments: Optional attachments (e.g., PDF, CSV)
            
        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"Daily Trading Report - {trading_date}"
        
        # Build text body
        summary = report_data.get("summary_text", "")
        insights = report_data.get("key_insights", [])
        tickers = report_data.get("tickers", [])
        
        body_text = f"""
Daily Trading Report - {trading_date}

Summary:
{summary}

Key Insights:
{chr(10).join(f"- {insight}" for insight in insights) if insights else "None"}

Tickers Tracked: {', '.join(tickers) if tickers else "None"}

---
This is an automated report from Brooks Data Center Daily Briefing.
"""
        
        # Build HTML body
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .insight {{ background-color: #f0f9ff; padding: 10px; margin: 10px 0; border-left: 4px solid #10b981; }}
        .footer {{ background-color: #f3f4f6; padding: 10px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Daily Trading Report</h1>
        <p>{trading_date}</p>
    </div>
    <div class="content">
        <h2>Summary</h2>
        <p>{summary.replace(chr(10), '<br>')}</p>
        
        <h2>Key Insights</h2>
        {'<div class="insight">' + '</div><div class="insight">'.join(insights) + '</div>' if insights else '<p>None</p>'}
        
        <h2>Tickers Tracked</h2>
        <p>{', '.join(tickers) if tickers else 'None'}</p>
    </div>
    <div class="footer">
        <p>This is an automated report from Brooks Data Center Daily Briefing.</p>
    </div>
</body>
</html>
"""
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments
        )


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_report_email(
    to_emails: List[str],
    report_data: Dict[str, Any],
    trading_date: str,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """
    Convenience function to send report email.
    
    Args:
        to_emails: List of recipient email addresses
        report_data: Report data dictionary
        trading_date: Trading date string
        attachments: Optional attachments
        
    Returns:
        True if sent successfully, False otherwise
    """
    service = get_email_service()
    return service.send_report_email(to_emails, report_data, trading_date, attachments)

