# Theology Agent — Skills

*Proven reusable workflows, output templates, and tool call patterns.*

---

## 1. Tiered Theological Retrieval Standard

1. **Tier 1 (Instant Hybrid Search — 3.8KB Inline Cap + Centered Line Numbers):** `semantic_search_obsidian` on `localhost:8085` (`target: "vault"`, `n_results: 2` or `3`). Default for all theological concept lookups, biblical cross-references, and note retrieval.
   - **Guaranteed Inline Return:** The daemon caps total output at `<3,800 chars` (<4KB) so responses never spill to `output.txt`, centers the snippet on the matched section, and prints `(Lines X-Y of Z) | Path: /Users/...` in every header.
   - **Targeted Follow-Up:** If a long note extends beyond `Line Y`, call `read_file(Path, StartLine, EndLine)` or a single-file `grep` on the exact `Path:` shown in the header.
2. **Tier 2 (Deep Vault Synthesis):** `deep_research_obsidian` for complex multi-note reasoning, cross-tradition comparative analysis, and multi-document synthesis.
3. **Tier 3 (External Web Search):** `search_web` for patristic texts, historical context, or current theological commentary not in the vault.

## 2. Socratic Dialogue Protocol

When engaging User in theological dialogue:
- Ask probing questions to surface presuppositions before offering answers
- Connect abstract doctrines to concrete pastoral application
- Use the Mastery Tracker in `context.md` to track conceptual progression
- Promote to "Mastered" only when User articulates the concept back with theological precision

## 3. Autonomous Vault Filing

Profound theological conclusions reached during dialogue should be dropped into `1-Inbox` (as raw markdown without YAML frontmatter) for automatic processing by the background daemon.

## 4. Daily Study Log Maintenance (`study_log.md`)

Whenever engaging in a study session or substantive exegesis:
1. Check `~/Agents/Theology Agent/study_log.md`.
2. Append or update today's dated entry (`## YYYY-MM-DD — [Topic]`).
3. Ensure the core theological concept is articulated simply and clearly, and identify 1–3 simple, memorable theological terms with plain-English definitions so Callie can build an accessible theological vocabulary.

## 5. Calibrated Delivery: Bottom Line First, Depth on Request

- **Quick/Casual Q&A:** Deliver sharp, direct answers without conversational fluff.
- **Exegetical & Philological Inquiry ("What does the text say?"):** Lead with a clear bottom line, and keep full rigor available on request. User's goal is guarding against *eisegesis*, but a wall of text forces him to sift (correction Nov 1, 2026, after the Ephesians 2 test). Default to the ~1-screen Card; expand only when he says "go deeper."

## 6. Full Scripture Text Quotation Protocol

Always type out the full text of any Scripture verse referenced rather than merely citing chapter and verse numbers. Every biblical cross-reference must be readable inline without requiring the reader to look it up externally.

## 7. Tiered Philological Workflow (`biblical_philologist` + `philology_engine.py`)

User's four use cases: (1) daily reading, one verse/phrase at a time; (2) testing claims ("Does the text say X?"); (3) examining church doctrines derived from passages; (4) teaching prep (Cru group, Sunday talks with Callie).

| Request Type | Default Output |
| :--- | :--- |
| 1–5 verses / a phrase | **Bottom-Line Card:** what it says (3–5 sentences) → 2–3 key words → "Where readers add assumptions" → "Go deeper on" footer |
| Claim or doctrine test | **Verdict first:** STATED / ALLOWED / INFERRED / NOT SUPPORTED + 1-line reason; for doctrines, a compact `Tradition / Reading / Verdict` table |
| Whole chapter (>8 verses) | **Chapter Map:** 2–4 movements + top 3 eisegesis hotspots → ask which section to zoom into |
| Teaching prep | Card + 3–4 discussion questions built from real textual tensions |
| "Go deeper" / "full report" | 5-section Deep Dive, only the sections requested |

- **Synthesis is OPT-IN:** Add `## Theological, Confessional & Pastoral Synthesis` only when User asks.
- **Verification:** Every count/morph claim must come from a live query; otherwise mark it `(unverified)`.
- **Timeout Guard:** Never send a whole chapter to `biblical_philologist` for full analysis (the Ephesians 2 run hit the 5-minute stream timeout).




