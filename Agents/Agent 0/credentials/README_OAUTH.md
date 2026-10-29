# Google Workspace & Google Drive OAuth Setup (Optional)

This directory stores your local OAuth 2.0 credentials for the `google-workspace` (Gmail & Calendar) and `google-drive` MCP servers.

## Setup Steps (If you want Gmail, Google Calendar, and Google Drive MCP tools)

1. **Create a Google Cloud OAuth Client ID (Desktop App):**
   - Visit the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a project and enable the **Gmail API**, **Google Calendar API**, and **Google Drive API**.
   - Go to **APIs & Services -> Credentials -> Create Credentials -> OAuth client ID**.
   - Select **Desktop app**, download the JSON file, and save it in this folder as:
     `~/Agents/Agent 0/credentials/gauth.json`

2. **Configure `accounts.json`:**
   - Copy `accounts.json.template` to `accounts.json` and put your Gmail address inside (Note: `setup.sh` automatically populates this if `USER_EMAIL` is set in `.env`).

3. **Authorize in Browser (Human Action Required):**
   - Run the token generator script:
     ```bash
     "$HOME/Agents/Agent 0/.venv/bin/python" "$HOME/Agents/Agent 0/credentials/generate_token.py"
     ```
   - A browser window will open asking you to sign into your Google Account and click **Allow**.
   - This saves `.oauth2.<your_email>.json` in this folder.
