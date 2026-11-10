---
name: update-agents
description: Pulls the latest agent infrastructure, search daemon, parser, global rules, and shared skill updates from the upstream repository while 100% preserving all personal context, memory, learnings, and custom study workflows. Use whenever the user asks to "check for updates", "update my agents", "pull updates", or "add the theology agent / financial coach".
---

# Update Agents & Add Modules Skill (`update-agents`)

When the user asks to **"check for updates"**, **"update my agents"**, or **add an optional agent module** (such as the Theology Agent or Financial Coach):

## 1. Locate the Updater Directory
Check for the updater repository at `~/Agents/Agent 0/updater` (or `$env:USERPROFILE\Agents\Agent 0\updater` on Windows).
- If it does not exist yet, clone it automatically:
  - **macOS / Linux:**
    ```bash
    git clone https://github.com/powelljosiah22/Agent-Update.git "$HOME/Agents/Agent 0/updater"
    ```
  - **Windows (PowerShell):**
    ```powershell
    git clone https://github.com/powelljosiah22/Agent-Update.git "$env:USERPROFILE\Agents\Agent 0\updater"
    ```

## 2. Optional: Enabling Additional Agent Modules (e.g., Theology Agent)
If the user asks to add the **Theology Agent** (`theology`) or **Financial Coach** (`finance`):
- Append the module name (`theology` or `finance`) to `~/Agents/.agents_profile` (and `~/.agents_profile` on Windows) before running the updater script so the updater installs the workspace, subagents (`theology_philosophical_agent`, `biblical_philologist`), and unpacks `biblical_corpus.db`.

## 3. Run the State-Preserving Updater
Execute the non-destructive update script for the user's operating system:
- **macOS / Linux:**
  ```bash
  bash "$HOME/Agents/Agent 0/updater/update.sh"
  ```
- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Agents\Agent 0\updater\update.ps1"
  ```

## 4. Verify & Report
- Confirm that the update completed cleanly and report the new `VERSION.txt` release tag.
- Reassure the user that their personal `context.md`, `memory.md`, `learnings.md`, journals, and `.env` were 100% preserved.
