# Agent 0 — Episodic Memory (`learnings.md`)

```yaml
## Active Learnings

- id: L-001
  summary: "ChromaDB HTTP daemon on 127.0.0.1:8085 eliminates cold-start embedding latency"
  category: tool_optimization
  created: 2026-10-15
  last_used: 2026-10-15
  use_count: 1
  status: active
  promoted_to: ""
  detail: |
    Running ChromaDB and the ONNX embedding model inside a persistent HTTP daemon (daemon.py on port 8085)
    keeps semantic_search_obsidian latency under 50ms. If port 8085 is unreachable, server.py automatically
    spawns daemon.py in the background.

- id: L-002
  summary: "macOS TCC permissions block cron jobs from reading ~/Documents or ~/Desktop unless Full Disk Access is granted"
  category: error_fix
  created: 2026-10-15
  last_used: 2026-10-15
  use_count: 1
  status: active
  promoted_to: ""
  detail: |
    Background cron tasks (such as watchdog_runner.py) reside in ~/Agents/Agent 0/ to avoid macOS TCC
    prompts on ~/Documents. If Google Drive paths require TCC access, grant Full Disk Access to
    /usr/sbin/cron and python3 in macOS System Settings -> Privacy & Security.
```

## Archived Learnings
