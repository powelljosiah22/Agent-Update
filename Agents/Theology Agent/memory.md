# Theology Agent — Working Memory (`memory.md`)

*Lean operational dashboard. Personal context → `context.md`. Workflows → `skills.md`. Discoveries → `learnings.md`.*

---

## Active Theological Threads & Study Queue
- [ ] Initial onboarding dialogue: explore current scripture study, historical/philosophical questions, or book reading list.

---

## ⚡ Fast Paths & Command Cache
- **Biblical Philological Subagent:** `biblical_philologist` (Stateless 66-book OT/NT + LXX philological engine over `biblical_corpus.db`; invoke first on exegetical/word-study prompts per Two-Stage Layering).
- **Knowledge Librarian Subagent:** `knowledge_librarian_v2` (`invoke_subagent(TypeName="knowledge_librarian_v2", ...)` for Mode 1/2 vault synthesis & Mode 3 stateless external primary-source dossiers).
- **Biblical Corpus SQLite DB:** `~/Agents/Theology Agent/philology_db/biblical_corpus.db` (1.068M words across `OT` WLC, `NT` SBLGNT, `LXX` Rahlfs 1935; 24,729 lexicon entries across Strong's/BDB & Abbott-Smith).
- **Search Personal Vault for Notes:** Use `obsidian-search` -> `semantic_search_obsidian` with `{"query": "...", "target": "vault", "n_results": 2, "lexical_weight": 1.5}`.
