# 🤖 AGENT_SETUP_WIZARD.md — Autonomous Onboarding & Zero-Terminal Setup Protocol

**Target Audience:** Any Antigravity Agent running inside this repository (`Agent-Update`).
When a user (Callie, Wyatt, Oliver, or anyone new) opens this folder in Antigravity and asks you to set up, install, or personalize their agents, follow this **Zero-Terminal Autonomous Setup Protocol**:

---

## ⚡ 0. The One-Prompt Zero-Terminal Execution Sequence

When the user pastes the **Kickoff Prompt** in chat with their details (Name, Module selection, `GEMINI_API_KEY`, Google Drive email):

### Step 1: Execute the Modular Setup Script
Run the installer via `run_command` in the workspace directory using their requested module flag:
```bash
# If they chose Theology:
./setup.sh --modules theology

# If they chose Academic:
./setup.sh --modules academic

# If they chose Finance:
./setup.sh --modules finance

# If they chose All Agents:
./setup.sh --all
```
*(If the user did not specify, ask them which module they want: [1] Academic, [2] Theology, [3] Finance, or [4] All).*

### Step 2: Configure Their `.env` File
Immediately write their provided credentials into `~/Agents/Agent 0/.env`:
- Set `GEMINI_API_KEY=<User's Key>`
- Set `USER_EMAIL=<User's Google Email>`
- Ensure all other placeholders remain intact.

### Step 3: Sync MCP Config
Run the environment synchronizer so Antigravity's MCP server config reflects their keys:
```bash
python3 ~/Agents/Agent\ 0/sync_env_to_mcp.py
```

### Step 4: Run System Healthcheck
Execute the diagnostic script to verify everything is operational:
```bash
python3 ~/Agents/Agent\ 0/healthcheck.py
```

### Step 5: Deliver Completion Instructions
Reply in chat with a clear, celebratory summary:
1. Confirm that their selected module is 100% installed and healthy.
2. Instruct them to perform the final 2-click GUI action:
   > *"Everything has been installed and configured autonomously! To start using your agents:*
   > *1. Go to **File → Open Folder...** in the top menu and select `~/Agents/Agent 0`.*
   > *2. Press **`Cmd + Shift + P`**, type **`Developer: Reload Window`**, and press `Return`.*
   > *You are now ready to chat with Agent 0 and your specialized subagents!"*

---

## ⚠️ 1. Know Your Agent Boundaries (Sandbox, TCC, OAuth, IDE Reloads)

To avoid errors or wasted steps, strictly respect the boundary between what you can execute autonomously via `run_command` / file tools vs. what requires Callie's action:

1. **Filesystem Sandbox (`~/.gemini` & `~/Agents`):**
   - If Callie has NOT run `./setup.sh` yet and asks you to run it from inside Antigravity, note that `setup.sh` writes to `~/.gemini/config/` and `~/Agents/` and starts background daemons.
   - If your `run_command` tool is sandboxed to the current workspace, either request sandbox bypass permission (`BypassSandbox` if available) OR instruct Callie to run `./setup.sh` directly in her macOS Terminal.
2. **Background Daemons (`daemon.py` on port 8085 & `brain_daemon.py`):**
   - Child processes spawned inside a non-daemon `run_command` call may be terminated by Antigravity when the command step exits.
   - Always use `~/Agents/Agent 0/voice_to_brain/watchdog_runner.py` (which uses `start_new_session=True`) or let the 15-minute cron job maintain the daemons.
3. **API Keys & Syncing (`~/Agents/Agent 0/.env` → `~/.gemini/config/mcp_config.json`):**
   - If Callie shares her `GEMINI_API_KEY`, `USER_EMAIL`, `GMAIL_APP_PASSWORD`, or `PERPLEXITY_API_KEY` in chat, write them into `~/Agents/Agent 0/.env` and immediately run:
     ```bash
     python3 ~/Agents/Agent\ 0/sync_env_to_mcp.py
     ```
   - Never leave `mcp_config.json` out of sync with `.env`.
4. **Interactive OAuth Popups (`generate_token.py` & `auth_flow.py`):**
   - Never run `generate_token.py` or `auth_flow.py` silently in the background expecting it to finish without user interaction—tell Callie first that a browser window or 2FA prompt will appear for her to approve.
5. **IDE Window Reload Requirement:**
   - Anytime you update `~/.gemini/config/mcp_config.json`, tell Callie to press **`Cmd + Shift + P` → `Developer: Reload Window`** so Antigravity restarts the MCP servers with the new keys.

---

## 🩺 2. Phase 1: Automated System Health Verification

Run the healthcheck script first:
```bash
~/Agents/Agent\ 0/.venv/bin/python ~/Agents/Agent\ 0/healthcheck.py
```

### How to Remediate Any Warnings/Failures:
- **If `ChromaDB Search Daemon` is offline on port 8085:**
  Run `~/Agents/Agent\ 0/.venv/bin/python ~/Agents/Agent\ 0/voice_to_brain/watchdog_runner.py` and re-verify `curl -s http://127.0.0.1:8085/health`.
- **If API keys in `.env` are still placeholders (`YOUR_GEMINI_API_KEY`, etc.):**
  Ask Callie if she would like to paste her keys in chat (so you can update `.env` and run `sync_env_to_mcp.py` for her) or edit `~/Agents/Agent 0/.env` directly.

---

## 🎯 3. Phase 2: Interactive Personalization Interview (All 4 Workspaces)

Once the technical healthcheck passes, conduct a brief, warm, structured onboarding interview with Callie (using `ask_question` or concise conversational questions) to populate her 4 workspaces:

### Question Block A — Executive & Schedule Context (`~/Agents/Agent 0/`)
1. What are your top 2–3 priorities or goals for this season/semester?
2. What time do you like to start your day, and what would be most helpful in a Morning Briefing?
- **Action:** Update `~/Agents/Agent 0/context.md` and `~/Agents/Agent 0/memory.md`.

### Question Block B — Academic Courses (`~/Agents/Academic Tutor/`)
1. What classes are you taking this semester (course codes & titles)?
2. How do you learn best when studying for exams or working through tough problem sets?
- **Action:**
  - Create the 5-subfolder structure (`1_Syllabus_and_Schedule`, `1_Lectures_and_Slides`, `1_Homework_and_Problems`, `1_Exams_and_Reviews`, `2_Parsed_Markdown`) inside `CLASS_FOLDERS_PATH/<COURSE_CODE>/` for each of her actual courses!
  - Update `~/Agents/Academic Tutor/memory.md` and `~/Agents/Academic Tutor/context.md` with her active courses.

### Question Block C — Theology & Personal Formation (`~/Agents/Theology Agent/`)
1. Are there any books of the Bible, theological topics, or authors you are currently reading or wrestling with?
- **Action:** Update `~/Agents/Theology Agent/context.md` and `~/Agents/Theology Agent/memory.md`.

### Question Block D — Financial Goals (`~/Agents/Financial_Coach/`)
1. What are your primary financial goals right now (e.g., building an emergency fund, budgeting cash flow, Roth IRA / ETF investing, or learning quantitative investing)?
- **Action:** Update `~/Agents/Financial_Coach/context.md` and `~/Agents/Financial_Coach/memory.md`.

---

## ✅ 4. Phase 3: Initial Vault Indexing & Completion Confirmation

After creating Callie's course folders and updating her `context.md` and `memory.md` files:
1. Run `~/Agents/Agent 0/mcp/obsidian_search/venv/bin/python ~/Agents/Agent 0/mcp/obsidian_search/sync_database.py` to index her new folders into ChromaDB.
2. Test `obsidian-search` -> `semantic_search_obsidian` (`query="Welcome to Your Second Brain"`, `target="vault"`, `n_results=2`, `lexical_weight=1.5`) to prove live end-to-end vector retrieval.
3. Provide a clean summary table showing all 4 configured workspaces and remind Callie how to drop syllabi, slides, and voice memos into her Second Brain!
