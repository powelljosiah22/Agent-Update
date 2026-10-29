# 🚀 Callie's Multi-Agent & Second Brain Infrastructure — Complete Setup Guide

Welcome! This package contains a complete, depersonalized multi-agent AI & Second Brain ecosystem built for **Google Antigravity**.

---

## 📦 1. What Is Inside This Package?

| Component | Target Location on Your Mac | What It Does |
| :--- | :--- | :--- |
| **Agent 0 (Master Node)** | `~/Agents/Agent 0/` | Chief Executive Assistant: manages calendar, email, morning briefings, daemons, and orchestrates all specialist subagents. |
| **Academic Tutor** | `~/Agents/Academic Tutor/` | Socratic tutor connected to your course syllabi, slides, and practice problems via instant hybrid vector search (`<50ms`). |
| **Theology Agent** | `~/Agents/Theology Agent/` | Warm, rigorous theological & philosophical sparring partner (Tim Keller / C.S. Lewis style) connected to your Obsidian vault. |
| **Financial Coach** | `~/Agents/Financial_Coach/` | Quantitative wealth & portfolio specialist equipped with live `yfinance` market data, Fama-French 5-Factor datasets, and optional Robinhood integration. |
| **ChromaDB Hybrid Search Daemon** | `~/Agents/Agent 0/mcp/obsidian_search/` | Persistent local HTTP vector + lexical search engine (`127.0.0.1:8085`) over your Obsidian Vault and Class Folders. |
| **Voice-to-Brain & Document Pipeline** | `~/Agents/Agent 0/voice_to_brain/` | Watches `00_Inbox/Voice_Notes` for audio memos and `Class Folders` for raw PDFs/PPTX/DOCX/XLSX, auto-transcribing, parsing, indexing, and semantically linking notes. |
| **Global Rules & Skills** | `~/.gemini/config/{rules,skills}/` | Enforces Calibrated Candor (3-layer objective feedback), KaTeX math rendering safety, Knowledge Lifecycle auto-learning, and interactive HTML quiz generation. |

---

## 🤝 2. Human vs. Agent Division of Labor (Why Certain Steps Require You)

Your Antigravity agent is powerful, but **macOS security boundaries and Antigravity's sandbox enforce strict limits on what an AI agent can do without a human**:

| Task | Who Does It? | Why? |
| :--- | :--- | :--- |
| Creating folder trees, building Python virtual environments, installing `pip` & `npm` packages, indexing ChromaDB, configuring `mcp_config.json` | **Automated (`./setup.sh` or Agent)** | 100% deterministic local file/package operations. |
| Tailoring your courses, schedule, spiritual study, and financial goals in `context.md` and `memory.md` | **Agent (via Onboarding Interview)** | Agent 0 interviews you in chat and updates all 4 workspaces automatically. |
| Installing **Python 3**, **Node.js**, **Obsidian**, or **Google Drive for Desktop** | **You (Human)** | Requires macOS installer / Homebrew privileges. |
| Generating your **Gemini API Key**, **16-character Gmail App Password**, and **Perplexity API Key** | **You (Human)** | Requires logging into your personal accounts with 2FA in your web browser. |
| Clicking **"Allow"** in the Google OAuth browser popup (`generate_token.py`) | **You (Human)** | Google OAuth security requires interactive human browser consent. |
| Granting **macOS Full Disk Access** (if your Vault is in `~/Documents` or Google Drive) | **You (Human)** | macOS TCC security blocks background daemons from protected folders unless toggled in **System Settings → Privacy & Security**. |
| Pressing **`Cmd + Shift + P` → `Reload Window`** in Antigravity | **You (Human)** | Antigravity loads `~/.gemini/config/mcp_config.json` and global rules on window startup. |

---

## ⚡ 3. Step-by-Step Setup Instructions (10–15 Minutes Total)

### Step 1: Check Prerequisites (2 Mins)
Open the **Terminal** app on your Mac (`Cmd + Space`, type `Terminal`) and verify Python 3 and Node.js are installed:
```bash
python3 --version
node --version
```
- If either is missing, install [Homebrew](https://brew.sh/) and run:
  ```bash
  brew install python node
  ```
- *(Recommended)* Install [Obsidian](https://obsidian.md/) for viewing your Second Brain notes.

---

### Step 2: Run the Automated Installer (`./setup.sh`) (3 Mins)
Unzip `Callie_Agent_Infrastructure.zip`, open **Terminal** inside the unzipped `Callie_Agent_Infrastructure` folder, and run:
```bash
cd /path/to/Callie_Agent_Infrastructure
chmod +x setup.sh
./setup.sh
```
**What `setup.sh` does automatically:**
1. Prompts you for your **Obsidian Vault path** (auto-detects Google Drive if installed, or defaults to `~/SecondBrain/Obsidian_Vault`), your **Class Folders path**, and your **Gmail address**.
2. Installs all Global Rules, Custom Skills, and `mcp_config.json` into `~/.gemini/config/`.
3. Installs all 4 Agent Workspaces (`Agent 0`, `Academic Tutor`, `Theology Agent`, `Financial_Coach`) into `~/Agents/`.
4. Builds both isolated Python virtual environments (`~/Agents/Agent 0/.venv` and `~/Agents/Agent 0/mcp/obsidian_search/venv`) and installs all required Python and Node.js packages.
5. Pre-warms ChromaDB and starts the local search daemon (`127.0.0.1:8085`) and `voice_to_brain` daemon, plus a 15-minute self-healing watchdog cron job.
6. Runs `healthcheck.py` to confirm every component is installed cleanly.

---

### Step 3: Add Your API Keys to One File (`~/Agents/Agent 0/.env`) (5 Mins)
Open `~/Agents/Agent 0/.env` in any text editor (or give your keys to Agent 0 in chat and let Agent 0 write them for you!):

1. **`GEMINI_API_KEY` (Required for Voice-to-Brain & Deep Vault Research):**
   - Go to [Google AI Studio (aistudio.google.com/apikey)](https://aistudio.google.com/apikey) → Click **Create API Key** → Paste into `GEMINI_API_KEY=...`
2. **`GMAIL_APP_PASSWORD` (Required for Email Sender MCP & Morning Briefings):**
   - Go to [Google Account App Passwords (myaccount.google.com/apppasswords)](https://myaccount.google.com/apppasswords) (requires 2-Step Verification enabled on your Google account).
   - Type `Antigravity Agent` → Click **Create** → Copy the 16-character password (remove spaces) into `GMAIL_APP_PASSWORD=...`
3. **`PERPLEXITY_API_KEY` (Optional — for live web research via `perplexity-ask` MCP):**
   - Go to [Perplexity API Settings (perplexity.ai/settings/api)](https://www.perplexity.ai/settings/api) → Copy key into `PERPLEXITY_API_KEY=...`

Then run this single command in Terminal so your `.env` keys automatically sync into `~/.gemini/config/mcp_config.json`:
```bash
python3 ~/Agents/Agent\ 0/sync_env_to_mcp.py
```

---

### Step 4: Optional OAuth Integrations (Google Drive / Robinhood)
- **Google Drive & Calendar OAuth (`google-drive` MCP & Morning Briefing Calendar):**
  Follow `~/Agents/Agent 0/credentials/README_OAUTH.md` to drop your `credentials.json` into `~/Agents/Agent 0/credentials/` and run:
  ```bash
  ~/Agents/Agent\ 0/.venv/bin/python ~/Agents/Agent\ 0/credentials/generate_token.py
  ```
- **Robinhood Portfolio Integration (Optional — for Financial Coach):**
  If you want live Robinhood positions, add `ROBINHOOD_USERNAME` and `ROBINHOOD_PASSWORD` to `~/Agents/Agent 0/.env` and run:
  ```bash
  ~/Agents/Agent\ 0/.venv/bin/python ~/Agents/Agent\ 0/mcp/robinhood/auth_flow.py
  ```

---

### Step 5: Launch Antigravity & Run the Agent Onboarding Wizard (2 Mins)
1. Open **Google Antigravity** and open the folder **`~/Agents/Agent 0`** as your workspace.
2. Press **`Cmd + Shift + P`** → Run **`Developer: Reload Window`** so Antigravity loads your new MCP servers and global rules.
3. Copy and paste the prompt below into your chat with **Agent 0**:

```text
Hi Agent 0! I just installed the Callie_Agent_Infrastructure package. Please read ~/Agents/Agent 0/AGENT_SETUP_WIZARD.md, run healthcheck.py to verify our setup, and walk me through the interactive onboarding interview to personalize Agent 0, Academic Tutor, Theology Agent, and Financial Coach for me!
```

---

## 🛠️ 4. Everyday Usage Cheat Sheet

- **Switching Personas:** Open any of the 4 folders in `~/Agents/` (`Agent 0`, `Academic Tutor`, `Theology Agent`, or `Financial_Coach`) as your workspace in Antigravity, and the agent automatically adopts that specialist persona and memory! Or stay in `~/Agents/Agent 0` and let Agent 0 invoke the others as subagents.
- **Adding Course Materials:** Create a folder for each class inside your `Class Folders` directory (e.g., `BIO_201/1_Syllabus_and_Schedule`, `1_Lectures_and_Slides`, `1_Homework_and_Problems`, `1_Exams_and_Reviews`). Drop any PDF, PPTX, DOCX, or XLSX inside—the background daemon automatically converts it to Markdown and indexes it into ChromaDB!
- **Adding Voice Memos:** Drop any `.m4a`, `.mp3`, or `.wav` recording into `00_Inbox/Voice_Notes/` inside your Obsidian Vault. Within seconds, `brain_daemon.py` transcribes it, classifies it, creates a structured note, and links it across your vault.
