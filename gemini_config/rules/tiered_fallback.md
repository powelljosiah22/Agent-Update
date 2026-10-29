# Tiered Fallback Protocol (EFFICIENCY)

Agents must prioritize speed and minimize token overhead by strictly adhering to a tiered tool escalation process.

1. **Tier 1 (Local & Instant):** ALWAYS attempt the fastest, most specific local tools first. Use semantic vector search, targeted `grep`, or `view_file` for specific, known paths.
2. **Tier 2 (Deep Local):** If Tier 1 fails, escalate to broader local tools (e.g., `deep_research_obsidian` or directory-wide searches).
3. **Tier 3 (Subagents & Web):** Only escalate to slow or expensive tools (like spawning new subagents, scraping the web, or executing massive multi-hop context window searches) if the fast local methods explicitly fail to provide the answer.
