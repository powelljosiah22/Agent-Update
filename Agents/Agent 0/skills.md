# Agent 0 — Procedural Memory (`skills.md`)

## 1. Second Brain Hybrid Retrieval Standard (`obsidian-search`)
Always query the local ChromaDB daemon (`127.0.0.1:8085`) via the `obsidian-search` MCP tool (`semantic_search_obsidian`) before falling back to filesystem searches:
- **Personal Vault Search:**
  ```json
  {
    "query": "<topic or keyword>",
    "target": "vault",
    "n_results": 4,
    "lexical_weight": 1.5
  }
  ```
- **Class Folder Search:**
  ```json
  {
    "query": "<course topic or problem>",
    "target": "classes",
    "course": "<COURSE_CODE>",
    "n_results": 4,
    "lexical_weight": 1.5
  }
  ```
- **Deep Multi-Subquery Synthesis:** Use `deep_research_obsidian` when synthesizing across 5+ notes or preparing a comprehensive briefing.

---

## 2. Executive Email Drafting & Dispatch Protocol
1. Gather context from `context.md` and `obsidian-search` if relevant.
2. Present the complete email preview in chat (`To`, `Subject`, `Body`).
3. Wait for explicit confirmation from Callie (`"Send it"` / `"Approved"`).
4. Call `email-sender-mcp` -> `send_email`.

---

## 3. Vault Resync & Semantic Relinking Workflow
When Callie adds a batch of new syllabus PDFs, slide decks, or Obsidian notes:
1. Run `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/voice_to_brain/pipeline_parser.py` to convert raw documents in `1_*` folders into `2_Parsed_Markdown/`.
2. Run `~/Agents/Agent 0/mcp/obsidian_search/venv/bin/python ~/Agents/Agent 0/mcp/obsidian_search/sync_database.py` to index all incremental changes into ChromaDB.
3. Run `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/voice_to_brain/relink_all_notes.py` to update `## 🔗 Vector Semantic Connections` across all permanent notes.
