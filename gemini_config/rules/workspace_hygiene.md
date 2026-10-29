# Workspace Hygiene Protocol (CLEANLINESS)

To prevent filesystem clutter and maintain version control, all agents must strictly adhere to the following file organization rules:

1. **Temporary Files:** ALL temporary scripts, one-off data pulls, and scratch code MUST be written to the system's `<Artifact Directory>/scratch/` folder.
2. **No Root Clutter:** Never dump files directly onto the Desktop, `~/Documents`, or the root `~/Agents` directory unless explicitly instructed by the user.
3. **Autonomous Git Commits:** Immediately after completing a significant task, modifying a codebase, or verifying that new code works, you must autonomously commit the changes to Git (`git add . && git commit -m "Summary"`). Do not wait for the user to tell you to commit working code.
