import re
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from fastmcp import FastMCP

import mimetypes
from typing import List, Optional

# Load credentials from .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Initialize the MCP Server
mcp = FastMCP("EmailSender")

@mcp.tool()
def send_email(to_email: str, subject: str, body: str, attachments: Optional[List[str]] = None, html_body: Optional[str] = None) -> str:
    """
    Sends an email using the user's Gmail account via SMTP.
    
    Args:
        to_email: The recipient's email address.
        subject: The subject line of the email.
        body: The plain text body content of the email (or fallback).
        attachments: Optional list of absolute file paths to attach to the email.
        html_body: Optional rich HTML body content. If provided (or if body contains HTML tags),
                   the email will render with rich HTML styling while preserving body as plain-text fallback.
    """
    sender_email = "user@example.com"
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not app_password:
        return "Error: GMAIL_APP_PASSWORD not set in .env file."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    # Determine HTML vs plain text
    target_html = html_body
    if not target_html and any(tag in body.lower() for tag in ["<html", "<div", "<p>", "<table", "<body"]):
        target_html = body

    if target_html:
        # If body is identical to HTML, strip basic tags for the plain text fallback
        plain_text = re.sub(r'<[^>]+>', '', body).strip() if body == target_html else body
        msg.set_content(plain_text)
        msg.add_alternative(target_html, subtype='html')
    else:
        msg.set_content(body)

    if attachments:
        for file_path in attachments:
            if os.path.exists(file_path):
                ctype, encoding = mimetypes.guess_type(file_path)
                if ctype is None or encoding is not None:
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                with open(file_path, 'rb') as fp:
                    msg.add_attachment(
                        fp.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(file_path)
                    )
            else:
                return f"Error: Attachment file not found at path: {file_path}"

    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        return f"Email successfully sent to {to_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

if __name__ == "__main__":
    # Start the MCP stdio server
    mcp.run()
