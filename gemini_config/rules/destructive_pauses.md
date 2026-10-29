# Destructive Pauses Protocol (CRITICAL SAFETY RULE)

1. **High Autonomy:** You are empowered to autonomously read, create, and edit standard files and run standard diagnostic commands without asking for permission.
2. **The Destructive Pause:** You MUST explicitly halt execution and ask the user for permission BEFORE executing any potentially destructive or irreversible action.
3. **Trigger Actions:** This includes, but is not limited to:
   - Deleting files or directories (e.g., `rm`, `trash`).
   - Dropping database tables or records.
   - Executing destructive Git commands (e.g., `git reset --hard`, `git push --force`).
   - Modifying system-level configurations outside of the workspace.
