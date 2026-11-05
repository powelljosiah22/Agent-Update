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
3. Wait for explicit confirmation (`"Send it"` / `"Approved"`).
4. Call `email-sender-mcp` -> `send_email`.

---

## 3. Vault Resync & Semantic Relinking Workflow
When adding a batch of new syllabus PDFs, slide decks, or Obsidian notes:
1. Run `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/voice_to_brain/pipeline_parser.py` to convert raw documents in `1_*` folders into `2_Parsed_Markdown/`.
2. Run `~/Agents/Agent 0/mcp/obsidian_search/venv/bin/python ~/Agents/Agent 0/mcp/obsidian_search/sync_database.py` to index all incremental changes into ChromaDB.
3. Run `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/voice_to_brain/relink_all_notes.py` to update `## 🔗 Vector Semantic Connections` across all permanent notes.

---

## 4. Inline 5-File Subagent Self-Learning & Compaction Auditor
**Subagent Types:** All domain subagents (`academic_tutor`, `theology_philosophical_agent`, `biblical_philologist`, `financial_coach`, `knowledge_librarian_v2`) + `memory_manager`
**Trigger:** Inline at the end of every substantive turn (for domain subagents); on-demand/periodic for `memory_manager`.
**Description:** Eliminates split-brain memory and per-turn background subagent overhead. Every domain subagent reads and writes directly to its canonical 5-file workspace (`~/Agents/<Domain>/{memory,learnings,skills,context}.md`) at the end of its turn, enforcing `memory.md <= 150 lines` and `context.md <= 100 lines` via 1-In/1-Out pruning.
**Instructions for Agent 0 (Subagent Querying & Dispatch Standard):**
1. **Step 0 Fact Verification:** Verify primary source facts (actual statutory text, syllabus, SEC filing, official records) BEFORE drafting subagent prompts. Never query on unverified assumptions.
2. **The Anti-Leading & Anti-Prooftexting Firewall:** NEVER embed desired conclusions, political views, or biased framings into subagent prompts. Formulate open, two-sided questions requiring evidence cutting both ways.
3. **Epistemic Isolation of `biblical_philologist`:** Pass ONLY neutral concepts, passages, or propositions to test. Never leak personal context (`context.md`), political preferences, or systematic denominational frameworks. Enforce Tiered Delivery (Card / Claim Test / Chapter Map).
4. **Neutral Dispatch to `theology_philosophical_agent`:** Provide verified facts and philological findings, but NEVER pass Agent 0's pre-determined recommendation. Classify issues by Category (Moral Command vs. Prudential Judgment vs. Adiaphora), and demand steelmanned counter-arguments and a self-interest/stakeholder audit.
5. **Pre-Dispatch Scope Injection:** When invoking any subagent, pass the core question plus a 2–3 bullet target scope so the subagent stays focused.
6. **Filter-Without-Flattening Synthesis:** When receiving outputs, condense conversational filler/preambles while **minimally editing and preserving 100% of the substantive technical depth** (formulas, tables, keystrokes, code, citations, Socratic arguments). On prudential decisions, assign an explicit confidence rating.
7. **On-Demand Compaction (`memory_manager`):** Invoke `memory_manager` only when requesting a cross-workspace 5-file compaction, promotion (`use_count >= 3`), archival (`>60 days`), or neural pathway sweep.

---

## 5. The Universal 4-Tier Retrieval & Routing Standard

### The 4-Tier Retrieval Standard:
1. **Tier 1 (Instant In-Memory Hybrid Search — ~140ms):**
   - Tool: `call_mcp_tool(ServerName="obsidian-search", ToolName="semantic_search_obsidian", Arguments={"query": "...", "target": "classes"|"vault", "course": "<COURSE_CODE>", "n_results": 3})`
   - Primary default for all single questions, formula lookups, syllabus policies, and fast neighbor discovery.
2. **Tier 2 (Targeted File Grep — ~15ms):**
   - Tool: `grep_search` strictly anchored to specific target folders:
     - Class materials: `~/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Class Folders/Fall_2026/<COURSE>/2_Parsed_MD/`
     - Second Brain notes: `~/Library/CloudStorage/GoogleDrive-user@example.com/My Drive/Second Brain/2-Permanent-Notes/`
   - Trigger: Use ONLY if Tier 1 misses an exact numbered question, table, or note title.
   - **STRICT PROHIBITION:** NEVER run `find_by_name` or `grep_search` on `$HOME`, `~`, or system roots.
3. **Tier 3 (Deep Vault Synthesis — ~2.5s via Flash-Lite Cascade):**
   - Tool: `call_mcp_tool(ServerName="obsidian-search", ToolName="deep_research_obsidian", Arguments={"query": "...", "target": "all"|"vault"})`
   - Engine: Powered by an ultra-low-latency model cascade (`gemini-3.5-flash-lite` [0.55s] → `gemini-flash-lite-latest` [0.76s] → `gemini-3.5-flash`) with strict 5s (subq) and 12s (synth) failovers and zero-crash graceful degradation (returns aggregated context directly if remote LLMs fail).
   - Trigger: Complex multi-note reasoning, cross-course schedule/syllabus conflict audits, and multi-document synthesis.
4. **Tier 4 (External Web Search — ~1–2s):**
   - Tool: `search_web(...)`
   - Trigger: Real-time internet data, current events, or when local files are confirmed absent.

### Intent-Based Subagent Routing Table:
- *Coursework / Exam Prep / Homework Drills* → `academic_tutor`
- *Theology / Apologetics / Pastoral Dialogue* → `theology_philosophical_agent`
- *Quantitative Portfolio / Factor Investing / Personal Finance* → `financial_coach`
- *Vault Ingestion & Processing* → `knowledge_librarian_v2`
- *On-Demand 5-File Compaction & Cross-Pollination Audit* → `memory_manager`

---

## 6. Continuous Workflow Optimization Protocol
**Description:** System protocol for caching optimal execution paths to eliminate search loops.
**Instructions:**
1. **Cache on Success:** If you spend 3 or more steps exploring a directory, finding an environment, debugging a tool, or fixing an MCP server, you MUST record the final, successful 1-step command/path in the `## ⚡ Fast Paths & Command Cache` section of `memory.md`.
2. **Fast-Path First:** Before running exploratory commands like `find`, `grep`, or guessing python environments, you must check `memory.md` to see if the optimal path or launch command is already cached.
3. **Parameter Evolution:** If you optimize a tool call (e.g. discovering that `n_results=5` works better for search), document the parameter preference in this skills document.

---

## 7. Infrastructure Modification Protocol (The "Examine 1 time completely over" Rule)
**Trigger Command:** Modifying architecture, updating MCP schemas, or applying codebase infrastructure changes.
**Description:** A mandatory Final Audit safety procedure designed to prevent "illusionary" features and silent bottlenecks caused by partial implementations.
**Instructions:**
1. **Develop & Implement:** Write the new code, schemas, or architectural updates.
2. **The Final Audit:** Before reporting back to the user, you MUST execute a holistic "Examine 1 time completely over" step.
3. **Consistency Check:** Review the newly written code/schemas to ensure full consistency across all related modules, environments, and sub-systems.
4. **Report Discovery:** Report any hidden bottlenecks or missing pieces caught during the Final Audit directly to the user when you summarize the implementation.

---

## 8. Biblical Philology 4-Step Evidence Pipeline (Promoted from L-032)
**Subagent / Workspace:** `biblical_philologist` / `~/Agents/Theology Agent/philology_db`
**Description:** Stateless, zero-discovery-call Greek/Hebrew philological pipeline with programmatic anti-bias guardrails.
**Instructions:**
1. **Step 1 (Multi-Facet Vector + Anti-Lexical Fallacy Attestation):** Run `philology_engine.py vector "<CONCEPT>" --n 8` first (supports multi-facet queries separated by `;`). Uses `core_gloss()` (stripping misaligned BDB entries), `gloss_attestation()` (with stem/cognate attestation and Lexicalization Fallacy guard), and prints the Cross-Testament Cluster Guide.
2. **Step 2 (Balanced Cluster Genre Dispersion):** Run `philology_engine.py sql --mode dispersion --lemma "H...,G..."` across the bilingual cluster. **Anti-Bias Constraint:** Must balance terms across major canonical divisions (Torah agrarian dues, Gospel charity/renunciation, Pauline partnership) to avoid false canonical silence. Reports distinct-verse counts, length-normalized rates per 10k words, and Silent Genres (`0 hits`).
3. **Step 3 (Single-Batch Interlinear & MT Versification):** Finalize all target verses from Step 2 before calling `--mode interlinear`. Batch all passages into a single `--ref "Ref1; Ref2; Ref3"` call (`~120ms`). Observe English versification notes in headers (e.g. `Eccl 5:18 [English: Eccl 5:19]`).
4. **Step 4 (Mechanical Claim Verification):** Run `philology_engine.py sql --mode verify --claims "Ref=lemma; ..."` to mechanically verify every cited verse-lemma pair before outputting Format B Scorecard. English-shifted verses are automatically cross-checked against MT.
