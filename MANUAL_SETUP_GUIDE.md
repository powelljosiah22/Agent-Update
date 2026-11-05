# 🍏 Antigravity Multi-Agent Ecosystem: Complete macOS Setup Manual

A comprehensive, beginner-friendly setup guide for installing **Google Antigravity 2.0**, **Agent 0**, and modular AI agents (**Theology & Biblical Philology**, **Academic Tutor**, and **Financial Coach**) on macOS.

---

## 🧭 System Overview & Division of Labor

The installation script (`./setup.sh`) automates 90% of the technical heavy lifting: creating directory trees, compiling isolated Python virtual environments, uncompressing morphological databases, configuring Model Context Protocol (MCP) servers, and launching background daemons.

However, **macOS security boundaries, Google authentication, and licensing require you to complete a few manual setup steps first**:

```
[Phase 1: Global Prerequisites]
Homebrew ➔ Git & GitHub ➔ Google Drive ➔ Google AI Studio (Student Plan) ➔ Antigravity 2.0 IDE
                                  │
                                  ▼
[Phase 2: Master Node Core]
Clone Repo ➔ Run ./setup.sh ➔ Select Modules ➔ Add API Key to .env
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
[Module 1: Theology & Philology] [Module 2: Academic Tutor]  [Module 3: Financial Coach]
- 100% Offline SQLite Exegesis   - Class Folders Ingestion   - yfinance & Factor Models
- WLC, SBLGNT, Septuagint (LXX)  - Hybrid Vector Search      - (Optional) Robinhood/Plaid
- Zero external APIs required    - (Optional) Obsidian App
```

---

## 🛠️ Phase 1: Global Prerequisites (Required for All Agents)

Complete these 6 steps once. They provide the foundation for all agents.

### Step 1: Install macOS Command Line Tools
1. Open the **Terminal** app on your Mac (Press `Cmd + Space`, type `Terminal`, and press `Return`).
2. Paste the following command and press `Return`:
   ```bash
   xcode-select --install
   ```
3. A popup dialog will appear asking to install developer tools. Click **Install** and agree to the license terms. (This takes about 2 minutes).

---

### Step 2: Install Homebrew (macOS Package Manager)
Homebrew is the standard package manager for Mac. It cleanly installs Git, Python, and other utilities without altering your core operating system.

1. In Terminal, paste and run:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Follow the on-screen prompts. When finished, Terminal will display 2–3 commands under **"Next steps"** to add Homebrew to your system path. Copy and paste those commands into Terminal.
3. Verify Homebrew is installed:
   ```bash
   brew --version
   ```
   *Official Documentation: [brew.sh](https://brew.sh)*

---

### Step 3: Install Git & Set Up GitHub Access
The multi-agent system is distributed via GitHub.

1. Install **Git** and the **GitHub CLI** via Homebrew:
   ```bash
   brew install git gh python@3.11 node
   ```
2. **Create a GitHub Account:** If you don't already have one, sign up for free at [github.com/signup](https://github.com/signup).
3. **Request Repository Access:** Provide your GitHub username to Josiah so he can add you as an authorized collaborator to the repository.
4. **Log in to GitHub via Terminal:**
   ```bash
   gh auth login
   ```
   - Select **GitHub.com**.
   - Select **HTTPS** (or **SSH** if you already use SSH keys).
   - Authenticate with your GitHub credentials: Choose **Login with a web browser**, copy the 8-character one-time code, press `Return`, and paste the code in your browser.

---

### Step 4: Install Google Drive for Desktop (REQUIRED)
All agents standardize file paths and document storage using Google Drive's native macOS mount point. This enables seamless cloud backups and note syncing.

1. Download **Google Drive for Desktop**: [google.com/drive/download](https://www.google.com/drive/download/)
2. Open the downloaded `.dmg` file and install the application.
3. Open Google Drive and sign in with your Google account.
4. Confirm your drive is mounted at:
   `/Users/<your-username>/Library/CloudStorage/GoogleDrive-<your-email>/My Drive/`

> [!IMPORTANT]
> Keep Google Drive running in your menu bar so note synchronization and inbox exports remain active.

---

### Step 5: Get Google AI Studio Student Plan (1 Year Free Gemini Pro)
Google provides students and developers with high-throughput API access to Gemini models.

1. Visit **Google AI Studio**: [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your student Google account (or standard Google account).
3. Follow the banner prompt to activate the **Student Plan** (1 year of free Gemini Pro access) or the standard Free Tier.
4. Navigate to **Get API Key**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
5. Click **Create API Key**, select or create a Google Cloud project, and copy the generated key string (starts with `AIza...`).
6. Save this key in a secure notes app—you will paste it into your agent configuration in Phase 2.

---

### Step 6: Install Google Antigravity 2.0 IDE
Antigravity is the agentic desktop IDE that runs the multi-agent system, provides pair-programming interfaces, and manages Model Context Protocol (MCP) servers.

1. Download the **Antigravity 2.0 IDE for Mac**: [antigravity.google](https://antigravity.google) (or the download link provided by Josiah).
2. Open the `.dmg` file and drag **Antigravity** into your `/Applications` folder.
3. Launch **Antigravity** from Applications.
   *(If macOS blocks it with an "Unidentified Developer" warning: Go to **Apple Menu  → System Settings → Privacy & Security**, scroll down, and click **Open Anyway**).*
4. Sign in to Antigravity using the same Google account associated with your Gemini API key.

---

## ⚡ Phase 2: Agent 0 (Master Node & Core Setup)

Agent 0 is the master coordinator. It routes requests, manages calendar and emails (if configured), and orchestrates specialized domain agents.

### Step 1: Clone the Repository
Open Terminal and clone the repository into your home directory:

```bash
cd ~
git clone https://github.com/powelljosiah22/Agent-Update.git ~/Agent-Update
```

*(If you were given a direct private repo URL, substitute it here).*

---

### Step 2: Run the Modular Setup Script
Run the automated installer:

```bash
cd ~/Agent-Update
chmod +x setup.sh update.sh
./setup.sh
```

During installation, the script will present a numbered menu:

```text
===========================================================
  Select Agent Modules to Install:
===========================================================
  [1] Academic Tutor only (Socratic tutor, class notes, TVM/Finance/Accounting)
  [2] Theology Agent & Philology DB (Biblical corpus, interlinear, Patristics)
  [3] Financial Coach only (Wealth management, factor models, market data)
  [4] All Agents (Full Suite: Academic + Theology + Financial + Agent 0)
===========================================================
```

* **For Wyatt:** Choose option **`[2] Theology Agent & Philology DB`** (or `[4]` if you want the full suite).
* **For Oliver:** Choose option **`[1] Academic Tutor`** (or `[4]` for the full suite).
* **For Power Users:** Choose option **`[4] All Agents`**.

> [!TIP]
> You can also run the installer non-interactively via flags:
> ```bash
> ./setup.sh --modules theology
> # or
> ./setup.sh --modules academic,theology
> # or
> ./setup.sh --all
> ```

---

### Step 3: Configure Your API Key
The installer creates a template configuration file at `~/Agents/Agent 0/.env`.

1. Open `~/Agents/Agent 0/.env` in any text editor (TextEdit, VS Code, or Antigravity):
   ```bash
   open -a TextEdit ~/Agents/Agent\ 0/.env
   ```
2. Paste your Google AI Studio key:
   ```env
   GEMINI_API_KEY=AIzaSyYourCopiedKeyHere
   ```
3. Save and close the file.
4. Sync the key to your agent's MCP servers:
   ```bash
   python3 ~/Agents/Agent\ 0/sync_env_to_mcp.py
   ```

---

### Step 4: Verify System Health
Run the diagnostic check to prove all components, virtual environments, and databases are operational:

```bash
python3 ~/Agent-Update/healthcheck.py
```
You should see all green checkmarks (`✅ OK`) for your selected modules.

---

### Step 5: Launch Antigravity Workspace
1. Open **Antigravity**.
2. Select **File → Open Folder...** (or `Cmd + O`).
3. Navigate to: `~/Agents/Agent 0/` and click **Open**.
4. Press `Cmd + Shift + P`, type **Reload Window**, and press `Return`.

You are now ready to chat with Agent 0!

---

## 🏛️ Phase 3: Module-Specific Setup & Usage (Optional)

Choose the module you installed below for specialized instructions:

---

### Module A: Theology Agent & Biblical Philology Engine

This module is designed for in-depth biblical exegesis, Patristics cross-referencing, and linguistic analysis over the Hebrew Old Testament (WLC), Greek New Testament (SBLGNT), and Greek Septuagint (LXX Rahlfs 1935).

#### 1. How It Operates
* **100% Offline Database:** The underlying SQLite database (`biblical_corpus.db`) is already installed on your Mac at `~/Agents/Theology Agent/philology_db/biblical_corpus.db`.
* **Zero External API Costs for Lexical Analysis:** Searching verses, roots, Strong's numbers, Abbott-Smith lexicons, and the Septuagint Lexical Bridge runs locally on your Mac's CPU with **zero token cost**.
* **Stateless Epistemic Firewall:** The Philology subagent does not read personal notes or bias itself with external doctrinal agendas—it strictly reports lexical grammar, syntax, and genre dispersion.

#### 2. Test It from Terminal
You can run direct queries from your Mac's terminal anytime:

```bash
# Test a Greek concept (finds θέλω, βούλομαι, ὑπακοή):
python3 ~/Agents/Theology\ Agent/philology_db/philology_engine.py vector "will; desire; obedience" --lang greek --n 5

# View an interlinear breakdown of Gethsemane:
python3 ~/Agents/Theology\ Agent/philology_db/philology_engine.py sql --mode interlinear --ref "Matt 26:39; Luke 22:42"
```

#### 3. Test It in Antigravity Chat
Inside Antigravity (`~/Agents/Agent 0`), simply type:
> *"Ask the Biblical Philologist to analyze the Greek lemmas for 'justification' in Romans 3 and Galatians 2 and check if the vocabulary aligns with the Septuagint."*

Agent 0 will automatically query `biblical_philologist` and return a structured **Single-Screen Scorecard** (`STATED` / `ALLOWED` / `INFERRED` / `NOT SUPPORTED`).

#### 4. (Optional) Exporting Study Notes to Second Brain
If you ask the agent to *"save this to inbox"*, it will format a clean Markdown note and write it to:
`/Users/<your-username>/Library/CloudStorage/GoogleDrive-<your-email>/My Drive/Second Brain/1-Inbox/`

---

### Module B: Academic Tutor (Socratic Problem Solver)

Designed for students tackling accounting, finance, economics, STEM, or humanities courses.

#### 1. Setting Up Class Materials
1. In Google Drive, create a folder for your current semester:
   `My Drive/Class Folders/Fall_2026/<COURSE_CODE>/` (e.g., `FIN_3105`, `ACG_3131`).
2. Drop your syllabi, lecture slides, and practice problem sets (PDF, DOCX, PPTX) into that folder.
3. The background daemon (`voice_to_brain`) will automatically convert, parse, and index them into local ChromaDB vector memory.

#### 2. (Optional) Install Obsidian
If you like visualizing notes in an interactive graph view:
1. Download **Obsidian for Mac**: [obsidian.md/download](https://obsidian.md/download)
2. Open Obsidian, click **Open folder as vault**, and select your `Second Brain` or `Class Folders` directory in Google Drive.
3. Recommended free community plugins:
   - **Dataview:** Dynamic note indexing.
   - **Paste URL into Selection:** Clean markdown link authoring.

#### 3. How to Study in Chat
Ask the Academic Tutor:
> *"Drill me on Bond Valuation and Yield to Maturity using the Socratic method. Give me one problem at a time and do not give me the answer."*

---

### Module C: Financial Coach (Quantitative Portfolio Studio)

Designed for tracking investments, personal balance sheets, and running Fama-French multi-factor regressions.

#### 1. Market Data
* Pre-configured with the `yfinance` MCP server for live, real-time stock and ETF lookups (quotes, financials, balance sheets, option chains).
* No manual API setup required—`yfinance` is open-source and ready immediately.

#### 2. Optional Account Linking (Plaid / Banking / Robinhood)
* If you want automated transaction tracking or banking summaries, Plaid API keys can be added to `~/Agents/Agent 0/.env`.
* If you do not use these features, leave them blank—Financial Coach will function as an investment analyst and valuation tutor without them.

---

## 🔄 Phase 4: How to Update Your Agents

When Josiah publishes new features, engine optimizations, or bug fixes:

1. Open Terminal.
2. Run the update script:
   ```bash
   cd ~/Agent-Update
   ./update.sh
   ```

### What `update.sh` Does:
* Performs a `git pull` from GitHub.
* Reads your saved profile (`~/.agents_profile`) to see which modules you have installed.
* Updates only your installed modules while **strictly preserving your personal data, API keys, notes, and customizations**.
* Re-runs `healthcheck.py` to confirm the update succeeded.

---

## 🧯 Phase 5: Common Mac Troubleshooting

### Problem 1: "App cannot be opened because it is from an unidentified developer"
* **Fix:** Open **System Settings  → Privacy & Security**, scroll down to the Security section, and click **Open Anyway** next to Antigravity.

### Problem 2: Python Command Not Found or Wrong Version
* macOS includes an older system Python. Ensure Homebrew's modern Python is used:
  ```bash
  which python3
  # Expected: /opt/homebrew/bin/python3 (Apple Silicon M1-M4)
  # Or:       /usr/local/bin/python3   (Intel Macs)
  ```
  If needed, run: `brew link --overwrite python@3.11`

### Problem 3: Google Drive Path Not Found
* If the setup script cannot locate Google Drive, verify that Google Drive for Desktop is running in your top menu bar. Check your mount path in Terminal:
  ```bash
  ls ~/Library/CloudStorage/
  ```
  You should see `GoogleDrive-<your-email>`.

### Problem 4: Antigravity Doesn't See the Subagents
* In Antigravity, press `Cmd + Shift + P`, type **Developer: Reload Window**, and press `Return`. This forces Antigravity to reload all MCP servers and agent configurations.

---

## 📋 Quick Reference Card

| Action | Command / Location |
| :--- | :--- |
| **Launch Antigravity** | `/Applications/Antigravity.app` |
| **Workspace Folder** | `~/Agents/Agent 0/` |
| **Update All Code** | `cd ~/Agent-Update && ./update.sh` |
| **Run Diagnostic** | `python3 ~/Agent-Update/healthcheck.py` |
| **API Key Config** | `~/Agents/Agent 0/.env` |
| **Philology DB** | `~/Agents/Theology Agent/philology_db/biblical_corpus.db` |
| **Google Drive** | `~/Library/CloudStorage/GoogleDrive-<email>/My Drive/` |
