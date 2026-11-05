# 🍏 Zero-Terminal Setup Guide: Antigravity Multi-Agent Ecosystem for macOS

A universal, non-technical setup manual for installing **Google Antigravity 2.0**, **Agent 0**, and modular AI agents (**Theology & Biblical Philology**, **Academic Tutor**, or **Financial Coach**) on macOS.

> [!TIP]
> **Zero Terminal Commands Required:** You do **not** need to open the macOS Terminal app or type shell commands. Simply install a few standard Mac applications, set up your accounts in your web browser, and **instruct the AI agent inside Antigravity** to clone the repository, compile environments, unpack the databases, and configure all tools autonomously.

---

## 🧭 The 3-Step Overview

```
[Step 1: Download Mac Apps & Set Up Accounts (Web Browser)]
Antigravity 2.0 IDE ➔ Google Drive ➔ Python 3 Mac Installer ➔ Gemini API Key
                                  │
                                  ▼
[Step 2: Open Antigravity & Open Your Home Folder]
Launch Antigravity ➔ Open Folder (Home ~) ➔ Open Chat Panel (Cmd + L)
                                  │
                                  ▼
[Step 3: Hand the Reins to the AI Agent (One Chat Message!)]
Paste the Setup Kickoff Message into Chat ➔ Agent clones repo & runs setup autonomously
```

---

## 🖥️ Step 1: Download Mac Apps & Set Up Accounts (In Your Browser)

Complete these straightforward downloads in your web browser.

### 1. Download Google Antigravity 2.0 IDE for Mac
Antigravity is the AI coding desktop application that houses and runs your multi-agent system.
* **Download Link:** [antigravity.google](https://antigravity.google) (or the official download link provided by your administrator).
* **Install:** Open the downloaded `.dmg` file and drag **Antigravity** into your **Applications** folder.
* **First Launch:** Open Antigravity from Applications.
  *(If macOS displays an "Unidentified Developer" warning: Open **Apple Menu  → System Settings → Privacy & Security**, scroll down, and click **Open Anyway**).*

---

### 2. Download Google Drive for Desktop (REQUIRED)
All agents standardize file paths and document storage using Google Drive's native macOS mount point for automatic cloud backups, study note exports, and course material syncing.
* **Download Link:** [google.com/drive/download](https://www.google.com/drive/download/)
* **Install & Sign In:** Open the downloaded `.dmg`, run the installer, and sign in with your Google account.
* **Confirm:** Ensure Google Drive is running in your Mac's top menu bar.

---

### 3. Get 1 Year of Free Gemini Pro (Google AI Studio Student Plan)
Google provides students, educators, and developers with high-throughput API access to the Gemini Pro model.
* **Step A:** Go to [aistudio.google.com](https://aistudio.google.com) in your browser.
* **Step B:** Sign in with your university/student Google account (or standard Google account) to activate the **Student Plan** (1 year of free Gemini Pro access) or the standard Free Tier.
* **Step C:** Navigate to the API Key page: [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
* **Step D:** Click **Create API Key**, select or create a Google Cloud project, and copy the generated key string (starts with `AIza...`).
* **Step E:** Keep this key copied or saved in a secure note—you will paste it into Antigravity in Step 3!

---

### 4. GitHub Account Access
The multi-agent codebase is hosted securely on GitHub.
* If you do not have a GitHub account, sign up for free at [github.com/signup](https://github.com/signup).
* Send your GitHub username to the repository owner so they can grant your account access to the distribution repository:
  `https://github.com/powelljosiah22/Agent-Update.git`

---

### 5. Install Python 3 via the 1-Click Mac Installer
To ensure your Mac has the modern Python engine required for local morphological search and vector embeddings without using the command line:
* **Download Link:** [Python 3.11 for macOS (Official Installer)](https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg) *(or latest stable Python 3 from [python.org/downloads/macos](https://www.python.org/downloads/macos/))*.
* **Install:** Double-click the downloaded `.pkg` file and click **Continue**, **Agree**, and **Install** like any standard Mac application.

---

### 6. (Optional) Download Obsidian for Note-Taking
If you want to view, write, or visualize notes in your Second Brain:
* **Download Link:** [obsidian.md/download](https://obsidian.md/download)
* **Install:** Drag Obsidian to your Applications folder.

---

## 🚀 Step 2: Open Antigravity & Start Chat

1. Open **Antigravity** from your Applications folder.
2. In the top menu bar, click **File → Open Folder...** (or press `Cmd + O`).
3. Select your **Home** folder (your user folder, e.g. `Users/<your-name>` or `~`) and click **Open**.
4. Open the **Antigravity Chat Panel** on the right side of the screen (or press `Cmd + L`).

---

## 🤖 Step 3: Hand the Reins to the AI Agent (One Chat Message!)

You will now let Antigravity's autonomous agent clone the repository, unpack the databases, configure virtual environments, and verify the installation.

1. In the Antigravity chat box, copy and paste the **Zero-Terminal Setup Kickoff Message** below:

```text
Hey! I'm setting up my agent system on this Mac. Please clone the repository and run the setup autonomously for me.

My Details:
- Repository URL: https://github.com/powelljosiah22/Agent-Update.git
- Selected Module: [CHOOSE ONE: Theology & Philology / Academic Tutor / Financial Coach / All Agents]
- Gemini API Key: [PASTE YOUR KEY HERE]
- Google Drive Email: [PASTE YOUR GOOGLE EMAIL HERE]

Please execute the following in the background:
1. Clone the repository into ~/Agent-Update (or git pull if already present).
2. Run ./setup.sh with the flag for my selected module.
3. Populate ~/Agents/Agent 0/.env with my Gemini API key and email.
4. Run sync_env_to_mcp.py and healthcheck.py to verify all systems.
```

2. Replace the bracketed placeholders with your actual details and press **Enter**.

---

### What the AI Agent Does Autonomously in the Background:
- ✅ Executes `git clone` to pull the distribution code into `~/Agent-Update`.
- ✅ Detects your Python 3 installation and builds isolated virtual environments (`.venv`).
- ✅ Runs `./setup.sh` with your requested module flag (`--modules theology`, `--modules academic`, `--modules finance`, or `--all`).
- ✅ Unpacks the complete 77MB offline biblical corpus database (`biblical_corpus.db`).
- ✅ Creates `~/Agents/Agent 0/.env` and writes your `GEMINI_API_KEY` and email.
- ✅ Syncs your API credentials into Antigravity's MCP configuration (`sync_env_to_mcp.py`).
- ✅ Runs the diagnostic health check (`healthcheck.py`) and reports a clean scorecard in chat.

---

## 🎉 Step 4: The Final 2-Click Launch

When the agent finishes running the setup commands, it will send a message in chat letting you know everything is verified. Complete these two final clicks to switch into your new operational workspace:

1. In the top menu bar, click **File → Open Folder...** (or press `Cmd + O`).
2. Navigate to your Home folder, open **`Agents`**, select **`Agent 0`**, and click **Open**.
3. Press **`Cmd + Shift + P`**, type **`Developer: Reload Window`**, and press `Return`.

**Congratulations! Your multi-agent ecosystem is live.**

---

## 🏛️ Module Overview & Usage Guide

Select the module that fits your focus:

### Module Option 1: Theology Agent & Biblical Philology Engine
Includes the complete, text-bound **Biblical Philology Engine** operating over the Hebrew Old Testament (WLC), Greek New Testament (SBLGNT), and Greek Septuagint (LXX Rahlfs 1935).

* **100% Offline & Free Exegesis:** The morphological database runs locally on your Mac. Querying Hebrew roots, Greek lemmas, Strong's glosses, and the Septuagint bridge incurs zero API token costs.
* **How to Talk to It in Chat:** In Antigravity's chat, simply ask:
  > *"Ask the Biblical Philologist to test Romans 3:24–26 and see how the Greek words for redemption (ἀπολύτρωσις) and propitiation (ἱλαστήριον) are used in the Septuagint."*
  > 
  > *"Test the doctrine of Christ's two wills in Gethsemane (Matt 26:39; Luke 22:42) and give me the single-screen scorecard."*
* **Saving Notes:** Tell the agent *"Save this to inbox"*, and it will format a clean Markdown study note and save it to your Google Drive (`Second Brain/1-Inbox/`).

---

### Module Option 2: Academic Tutor (Socratic Problem Solver)
Includes the Socratic **Academic Tutor** connected to course syllabi, slides, and practice problem sets.

* **Add Class Files:** In Google Drive, create a folder for your course: `My Drive/Class Folders/Fall_2026/<COURSE_CODE>/` and drop your syllabi, lecture slides, or practice PDFs into it. The background daemon will parse and index them into local vector memory.
* **How to Study in Chat:**
  > *"Drill me on TVM bond valuation using the Socratic method. Give me one problem at a time and don't give me the answer."*

---

### Module Option 3: Financial Coach (Quantitative Portfolio Studio)
Includes quantitative portfolio analysis, Fama-French multi-factor regressions, and live market data.

* **Live Market Data:** Pre-configured with the open-source `yfinance` MCP server for live stock and ETF quotes, financials, and balance sheets.
* **Optional Account Linking:** Optional banking or Robinhood integrations can be configured if desired; otherwise, the agent operates as a standalone quantitative analyst.

---

### Module Option 4: Full Multi-Agent Suite
Installs all domain agents (**Academic Tutor**, **Theology Agent & Philology DB**, and **Financial Coach**) managed by **Agent 0** as the Master Node.

---

## 🔄 Future Updates (Also Zero-Terminal!)

When updates, bug fixes, or new philological features are published to GitHub, you do not need to touch the terminal. Simply open Antigravity, go to chat, and say:

> *"Please update my agents from GitHub."*

The agent will run `./update.sh` in the background, pull the latest changes, preserve all of your personal notes, API keys, and settings, and re-run the healthcheck!

---

## 🧯 Quick Help & FAQ

* **Q: Antigravity says "App can't be opened because it is from an unidentified developer"?**
  * *Fix:* Open **System Settings  → Privacy & Security**, scroll down to the Security section, and click **Open Anyway**.
* **Q: Do I need to keep Terminal open while using Antigravity?**
  * *No.* Terminal never needs to be opened. Antigravity manages all background tools, databases, and Python virtual environments autonomously.
* **Q: Can I install more modules later?**
  * *Yes.* Simply tell the agent in chat: *"Please install the Academic Tutor module as well"* and it will execute the modular installer for you.
