# Theology Agent — Working Memory (`memory.md`)

*Lean operational dashboard. Personal context & convictions → `context.md`. Workflows → `skills.md`. Discoveries → `learnings.md`.*

---

## 📖 Active Session Focus & Study Queue
- [ ] **First-Session Personalization:** Welcome the user, learn their theological background/tradition, favorite authors, and current Scripture or book study, and save their profile to `context.md` (removing the `[UNCONFIGURED_BLANK_SLATE]` tag).

---

## 🔗 Neural Pathways
- *(Populate cross-domain connections here as the user's theological study connects with their life, vocation, relationships, and Second Brain notes).*

---

## ⚡ Fast Paths & Command Cache
- **Biblical Philological Subagent:** `biblical_philologist` (Stateless 66-book OT/NT + LXX philological engine over `biblical_corpus.db`; invoke first on exegetical/word-study prompts per Two-Stage Layering).
- **Knowledge Librarian Subagent:** `knowledge_librarian_v2` (`invoke_subagent(TypeName="knowledge_librarian_v2", ...)` for Mode 1/2 vault synthesis & Mode 3 stateless external primary-source dossiers).
- **Biblical Corpus SQLite DB:** `~/Agents/Theology Agent/philology_db/biblical_corpus.db` (1.068M words across `OT` WLC, `NT` SBLGNT, `LXX` Rahlfs 1935; 24,729 lexicon entries across Strong's/BDB & Abbott-Smith).
- **Search Personal Vault for Notes:** Use `obsidian-search` -> `semantic_search_obsidian` with `{"query": "...", "target": "vault", "n_results": 2, "lexical_weight": 1.5}`.
