#!/usr/bin/env python3
"""
Evening Academic Briefing & Vector Intelligence Mailer
Queries local ChromaDB (port 8085) for tomorrow's scheduled courses and sends
an HTML preparation digest to USER_EMAIL via Gmail SMTP.
Configure CLASS_SCHEDULE and EXAM_CALENDAR below for your current semester.
"""
import os
import json
import smtplib
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

AGENT0_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
load_dotenv(os.path.join(AGENT0_DIR, ".env"))

USER_EMAIL = os.getenv("USER_EMAIL", "").strip()
USER_NAME = os.getenv("USER_NAME", "Callie").strip()
TIMEZONE = ZoneInfo("America/New_York")
CHROMA_URL = os.getenv("CHROMADB_URL", "http://127.0.0.1:8085")

# Customize your weekly class schedule (0 = Monday, 1 = Tuesday, 2 = Wednesday, 3 = Thursday, 4 = Friday)
CLASS_SCHEDULE = {
    0: [
        # Example: {"code": "SPA 3112", "name": "Basic Phonetics", "time": "10:30 AM - 11:45 AM", "location": "Main Campus", "instructor": "Professor", "query": "SPA 3112 phonetics IPA transcription"}
    ],
    1: [],
    2: [],
    3: [],
    4: []
}

# Customize upcoming exam dates ("YYYY-MM-DD")
EXAM_CALENDAR = [
    # Example: {"date": "2026-11-05", "course": "SPA 3112", "name": "Exam 2", "location": "In-Class"}
]

def query_vector_db(query, course="", n_results=2):
    try:
        req = urllib.request.Request(
            CHROMA_URL,
            data=json.dumps({"query": query, "n_results": n_results, "target": "all", "course": course}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result_text = data.get("result", "")
            lines = [line for line in result_text.split("\n") if line.strip() and not line.startswith("---")]
            return " ".join(lines[:3])[:280] + "..." if lines else "Review core chapter readings and lecture notes."
    except Exception:
        return "Review core chapter readings and lecture notes."

def build_reminder_email(target_date=None):
    if target_date is None:
        target_date = datetime.now(TIMEZONE).date() + timedelta(days=1)

    weekday = target_date.weekday()
    day_name = target_date.strftime("%A")
    formatted_date = target_date.strftime("%B %d, %Y")
    classes_tomorrow = CLASS_SCHEDULE.get(weekday, [])

    upcoming_exams = []
    for exam in EXAM_CALENDAR:
        exam_dt = datetime.strptime(exam["date"], "%Y-%m-%d").date()
        days_until = (exam_dt - target_date).days
        if 0 <= days_until <= 14:
            upcoming_exams.append({**exam, "days_until": days_until})

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 680px; margin: 0 auto; background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }}
            .header {{ background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%); color: #ffffff; padding: 28px 32px; border-bottom: 3px solid #52b788; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 6px 0 0 0; font-size: 14px; color: #d8f3dc; }}
            .content {{ padding: 32px; }}
            .section-title {{ font-size: 14px; font-weight: 700; color: #52b788; text-transform: uppercase; margin-top: 24px; margin-bottom: 16px; border-bottom: 1px solid #334155; padding-bottom: 6px; }}
            .card {{ background: #0f172a; border-left: 4px solid #52b788; border-radius: 8px; padding: 18px 20px; margin-bottom: 20px; }}
            .course-code {{ font-size: 18px; font-weight: 700; color: #74c69d; }}
            .course-time {{ font-size: 13px; font-weight: 600; color: #d8f3dc; background: #1b4332; padding: 4px 10px; border-radius: 20px; float: right; }}
            .detail-row {{ font-size: 14px; margin: 8px 0; color: #94a3b8; }}
            .vector-snippet {{ background: #182232; border: 1px dashed #334155; border-radius: 6px; padding: 10px 12px; font-size: 12px; color: #cbd5e1; margin-top: 10px; font-style: italic; }}
            .alert-box {{ background: #451a03; border-left: 4px solid #f97316; padding: 14px 18px; border-radius: 8px; margin-bottom: 24px; }}
            .no-class {{ background: #14532d; border: 1px solid #22c55e; border-radius: 8px; padding: 20px; text-align: center; color: #dcfce7; font-weight: 600; }}
            .footer {{ background: #0f172a; text-align: center; padding: 18px; font-size: 12px; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ Academic Briefing & Vector Intelligence</h1>
                <p>Hi {USER_NAME} &bull; Preparation for <strong>{day_name}, {formatted_date}</strong></p>
            </div>
            <div class="content">
    """

    if upcoming_exams:
        html += '<div class="alert-box"><div style="font-weight:700; color:#fdba74; font-size:14px; margin-bottom:4px;">🚨 UPCOMING EXAM & DEADLINE COUNTDOWN</div>'
        for ex in upcoming_exams:
            days_str = "TODAY / TOMORROW" if ex["days_until"] <= 1 else f"in {ex['days_until']} days"
            html += f"<div style='font-size:13px; color:#ffedd5; margin-top:4px;'>• <strong>{ex['course']} - {ex['name']}</strong> ({ex['location']}) — <em>{days_str} ({ex['date']})</em></div>"
        html += "</div>"

    html += f"<div class='section-title'>🗓️ Tomorrow's Schedule ({day_name})</div>"

    if classes_tomorrow:
        for cls in classes_tomorrow:
            vector_snippet = query_vector_db(cls.get("query", cls["code"]), course=cls["code"].replace(" ", "_"))
            html += f"""
                <div class="card">
                    <div>
                        <span class="course-code">{cls['code']}: {cls['name']}</span>
                        <span class="course-time">🕒 {cls['time']}</span>
                    </div>
                    <div class="detail-row">📍 <strong>Location:</strong> {cls['location']} &bull; 👤 <strong>Instructor:</strong> {cls['instructor']}</div>
                    <div class="vector-snippet">🧠 <strong>ChromaDB Vector Context:</strong> "{vector_snippet}"</div>
                </div>
            """
    else:
        html += f'<div class="no-class">🎉 No lectures scheduled in CLASS_SCHEDULE for {day_name}!</div>'

    html += """
            </div>
            <div class="footer">
                Agent 0 Academic Planning Engine &bull; ChromaDB Vector Daemon Active (Port 8085)
            </div>
        </div>
    </body>
    </html>
    """
    return html, day_name, formatted_date

def send_evening_class_reminder(target_date=None):
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if not USER_EMAIL or not app_password:
        print("Error: USER_EMAIL or GMAIL_APP_PASSWORD not configured in .env.")
        return False

    html_content, day_name, formatted_date = build_reminder_email(target_date)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚡ Academic Briefing: {day_name}, {formatted_date}"
    msg["From"] = USER_EMAIL
    msg["To"] = USER_EMAIL
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(USER_EMAIL, app_password)
            server.send_message(msg)
        print(f"Academic briefing successfully sent to {USER_EMAIL} for {day_name}, {formatted_date}.")
        return True
    except Exception as e:
        print(f"Failed to send academic briefing email: {e}")
        return False

if __name__ == "__main__":
    send_evening_class_reminder()
