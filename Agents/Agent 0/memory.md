# Agent 0 — Working Memory (Operational Dashboard)

## 🎯 Active Sprint Queue
- [ ] Complete initial onboarding & personalization with Callie (see `AGENT_SETUP_WIZARD.md`).
- [ ] Verify Google Workspace / Calendar / Gmail OAuth tokens (`~/Agents/Agent 0/credentials/`).
- [ ] Index initial Obsidian Second Brain notes and current semester Class Folders into ChromaDB.

---

## 🧭 Specialist Agent Dispatch Table
| Domain | Workspace Path | Subagent Name | Primary MCPs |
| :--- | :--- | :--- | :--- |
| **Executive / Master Node** | `~/Agents/Agent 0` | `self` | `google-workspace`, `email-sender-mcp`, `google-drive`, `obsidian-search` |
| **Academics & Coursework** | `~/Agents/Academic Tutor` | `academic_tutor` | `obsidian-search` (`target="classes"`), `perplexity-ask` |
| **Theology & Philosophy** | `~/Agents/Theology Agent` | `theology_philosophical_agent` | `obsidian-search` (`target="vault"`), `perplexity-ask` |
| **Wealth & Quant Finance** | `~/Agents/Financial_Coach` | `financial_coach` | `yfinance`, `robinhood`, `perplexity-ask` |
| **Deep Vault Synthesis** | `~/Agents/Agent 0` | `knowledge_librarian_v2` | `obsidian-search` (`deep_research_obsidian`) |

---

## ⚡ Fast Paths & Command Cache
- **Check Search Daemon Health:**
  `curl -s http://127.0.0.1:8085/health`
- **Restart All Daemons (Watchdog):**
  `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/voice_to_brain/watchdog_runner.py`
- **Full ChromaDB Re-Index (Vault + Class Folders):**
  `~/Agents/Agent 0/mcp/obsidian_search/venv/bin/python ~/Agents/Agent 0/mcp/obsidian_search/sync_database.py`
- **Run System Healthcheck:**
  `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/healthcheck.py`
- **Generate Google Drive OAuth Token:**
  `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/credentials/generate_token.py`

---

## 🔗 Neural Pathways (Cross-Domain Connections)
- **Academic Schedule → Executive Calendar:** Upcoming exam dates and project deadlines discovered in `~/Agents/Academic Tutor` must be synced to Google Calendar via `Agent 0`.
- **Voice Memos → Domain Agents:** Audio memos dropped into `00_Inbox/Voice_Notes` are automatically routed by `brain_daemon.py` into permanent notes (`02_Permanent_Notes`), theology syntheses (`03_Theology_Synthesis`), or `Academic Tutor/study_log.md`.
