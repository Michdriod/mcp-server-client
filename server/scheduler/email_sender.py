"""
Email sender for scheduled reports.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any

from shared.config import settings


async def send_report_email(
    recipients: list[str],
    subject: str,
    report_name: str,
    description: str,
    data: list[dict[str, Any]],
    attachment_path: str | None = None,
    format: str = "csv",
) -> dict[str, Any]:
    """
    Send report via email.
    
    Args:
        recipients: List of email addresses
        subject: Email subject
        report_name: Name of the report
        description: Report description
        data: Query results
        attachment_path: Path to attachment file (optional)
        format: Report format (csv, excel, pdf)
    
    Returns:
        Dictionary with send status
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.email_from
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        
        # Create HTML body
        html_body = _create_html_email_body(
            report_name=report_name,
            description=description,
            data=data,
            row_count=len(data),
        )
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, "html"))
        
        # Attach file if provided
        if attachment_path and Path(attachment_path).exists():
            _attach_file(msg, attachment_path)
        
        # Send email
        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as server:
            if settings.email_use_tls:
                server.starttls()
            
            if settings.email_username and settings.email_password:
                server.login(settings.email_username, settings.email_password)
            
            server.send_message(msg)
        
        return {
            "status": "success",
            "recipients": recipients,
            "subject": subject,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def _create_html_email_body(
    report_name: str,
    description: str,
    data: list[dict[str, Any]],
    row_count: int,
) -> str:
    """Create HTML email body with data preview."""
    # Limit preview to first 10 rows
    preview_data = data[:10]
    
    # Build HTML table
    table_html = ""
    if preview_data:
        columns = list(preview_data[0].keys())
        
        table_html = "<table style='border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;'>"
        
        # Header
        table_html += "<thead><tr style='background-color: #4472C4; color: white;'>"
        for col in columns:
            table_html += f"<th style='padding: 12px; text-align: left; border: 1px solid #ddd;'>{col}</th>"
        table_html += "</tr></thead>"
        
        # Rows
        table_html += "<tbody>"
        for i, row in enumerate(preview_data):
            bg_color = "#f2f2f2" if i % 2 == 0 else "white"
            table_html += f"<tr style='background-color: {bg_color};'>"
            for col in columns:
                value = row.get(col, "")
                table_html += f"<td style='padding: 10px; border: 1px solid #ddd;'>{value}</td>"
            table_html += "</tr>"
        table_html += "</tbody></table>"
        
        if row_count > 10:
            table_html += f"<p style='margin-top: 10px; color: #666;'><em>Showing 10 of {row_count} rows. See attachment for full results.</em></p>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4472C4; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{report_name}</h1>
            </div>
            <div class="content">
                <p><strong>Description:</strong> {description}</p>
                <p><strong>Total Rows:</strong> {row_count}</p>
                <p><strong>Generated:</strong> {_get_current_timestamp()}</p>
                
                <h2>Data Preview</h2>
                {table_html}
            </div>
            <div class="footer">
                <p>This is an automated report from Database Query Assistant.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def _attach_file(msg: MIMEMultipart, filepath: str) -> None:
    """Attach a file to the email message."""
    path = Path(filepath)
    
    with open(path, "rb") as file:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(file.read())
    
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={path.name}",
    )
    
    msg.attach(part)


def _get_current_timestamp() -> str:
    """Get current timestamp as formatted string."""
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
