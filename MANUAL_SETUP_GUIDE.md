# 🍏 Zero-Terminal Setup Guide: Antigravity Multi-Agent Ecosystem for Mac

A completely non-technical, GUI-first setup manual for **Wyatt**, **Oliver**, and new users installing **Google Antigravity 2.0**, **Agent 0**, and modular AI agents (**Theology & Biblical Philology**, **Academic Tutor**, or **Financial Coach**) on macOS.

> [!TIP]
> **No Terminal Required:** You do **not** need to open the macOS Terminal app or type complex shell commands. You will simply download a few standard Mac apps, set up your accounts in your web browser, and then **paste a single message to your AI agent in Antigravity**, which handles all installation, compilation, database unpacking, and configuration behind the scenes.

---

## 🧭 The 3-Step Overview

```
[Step 1: Download Mac Apps & Set Up Accounts (Web Browser)]
Antigravity 2.0 IDE ➔ Google Drive ➔ Python 3 Installer ➔ Google AI Studio Key
                                  │
                                  ▼
[Step 2: Clone the Project via Antigravity GUI]
Open Antigravity ➔ Click "Clone Git Repository" ➔ Paste Repo Link ➔ Click Open
                                  │
                                  ▼
[Step 3: Hand the Reins to the AI Agent (One Chat Message!)]
Paste the Setup Kickoff Message into Chat ➔ Agent runs all scripts autonomously
```

---

## 🖥️ Step 1: Download Mac Apps & Set Up Accounts (In Your Browser)

Complete these 5 straightforward downloads in your web browser.

### 1. Download Google Antigravity 2.0 IDE for Mac
Antigravity is the AI coding desktop application that houses your multi-agent system.
* **Download Link:** [antigravity.google](https://antigravity.google) (or the official preview download link provided by Josiah).
* **Install:** Open the downloaded `.dmg` file and drag **Antigravity** into your **Applications** folder.
* **First Launch:** Open Antigravity from Applications.
  *(If macOS displays a warning saying the app is from an unidentified developer: Open **Apple Menu  → System Settings → Privacy & Security**, scroll down, and click **Open Anyway**).*

---

### 2. Download Google Drive for Desktop (REQUIRED)
All agents standardize file paths and document storage using Google Drive's native macOS mount point for automatic cloud backups and note syncing.
* **Download Link:** [google.com/drive/download](https://www.google.com/drive/download/)
* **Install & Sign In:** Open the downloaded `.dmg`, run the installer, and sign in with your Google account.
* **Confirm:** Ensure Google Drive is running in your Mac's top menu bar.

---

### 3. Get 1 Year of Free Gemini Pro (Google AI Studio Student Plan)
Google provides students and developers with high-throughput API access to the Gemini Pro model for free.
* **Step A:** Go to [aistudio.google.com](https://aistudio.google.com) in your browser.
* **Step B:** Sign in with your university/student Google account (or standard Google account) to activate the **Student Plan** (1 year of free Gemini Pro access).
* **Step C:** Navigate to the API Key page: [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
* **Step D:** Click **Create API Key**, select or create a project, and copy the generated key string (starts with `AIza...`).
* **Step E:** Keep this key copied or saved in a note—you will paste it into Antigravity in Step 3!

---

### 4. GitHub Account Access
The multi-agent codebase is hosted securely on GitHub.
* If you don't already have a GitHub account, sign up for free at [github.com/signup](https://github.com/signup).
* Send your GitHub username to **Josiah** so he can grant your account access to the repository:
  `https://github.com/powelljosiah22/Agent-Update.git`

---

### 5. Install Python 3 via the 1-Click Mac Installer
To ensure your Mac has the modern Python engine needed for local morphological search and vector embeddings without using the command line:
* **Download Link:** [Python 3.11 for macOS (Official Installer)](https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg) *(or latest stable Python 3 from [python.org/downloads/macos](https://www.python.org/downloads/macos/))*.
* **Install:** Double-click the downloaded `.pkg` file and click **Continue**, **Agree**, and **Install** like any normal Mac application.

---

### 6. (Optional) Download Obsidian for Note-Taking
If you want to view, write, or visualize notes in your Second Brain:
* **Download Link:** [obsidian.md/download](https://obsidian.md/download)
* **Install:** Drag Obsidian to your Applications folder.

---

## 🚀 Step 2: Open Antigravity & Clone the Project (Via GUI)

Now that your apps are installed, open Antigravity and clone the repository without touching Terminal:

1. Open **Antigravity** from your Applications folder.
2. On the Antigravity Welcome tab, click the **Clone Git Repository...** button (or click the Source Control icon on the far left bar and click **Clone Repository**).
3. A text bar will appear at the top of Antigravity. Paste the repository URL:
   ```text
   https://github.com/powelljosiah22/Agent-Update.git
   ```
   and press `Return`.
4. A macOS Finder window will pop up asking where to save the folder. Select your **Home** folder (e.g., `Wyatt` or `Users/wyatt`) and click **Select Repository Destination**.
5. Once downloaded, a popup in the bottom-right corner will ask:
   > *"Would you like to open the cloned repository?"*
   Click **Open**.

---

## 🤖 Step 3: Hand the Reins to the AI Agent (One Chat Message!)

Antigravity will now be open with the `Agent-Update` repository loaded. You will now let Antigravity's autonomous agent configure everything for you.

1. Open the **Antigravity Chat Panel** on the right side of the screen (or press `Cmd + L`).
2. Copy the template below, replace the bracketed items with your information, and paste it into the chat:

```text
Hey! I'm setting up my agent system on this Mac. Please run the setup autonomously for me.

My Details:
- My Name: Wyatt
- Selected Module: Theology Agent & Biblical Philology DB (Option 2)
- Gemini API Key: [PASTE YOUR KEY HERE]
- Google Drive Email: [PASTE YOUR GOOGLE EMAIL HERE]

Please run the automated setup for my selected module, configure my .env file, sync MCP servers, and verify everything with healthcheck.py.
```

3. Press **Enter** to send the message!

### What the AI Agent Does Autonomously in the Background:
- ✅ Detects your Python 3 installation and builds an isolated virtual environment (`.venv`).
- ✅ Runs `./setup.sh --modules theology` to install the exact agent files to `~/Agents/`.
- ✅ Unpacks the complete 77MB offline biblical corpus database (`biblical_corpus.db`).
- ✅ Creates `~/Agents/Agent 0/.env` and securely writes your `GEMINI_API_KEY`.
- ✅ Syncs your API credentials into Antigravity's MCP configuration (`sync_env_to_mcp.py`).
- ✅ Runs the diagnostic health check (`healthcheck.py`) and reports a clean scorecard.

---

## 🎉 Step 4: The Final 2-Click Launch

When the agent finishes running the setup commands, it will send a message in chat letting you know everything is verified. Complete these two final clicks to switch into your new workspace:

1. In the top menu bar, click **File → Open Folder...** (or press `Cmd + O`).
2. Navigate to your Home folder, open **`Agents`**, select **`Agent 0`**, and click **Open**.
3. Press **`Cmd + Shift + P`**, type **`Developer: Reload Window`**, and press `Return`.

**Congratulations! Your multi-agent ecosystem is live.**

---

## 🏛️ How to Use Your Agents (Module Guide)

### For Wyatt: Theology Agent & Biblical Philology Engine
Your installation includes the complete, text-bound **Biblical Philology Engine** operating over the Hebrew Old Testament (WLC), Greek New Testament (SBLGNT), and Greek Septuagint (LXX Rahlfs 1935).

* **100% Offline & Free Exegesis:** The morphological database runs locally on your Mac. Querying Greek roots, syntax, Strong's glosses, and the Septuagint bridge incurs zero API token costs!
* **How to Talk to It in Chat:** In Antigravity's chat, simply ask:
  > *"Ask the Biblical Philologist to test Romans 3:24–26 and see how the Greek words for redemption (ἀπολύτρωσις) and propitiation (ἱλαστήριον) are used in the Septuagint."*
  > 
  > *"Test the doctrine of Christ's two wills in Gethsemane (Matt 26:39; Luke 22:42) and give me the single-screen scorecard."*
* **Saving Notes:** If you tell the agent *"Save this to inbox"*, it will format a clean Markdown study note and save it to your Google Drive (`Second Brain/1-Inbox/`).

---

### For Oliver: Academic Tutor & Problem Drills
Your installation includes the Socratic **Academic Tutor** connected to course materials.

* **Add Class Files:** In Google Drive, create a folder for your course: `My Drive/Class Folders/Fall_2026/<COURSE_CODE>/` and drop your syllabi, lecture slides, or practice PDFs into it.
* **How to Study in Chat:**
  > *"Drill me on TVM bond valuation using the Socratic method. Give me one problem at a time and don't give me the answer."*

---

### Future Updates (Also Zero-Terminal!)
When Josiah publishes updates, bug fixes, or new philological features, you don't need to touch Terminal either! Simply open Antigravity, go to chat, and say:

> *"Please update my agents from GitHub."*

The agent will run `./update.sh` in the background, pull the latest changes, preserve all of your personal notes, API keys, and settings, and re-run the healthcheck!

---

## 🧯 Quick Help & FAQ

* **Q: Antigravity says "App can't be opened because it is from an unidentified developer"?**
  * *Fix:* Open **System Settings  → Privacy & Security**, scroll down, and click **Open Anyway**.
* **Q: Do I need to keep Terminal open while using Antigravity?**
  * *No.* Terminal never needs to be opened. Antigravity manages all background tools, databases, and Python virtual environments autonomously.
* **Q: Can I install more modules later?**
  * *Yes!* Simply tell the agent in chat: *"Please install the Academic Tutor module as well"* and it will execute the modular installer for you.
