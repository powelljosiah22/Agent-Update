---
name: update-agents
description: Pulls the latest agent infrastructure, search daemon, parser, global rules, and shared skill updates from Josiah's upstream repository while 100% preserving all personal context, memory, learnings, and custom study workflows. Use whenever the user asks to "update my agents", "pull updates from Josiah", or "sync agent updates".
---

# Update Agents Skill (`update-agents`)

When the user asks to update their agents or pull the latest updates:

1. **Locate the Updater Directory:**
   Check for the updater repository at `~/Agents/Agent 0/updater`.
   - If `~/Agents/Agent 0/updater` does not exist yet, clone it automatically:
     ```bash
     git clone https://github.com/powelljosiah22/Agent-Update.git "$HOME/Agents/Agent 0/updater"
     ```

2. **Run the State-Preserving Updater (`update.sh`):**
   Execute the non-destructive update script via `run_command`:
   ```bash
   bash "$HOME/Agents/Agent 0/updater/update.sh"
   ```

3. **Verify & Report:**
   - Confirm that the healthcheck at the end of `update.sh` passed (`ChromaDB Search Daemon is ONLINE (port 8085)`).
   - Reassure the user that their personal `context.md`, `memory.md`, `learnings.md`, `skills.md`, journals, and `.env` were backed up to `~/Agents/.backups/` and left 100% untouched.
