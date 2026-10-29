#!/usr/bin/env python3
import json
import os
import sys
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

CREDS_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT0_DIR = os.path.dirname(CREDS_DIR)
load_dotenv(os.path.join(AGENT0_DIR, ".env"))

def main():
    user_email = os.getenv("USER_EMAIL", "").strip()
    if not user_email and len(sys.argv) > 1:
        user_email = sys.argv[1].strip()
    if not user_email or user_email == "__USER_EMAIL__":
        user_email = input("Enter your Gmail address for OAuth token storage: ").strip()

    gauth_path = os.path.join(CREDS_DIR, "gauth.json")
    if not os.path.exists(gauth_path):
        print(f"Error: gauth.json not found at {gauth_path}.")
        print("Please see README_OAUTH.md in this folder for instructions.")
        sys.exit(1)

    with open(gauth_path, "r", encoding="utf-8") as f:
        raw_gauth = f.read()
    if "YOUR_GOOGLE_OAUTH_CLIENT_ID" in raw_gauth:
        print("Error: gauth.json still contains the placeholder client_id.")
        print("Please download your Desktop OAuth client JSON from Google Cloud Console and save it as:")
        print(f"  {gauth_path}")
        print("See README_OAUTH.md for step-by-step instructions.")
        sys.exit(1)

    scopes = [
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/calendar",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/drive"
    ]

    flow = InstalledAppFlow.from_client_secrets_file(gauth_path, scopes)
    print("Opening browser for Google OAuth authorization...", flush=True)
    creds = flow.run_local_server(port=0)

    creds_data = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "scope": " ".join(creds.scopes) if isinstance(creds.scopes, (list, set)) else str(creds.scopes),
        "token_type": "Bearer",
        "id_token": creds.id_token,
        "expiry_date": int(creds.expiry.timestamp() * 1000) if creds.expiry else None
    }

    out_file = os.path.join(CREDS_DIR, f".oauth2.{user_email}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(creds_data, f, indent=2)

    print(f"SUCCESS: OAuth token saved to {out_file}")

if __name__ == "__main__":
    main()
