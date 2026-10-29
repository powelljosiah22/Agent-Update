#!/usr/bin/env python3
import os
import smtplib
import mimetypes
from email.message import EmailMessage
from typing import List, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load credentials dynamically relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

mcp = FastMCP("EmailSender")

@mcp.tool()
def send_email(to_email: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> str:
    """
    Sends an email using the user's Gmail account via SMTP.

    Args:
        to_email: The recipient's email address.
        subject: The subject line of the email.
        body: The plain text body content of the email.
        attachments: Optional list of absolute file paths to attach to the email.
    """
    sender_email = os.getenv("USER_EMAIL", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not sender_email:
        return "Error: USER_EMAIL is not configured in ~/Agents/Agent 0/.env."
    if not app_password:
        return "Error: GMAIL_APP_PASSWORD is not configured in ~/Agents/Agent 0/.env."

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    if attachments:
        for file_path in attachments:
            expanded_path = os.path.expanduser(file_path)
            if os.path.exists(expanded_path):
                ctype, encoding = mimetypes.guess_type(expanded_path)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"
                maintype, subtype = ctype.split("/", 1)
                with open(expanded_path, "rb") as fp:
                    msg.add_attachment(
                        fp.read(),
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(expanded_path)
                    )
            else:
                return f"Error: Attachment file not found at path: {expanded_path}"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        return f"Email successfully sent to {to_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

if __name__ == "__main__":
    mcp.run()
