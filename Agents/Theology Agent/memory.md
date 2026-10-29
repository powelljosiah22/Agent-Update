# Theology Agent — Working Memory (`memory.md`)

## 📖 Active Theological Threads & Study Queue
- [ ] Initial onboarding dialogue: explore Callie's current scripture study, book reading list, or theological questions.
- [ ] Connect Obsidian `03_Theology_Synthesis/` notes with ChromaDB vector search.

---

## ⚡ Fast Paths & Command Cache
- **Search Personal Vault for Theological Notes:**
  Use `obsidian-search` -> `semantic_search_obsidian` with `{"query": "...", "target": "vault", "n_results": 4, "lexical_weight": 1.5}`.
- **Relink Permanent Notes & Theology Syntheses:**
  `~/Agents/Agent 0/.venv/bin/python ~/Agents/Agent 0/voice_to_brain/relink_all_notes.py`

---

## 🔗 Neural Pathways
- **Voice Memos → `03_Theology_Synthesis/`:** Voice memos containing scripture reflections, sermon takeaways, or prayer meditations are automatically routed by `brain_daemon.py` into `03_Theology_Synthesis/` and logged in `~/Agents/Theology Agent/dialogue_journal.md`.
