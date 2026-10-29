#!/usr/bin/env python3
"""
Unified 9:30 AM Executive Morning Briefing
Reads local .env credentials (zero cloud dependency), sorts unread Gmail via IMAP + Gemini,
checks local memory.md, and emails a unified morning digest to USER_EMAIL.
"""
import os
import sys
import smtplib
import email
import imaplib
import json
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from google import genai
from email.message import EmailMessage
from email.header import decode_header

AGENT0_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
load_dotenv(os.path.join(AGENT0_DIR, ".env"))

USER_NAME = os.getenv("USER_NAME", "Callie").strip()
USER_EMAIL = os.getenv("USER_EMAIL", "").strip()
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
GEMINI_KEY = os.getenv("GEMINI_FREE_API_KEY") or os.getenv("GEMINI_API_KEY", "").strip()
TIMEZONE = pytz.timezone("America/New_York")

def decode_mime_header(header_val):
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    decoded_string = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            decoded_string += part.decode(charset or "utf-8", errors="ignore")
        else:
            decoded_string += str(part)
    return decoded_string

def get_memory_projects():
    try:
        memory_path = os.path.join(AGENT0_DIR, "memory.md")
        if os.path.exists(memory_path):
            with open(memory_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "## Projects" in content:
                section = content.split("## Projects")[1].split("---")[0]
                return section.strip()
        return "• See ~/Agents/Agent 0/memory.md"
    except Exception as e:
        return f"• Error reading local memory: {e}"

def process_emails():
    retail_deals, finance_offers, newsletters_social, entertainment_sports, actionable_items = [], [], [], [], []
    archived_ids = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(USER_EMAIL, APP_PASSWORD)
        mail.select("INBOX")

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        status, response = mail.search(None, f'UNSEEN SINCE "{yesterday}"')
        if status != "OK" or not response[0]:
            mail.logout()
            return [], [], [], [], ["• No unread emails found."]

        msg_ids = response[0].split()
        emails_to_process = []
        msg_id_map = {}

        for msg_id in msg_ids[:30]:
            res, msg_data = mail.fetch(msg_id, "(BODY.PEEK[]<0.3000>)")
            if res != "OK":
                continue
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_mime_header(msg.get("Subject", "(No Subject)"))
                    sender = decode_mime_header(msg.get("From", "(Unknown Sender)"))
                    email_id_str = msg_id.decode("utf-8")
                    emails_to_process.append({"id": email_id_str, "sender": sender, "subject": subject})
                    msg_id_map[email_id_str] = {"id": msg_id, "sender": sender, "subject": subject}

        if emails_to_process and GEMINI_KEY:
            client = genai.Client(api_key=GEMINI_KEY)
            prompt = (
                "You are an AI Executive Assistant. Categorize the following emails.\n"
                "Categories must be EXACTLY ONE of: 'Retail and Deals', 'Finance and Offers', "
                "'Newsletters and Social', 'Entertainment and Sports', or 'Important/Actionable'.\n"
                "If 'Important/Actionable', provide a 1-sentence summary AND specific action_needed.\n"
                "Return ONLY a JSON array of objects with keys: 'id', 'category', 'summary', 'action_needed'.\n\n"
                + json.dumps(emails_to_process, indent=2)
            )

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )

            results = json.loads(response.text)
            if isinstance(results, dict) and "emails" in results:
                results = results["emails"]
            elif isinstance(results, dict) and len(results) == 1:
                results = list(results.values())[0]

            for res in results:
                m_id_str = str(res.get("id"))
                if m_id_str not in msg_id_map:
                    continue
                category = res.get("category", "Important/Actionable")
                summary = res.get("summary", "")
                action = res.get("action_needed", "")
                msg_id = msg_id_map[m_id_str]["id"]
                sender = msg_id_map[m_id_str]["sender"]
                formatted_item = f"[{sender}] - {summary}"

                if category == "Retail and Deals":
                    retail_deals.append(formatted_item)
                    archived_ids.append(msg_id)
                elif category == "Finance and Offers":
                    finance_offers.append(formatted_item)
                    archived_ids.append(msg_id)
                elif category == "Newsletters and Social":
                    newsletters_social.append(formatted_item)
                    archived_ids.append(msg_id)
                elif category == "Entertainment and Sports":
                    entertainment_sports.append(formatted_item)
                    archived_ids.append(msg_id)
                else:
                    actionable_items.append(f"• {formatted_item} -> [Action: {action}]")

        if archived_ids:
            for m_id in archived_ids:
                mail.store(m_id, "+FLAGS", "\\Deleted")
            mail.expunge()

        mail.logout()
        if not actionable_items:
            actionable_items.append("• No actionable personal emails today.")
        return retail_deals, finance_offers, newsletters_social, entertainment_sports, actionable_items
    except Exception as e:
        return [], [], [], [], [f"• Error fetching emails: {e}"]

def send_briefing():
    if not USER_EMAIL or not APP_PASSWORD:
        print("Error: USER_EMAIL or GMAIL_APP_PASSWORD missing in .env")
        sys.exit(1)

    today_str = datetime.now(TIMEZONE).strftime("%B %d, %Y")
    projects_str = get_memory_projects()
    retail, finance, newsletters, sports, actionable = process_emails()

    body = f"Hi {USER_NAME},\n\nHere is your 9:30 AM unified executive morning briefing for {today_str}:\n\n"
    body += "🚨 PRIORITY & ACTIONABLE EMAILS (Kept in Inbox)\n"
    for item in actionable:
        body += f"{item}\n"

    body += "\n🧹 AUTOMATED INBOX CLEANUP (Archived)\n"
    if retail: body += "* Retail & Deals:\n" + "\n".join([f"  - {i}" for i in retail]) + "\n"
    if finance: body += "* Finance & Offers:\n" + "\n".join([f"  - {i}" for i in finance]) + "\n"
    if newsletters: body += "* Newsletters & Social:\n" + "\n".join([f"  - {i}" for i in newsletters]) + "\n"
    if sports: body += "* Entertainment & Sports:\n" + "\n".join([f"  - {i}" for i in sports]) + "\n"
    if not (retail or finance or newsletters or sports):
        body += "* No promotional emails archived today.\n"

    body += "\n📌 ACTIVE PROJECTS & MEMORY\n" + projects_str + "\n\n"
    body += "Have a great day!\n- Agent 0"

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = f"9:30 AM Executive Briefing - {today_str}"
    msg["From"] = USER_EMAIL
    msg["To"] = USER_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(USER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
    print("Unified morning briefing sent successfully.")

if __name__ == "__main__":
    send_briefing()
