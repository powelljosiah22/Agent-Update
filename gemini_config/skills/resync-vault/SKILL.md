---
name: resync-vault
description: Re-indexes the entire Obsidian Second Brain vault and Class Folders into ChromaDB vector memory and updates vector semantic connections for all permanent notes.
---

# Vault Vector Resync Skill

When the user asks to resync their vault, update note connections, or run `/resync-vault`, execute the following workflow:

## Workflow Steps
1. Run the local Python vector sync and semantic relinking scripts using `run_command`:
   ```bash
   "$HOME/Agents/Agent 0/mcp/obsidian_search/venv/bin/python" "$HOME/Agents/Agent 0/mcp/obsidian_search/sync_database.py" && "$HOME/Agents/Agent 0/mcp/obsidian_search/venv/bin/python" "$HOME/Agents/Agent 0/voice_to_brain/relink_all_notes.py"
   ```
2. Report the summary of newly indexed chunks, updated notes, and generated vector semantic connections back to the user.
