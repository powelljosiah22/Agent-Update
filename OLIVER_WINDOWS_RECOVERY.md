# 🪟 Oliver's Windows Antigravity Setup & Git Recovery Guide

A dedicated recovery manual and action plan to transition Oliver's Windows environment from its September 8 "halfway" state to a fully updated, self-healing multi-agent system linked to Git for future updates.

---

## ❓ 1. Do We Need to Link Him to Git for Updates?

**YES, absolutely.** Here is why:

1. **Why the September 8 Setup Stalled:**
   Without Git, Oliver's installation was an isolated, static snapshot. When bugs occurred (e.g., `<YourUsername>` placeholder in `mcp_config.json` or unbuilt Python venvs), there was no automated mechanism to deliver fixes or modern engine improvements.
2. **What Git Linking Unlocks:**
   By cloning `https://github.com/powelljosiah22/Agent-Update.git` to his PC:
   * **1-Command Updates:** Whenever you publish a bug fix, new academic skill, or engine upgrade, Oliver simply asks his agent: *"Update my agents from GitHub"* (or runs `.\update.ps1`).
   * **State Preservation:** The updater updates the engine and rules while **strictly protecting** his `.env` file, course notes, syllabi, and study memories.
   * **No Manual Copy-Pasting:** He never has to unzip packages or manually move files again.

---

## 🔍 2. Double-Check Audit: What Could We Be Missing?

Before Oliver runs the update, here is a double-check audit of potential Windows-specific failure points and how our new configuration prevents them:

| Potential Roadblock | Why It Fails on Windows | How We Fixed It |
| :--- | :--- | :--- |
| **PowerShell Execution Policy** | Windows blocks `.ps1` scripts by default with `running scripts is disabled on this system`. | All commands use `-ExecutionPolicy Bypass` so Windows security allows the script to run smoothly. |
| **JSON Backslash Escaping** | Windows paths like `C:\Users\Oliver\...` break JSON syntax unless escaped (`\\`) or formatted with forward slashes (`/`). | Our new `setup.ps1` formats all paths with forward slashes (`C:/Users/Oliver/...`), which both Windows and Python natively accept without syntax errors. |
| **Zombie Daemon / Port Conflict** | An old `daemon.py` process from 6 weeks ago might be lingering on port 8765 or 8085 (`WinError 10048`). | The setup routine kills any lingering Python daemon processes before binding port `8085`. |
| **Missing Node.js / NPX** | Oliver's old `mcp_config.json` tried to run `google-workspace` and `perplexity-ask` via `npx`, crashing if Node.js wasn't installed. | We pruned `mcp_config.json` down to the rock-solid, native Python `obsidian-search` server (zero Node.js required). |
| **Google Drive Mount Differences** | On Windows, Google Drive is a drive letter (`G:\My Drive\`) or `%USERPROFILE%\Google Drive\`. | The agent auto-detects if Google Drive exists; if not, it cleanly defaults to `%USERPROFILE%\Class_Folders` on his local drive so nothing breaks. |
| **Class Folders Empty** | Oliver only had `Sample_Course` created. | The new setup prompts him for his actual course codes (e.g. `FIN_3105`, `ACG_3131`) and builds the 3-subfolder structure automatically. |

---

## 🤖 3. The One-Prompt Kickoff for Oliver's Antigravity Agent

Oliver can open **Antigravity** on his Windows PC, open his `Agents\Agent 0` workspace, open the **Chat Panel** (`Ctrl + L`), and paste this exact prompt:

```text
Hey! I have an existing agent setup on Windows from about 6 weeks ago that stalled. Please autonomously heal, update, and link my setup to Git:

1. My Details:
   - Target Module: Academic Tutor (Option 1)
   - Repository URL: https://github.com/powelljosiah22/Agent-Update.git
   - Gemini API Key: [OLIVER: PASTE YOUR GEMINI API KEY HERE]
   - My Courses This Semester: [OLIVER: LIST YOUR COURSES, e.g., FIN_3105, ACG_3131, CS_101]

2. Autonomous Execution Steps:
   - Clone or pull the repository into $HOME\Agent-Update:
     if (!(Test-Path "$HOME\Agent-Update")) { git clone https://github.com/powelljosiah22/Agent-Update.git "$HOME\Agent-Update" } else { cd "$HOME\Agent-Update"; git pull origin main }
   - Execute the Windows setup script:
     powershell -ExecutionPolicy Bypass -File "$HOME\Agent-Update\setup.ps1" -modules academic
   - Update $HOME\Agents\Agent 0\.env with my Gemini API key.
   - In $HOME\Class_Folders\Fall_2026\, create folders for each of my courses with subdirectories: 1_Raw_Images, 2_Parsed_MD, 3_Archive.
   - Run healthcheck.py and confirm everything is green!
```

---

## 📋 4. Actionable Checklist to Wrap Everything Up

Here is the exact step-by-step checklist to close the loop with Oliver:

### For Josiah (1 Minute):
- [x] **Repository is Public:** The distribution repo is public, so Oliver can clone immediately without any GitHub invitation or login prompts!
- [ ] **Send Him the Prompt:** Copy the prompt from Section 3 above and text/email it to Oliver.

### For Oliver (3 Minutes):
- [ ] **Get Free Gemini API Key:** Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey), sign in with his Google account, click **Create API Key**, and copy it.
- [ ] **Paste Prompt in Antigravity:** Open Antigravity on Windows, paste the kickoff prompt into chat with his API key and course codes, and press Enter.
- [ ] **Final Reload:** Once the agent finishes, press **`Ctrl + Shift + P`** in Antigravity, type **`Developer: Reload Window`**, and press Enter.

---

## 🎯 5. How Oliver Uses His Modern Academic Tutor

Once verified:
1. **Drop Course Materials:** Oliver drops lecture slides, practice problems, or syllabus PDFs into `Class_Folders\Fall_2026\<Course>\1_Raw_Images\`.
2. **Auto-Parse:** The agent converts them into clean markdown cheat sheets in `2_Parsed_MD\`.
3. **Study Socratic Drills:** In Antigravity chat, Oliver says:
   > *"Academic Tutor: Drill me on Capital Budgeting and NPV using the Socratic method. Give me one problem at a time and do not give me the answer."*
4. **Future Updates:** Oliver simply types: *"Please update my agents from GitHub"* whenever you push new features.
