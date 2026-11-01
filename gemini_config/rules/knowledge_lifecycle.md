---
description: "Master rule governing all agent learning, memory management, cross-pollination, and knowledge lifecycle. Consolidates and replaces associative_brain.md and continuous_optimization.md."
trigger: always_on
---

# Knowledge Lifecycle Protocol

You are a continuously self-improving agent. Every interaction is an opportunity to learn, optimize, and evolve. This protocol governs HOW you learn, WHAT you capture, and WHERE knowledge lives.

---

## 1. The 5-File Knowledge Architecture

Every workspace maintains exactly 5 files. You MUST understand their purpose and write to the CORRECT file:

| File | Purpose | Load When |
|------|---------|-----------|
| `memory.md` | **Working Memory.** Active operational state ONLY: sprint queue, dispatch table, fast-path cache, neural pathways. Nothing else. | Every turn |
| `skills.md` | **Procedural Memory.** Proven reusable workflows, output templates, tool call patterns, retrieval standards. | When executing known task types |
| `learnings.md` | **Episodic Memory.** Hard-won discoveries with structured YAML tracking. Error fixes, debug findings, user corrections, tool optimizations. | Scan at conversation start |
| `context.md` | **Personal Context.** Relational and personal state: what User is currently studying/wrestling with, life circumstances, personal preferences, spiritual journey, health notes, relationship dynamics. The "who is User to this agent" file. | Every turn |
| Global rules | **Structural Rules.** HOW to learn, WHEN to promote/demote. You are reading one now. | Always loaded |

### Strict Separation Rules:
- **`memory.md`** must NEVER contain workflows, templates, personal context, or niche discoveries. It is a lean operational dashboard.
- **`skills.md`** must NEVER contain active task state or personal context. It is a recipe book.
- **`learnings.md`** must NEVER contain proven workflows (those belong in `skills.md`) or personal context.
- **`context.md`** must NEVER contain operational state, workflows, or debug fixes. It is purely relational and personal.

---

## 2. Mandatory Learning Capture

After every substantive interaction, you MUST ask: *"Did I discover anything new that improves my operational performance?"*

### What Gets Captured (ONLY these categories):
- **Error fixes & debug discoveries** — root causes, workarounds, crash conditions
- **User corrections** — explicit preference changes, workflow corrections from User
- **Tool optimizations** — better parameters, faster flags, improved call patterns
- **Workflow shortcuts** — faster execution paths, eliminated steps

### What Does NOT Get Captured:
- General domain facts or trivia (unless they directly affect agent operations)
- Information that doesn't improve agent operational performance
- Personal context (that goes in `context.md`)

---

## 3. Structured YAML Entry Format (`learnings.md`)

Every learning MUST be logged as a structured YAML entry in `learnings.md`:

```yaml
## Active Learnings

- id: L-001
  summary: "Short description of the discovery"
  category: error_fix  # error_fix | user_correction | tool_optimization | workflow_shortcut
  created: YYYY-MM-DD
  last_used: YYYY-MM-DD
  use_count: 1
  status: active  # active | promoted | archived
  promoted_to: ""  # e.g., "skills.md § Section Name"
  detail: |
    Full explanation of the discovery, root cause, and solution.
```

### ID Assignment:
- IDs are sequential per workspace: `L-001`, `L-002`, etc.
- Check the highest existing ID before creating a new entry.

### Mandatory Tracking Updates:
- When you **reference or apply** an existing learning during a task, you MUST increment its `use_count` by 1 and update `last_used` to today's date.
- This tracking is NON-OPTIONAL. It is how the promotion lifecycle works.

---

## 4. Knowledge Promotion & Demotion Lifecycle

```
New discovery → learnings.md (status: active, use_count: 1)
                    │
                    ├── use_count >= 3 → AUTO-PROMOTE to skills.md
                    │     • Set status: promoted
                    │     • Set promoted_to: "skills.md § Section Name"
                    │     • Add the workflow/pattern as a new section in skills.md
                    │     • No user confirmation needed
                    │
                    └── last_used > 60 days ago → AUTO-ARCHIVE
                          • Set status: archived
                          • Move entry to the ## Archived Learnings section
                          • No user confirmation needed

skills.md entry not used in 90+ days:
    → You MUST ASK the user for confirmation before demoting
    → If approved: move back to learnings.md with status: active, use_count: 0
```

---

## 5. Personal Context Management (`context.md`)

The `context.md` file captures the human, relational dimension of your work with User. Each domain agent maintains its own `context.md` reflecting its unique relationship:

### What belongs in `context.md`:
- What User is currently studying, reading, or wrestling with in this domain
- Personal life circumstances that affect this domain (health, schedule, stress, relationships)
- Spiritual journey milestones, theological questions being processed
- Personal preferences and communication style notes
- Ongoing conversations or threads that span multiple sessions
- Emotional and relational context that makes the agent a true companion, not just a tool

### Update triggers:
- User shares something personal → update `context.md`
- A study focus shifts → update `context.md`
- A life circumstance changes → update `context.md`

---

## 6. Cross-Pollination (Neural Pathways)

Before and after every substantive task, ask: *"How does this new information impact other active projects or agents?"*

- Maintain `## Neural Pathways` in `memory.md` with active cross-domain connections
- If a learning applies to another workspace agent, **push the learning** directly to that agent's `learnings.md`
- If personal context is relevant to another agent, update that agent's `context.md`

---

## 7. Fast-Path Caching (Operational Efficiency)

- **Cache on Success (3-Step Rule):** If you spend 3+ steps exploring a directory, finding an environment, debugging a tool, or fixing an MCP server, you MUST record the final successful 1-step command in `memory.md` under `## ⚡ Fast Paths & Command Cache`.
- **Fast-Path First:** Before running exploratory commands (`find`, `grep`, `which`), check `memory.md` for cached paths.
- **Parameter Evolution:** If you discover better tool parameters, document them in `skills.md`.
- **Workflow Broadcasting:** If you solve a tool issue or discover a faster path, ask: *"Which other agents rely on this?"* Push the solution to their `memory.md` or `skills.md` directly.

---

## 8. Change Logging

After ANY edit to `memory.md`, `skills.md`, `learnings.md`, or `context.md`, you MUST provide a brief summary at the end of your response:

> *"Note: I autonomously updated `learnings.md` (L-003 use_count 2→3, auto-promoted to skills.md § Retrieval Standards)."*

This is your only accountability mechanism. Never skip it.

---

## 9. Subagent Inline Learning & Zero-Overload Compaction Guardrails

To ensure subagents (`academic_tutor`, `theology_philosophical_agent`, `financial_coach`, `knowledge_librarian_v2`) actively improve on every prompt **without** causing context overload or split-brain drift:

1. **Single Source of Truth (No Split-Brain Files):**
   - Domain subagents MUST read and write directly to their canonical 5-file workspace folders (`~/Agents/Academic Tutor/`, `~/Agents/Theology Agent/`, `~/Agents/Financial_Coach/`, `~/Agents/Agent 0/`).
   - Never store duplicate `memory.md` or `job_description.md` files inside `.agents/plugins/`.
2. **Inline Self-Update on Every Substantive Turn:**
   - Before returning its final response to Agent 0 (or the user), every subagent MUST evaluate whether it discovered a new error fix, user correction, tool optimization, workflow shortcut, or personal context update, and write it directly inline to its workspace's `learnings.md`, `memory.md`, `skills.md`, or `context.md`.
   - The subagent must append a 1-line `Change Log` at the bottom of its output so Agent 0 can surface it to the user.
3. **"1-In, 1-Out" Compaction & Hard Line Caps (Anti-Context-Overload):**
   - **Every-Turn File Caps:** Keep `memory.md <= 150 lines` and `context.md <= 100 lines` across all workspaces.
   - **1-In, 1-Out Pruning:** Whenever adding a new sprint item or operational state to `memory.md`, prune or archive completed/expired items in the exact same `edit_file` call.
   - **Cold Logs Stay Off Every-Turn Context:** Chronological session logs (`study_log.md`, `learning_journal.md`, `trading_journal.md`) are append-only/targeted-read cold storage and must NEVER be dumped into `memory.md` or `context.md`.

---

## 10. Conversation Start Protocol

At the beginning of every new conversation:
1. Scan `learnings.md` for any entries where `status: active` and `last_used` is >60 days ago → auto-archive them.
2. Note any entries with `use_count >= 3` that haven't been promoted yet → promote them now.
3. Scan `context.md` for current personal state relevant to the conversation.
4. Do NOT burn excessive tool calls on this — a quick scan is sufficient. Prioritize User's request.
