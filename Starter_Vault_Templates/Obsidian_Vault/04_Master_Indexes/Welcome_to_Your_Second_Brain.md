---
title: Welcome to Your Second Brain
date: 2026-10-15
tags: [second-brain, index, onboarding]
---

# 🧠 Welcome to Your Second Brain

This Obsidian vault is connected directly to your **Antigravity Multi-Agent Ecosystem** (`Agent 0`, `Academic Tutor`, `Theology Agent`, and `Financial Coach`) via a local ChromaDB Hybrid Search Daemon (`127.0.0.1:8085`).

## 📂 Vault Directory Architecture
- **`00_Inbox/Voice_Notes/`** — Drop `.m4a`, `.mp3`, or `.wav` voice memos here. The background `brain_daemon.py` will automatically transcribe them with Gemini, classify them (`permanent_note`, `theology`, or `academic_study`), create a structured Markdown note, and move the audio to `Processed_Audio/`.
- **`01_Daily_Notes/`** — Daily plans, reflections, and quick capture logs.
- **`02_Permanent_Notes/`** — Atomic Zettelkasten notes on ideas, books, career, and strategy. Automatically linked via `## 🔗 Vector Semantic Connections`.
- **`03_Theology_Synthesis/`** — Scripture reflections, sermon notes, and theological syntheses connected to your `Theology Agent`.
- **`04_Master_Indexes/`** — High-level Maps of Content (MOCs) and index notes.

## 🔗 Vector Semantic Connections
- *Run `relink_all_notes.py` after adding new notes to auto-populate semantic links!*
