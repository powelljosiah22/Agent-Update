# Continuous Workflow Optimization Protocol

Agents must systematically eliminate repetitive exploratory work. You are required to aggressively cache solutions to workflow bottlenecks.

1. **Cache on Success (The 3-Step Rule):** If you spend 3 or more steps exploring a directory, finding an environment, debugging a tool, or fixing an MCP server, you MUST autonomously record the final, successful 1-step command, script, or path in the `## ⚡ Fast Paths & Command Cache` section of the workspace's `memory.md`.
2. **Fast-Path First:** Before running exploratory commands like `find`, `grep`, or `which python`, you must consult `memory.md` to see if the optimal path, python binary, or launch command is already cached.
3. **Parameter Evolution:** If you discover a better way to use an existing tool (e.g., increasing `n_results` on semantic search, passing specific flags to a build script), you must document the optimal parameters in `skills.md`.

4. **Active Workflow Broadcasting:** If you solve a tool call issue, discover a faster execution path, or optimize a workflow, you must actively pause and ask: *"Which other agents rely on this tool or workflow?"* You MUST proactively use your file-editing tools to push that solution directly into the `memory.md` or `skills.md` of the other relevant agents. Do not silo workflow solutions in your own workspace.
