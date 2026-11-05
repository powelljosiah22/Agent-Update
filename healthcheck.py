#!/usr/bin/env python3
"""
Multi-Agent Infrastructure Healthcheck & Verification Suite.
Verifies:
1. Global Rules & Custom Skills in ~/.gemini/config/
2. ~/.gemini/config/mcp_config.json syntax & resolved paths
3. Active Agent Workspaces & 5-File Knowledge Architecture (per .agents_profile)
4. Python Virtual Environments & critical imports
5. Node.js Google Drive MCP dependencies
6. .env Configuration & API key readiness
7. Second Brain Vault, Class Folders, or Biblical Corpus DB (per module)
8. Live ChromaDB HTTP Search Daemon on 127.0.0.1:8085 (when Academic active)
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

HOME = Path(os.environ.get("HOME", str(Path.home())))
AGENTS_ROOT = HOME / "Agents"
PROFILE_PATH = AGENTS_ROOT / ".agents_profile"
AGENT0_DIR = AGENTS_ROOT / "Agent 0"
GEMINI_CONFIG = HOME / ".gemini" / "config"

PASS_COUNT = 0
WARN_COUNT = 0
FAIL_COUNT = 0


def ok(msg: str):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"  ✅ [PASS] {msg}")


def warn(msg: str):
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"  ⚠️  [WARN] {msg}")


def fail(msg: str):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"  ❌ [FAIL] {msg}")


def parse_env(env_file: Path) -> dict:
    values = {}
    if not env_file.exists():
        return values
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def get_active_modules() -> set:
    if not PROFILE_PATH.exists():
        return {"academic", "theology", "finance"}
    try:
        data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        mods = data.get("modules", ["academic", "theology", "finance"])
        return {m.strip().lower() for m in mods if m.strip()}
    except Exception:
        return {"academic", "theology", "finance"}


def main():
    active_modules = get_active_modules()
    print("=" * 72)
    print("🩺 MULTI-AGENT INFRASTRUCTURE HEALTHCHECK")
    version_file = AGENT0_DIR / "VERSION.txt"
    if version_file.exists():
        print(f"📌 Installed Release: {version_file.read_text(encoding='utf-8').strip()}")
    print(f"📦 Active Profile Modules: {', '.join(sorted(active_modules))}")
    print("=" * 72)

    # 1. Global Rules & Skills
    print("\n1. Global Rules & Skills (~/.gemini/config/)")
    expected_rules = [
        "calibrated_candor.md",
        "core_persona.md",
        "destructive_pauses.md",
        "email_communication_safety.md",
        "katex_safety.md",
        "knowledge_lifecycle.md",
        "tiered_fallback.md",
        "workspace_hygiene.md",
        "work_verification_and_audit.md",
    ]
    for r in expected_rules:
        p = GEMINI_CONFIG / "rules" / r
        if p.exists():
            ok(f"Rule installed: {r}")
        else:
            fail(f"Missing global rule: {p}")

    expected_skills = [
        "adaptive-quiz-generator/SKILL.md",
        "resync-vault/SKILL.md",
        "gcp-vm-management/SKILL.md",
        "update-agents/SKILL.md",
    ]
    for s in expected_skills:
        p = GEMINI_CONFIG / "skills" / s
        if p.exists():
            ok(f"Skill installed: {s}")
        else:
            fail(f"Missing global skill: {p}")

    # 2. MCP Config
    print("\n2. MCP Server Configuration (~/.gemini/config/mcp_config.json)")
    mcp_path = GEMINI_CONFIG / "mcp_config.json"
    if not mcp_path.exists():
        fail(f"Missing {mcp_path}")
    else:
        try:
            raw = mcp_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            servers = data.get("mcpServers", {})
            ok(f"Valid JSON with {len(servers)} MCP servers configured: {', '.join(servers.keys())}")
            if any(ph in raw for ph in ["__HOME_DIR__", "__OBSIDIAN_VAULT_PATH__", "__CLASS_FOLDERS_PATH__"]):
                fail("Unresolved path placeholders (__HOME_DIR__, __OBSIDIAN_VAULT_PATH__, or __CLASS_FOLDERS_PATH__) in mcp_config.json")
            else:
                ok("All path placeholders resolved in mcp_config.json")
        except Exception as e:
            fail(f"Invalid JSON in {mcp_path}: {e}")

    # 3. Workspaces (Scoped to Active Modules)
    print("\n3. Agent Workspaces & 5-File Knowledge Architecture (~/Agents/)")
    workspaces = ["Agent 0"]
    if "academic" in active_modules:
        workspaces.append("Academic Tutor")
    if "theology" in active_modules:
        workspaces.append("Theology Agent")
    if "finance" in active_modules:
        workspaces.append("Financial_Coach")

    core_files = ["job_description.md", "memory.md", "skills.md", "learnings.md", "context.md"]
    for ws in workspaces:
        ws_dir = AGENTS_ROOT / ws
        missing = [f for f in core_files if not (ws_dir / f).exists()]
        if not missing:
            ok(f"Workspace '{ws}' has all 5 core knowledge files")
        else:
            fail(f"Workspace '{ws}' missing files: {missing}")

    if "theology" in active_modules:
        phil_db = AGENTS_ROOT / "Theology Agent" / "philology_db" / "biblical_corpus.db"
        if phil_db.exists():
            ok("Biblical Philology Corpus DB (biblical_corpus.db) verified")
        else:
            fail(f"Missing Biblical Corpus DB at {phil_db}")

    # 4. Python Virtual Environments
    print("\n4. Python Virtual Environments & Dependencies")
    venv_main = AGENT0_DIR / ".venv" / "bin" / "python"
    venv_search = AGENT0_DIR / "mcp" / "obsidian_search" / "venv" / "bin" / "python"

    if venv_main.exists():
        res = subprocess.run(
            [str(venv_main), "-c", "import dotenv, fitz, pptx, docx, openpyxl, watchdog, yfinance, pandas, mcp; print('OK')"],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            ok("Main venv (~/Agents/Agent 0/.venv) & all core packages verified")
        else:
            fail(f"Main venv missing packages: {res.stderr.strip()}")
    else:
        fail(f"Missing main Python venv at {venv_main}")

    if "academic" in active_modules or "theology" in active_modules:
        if venv_search.exists():
            res = subprocess.run(
                [str(venv_search), "-c", "import chromadb, onnxruntime, dotenv; print('OK')"],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                ok("Search & Vector venv (mcp/obsidian_search/venv) & ChromaDB verified")
            else:
                fail(f"Search venv missing packages: {res.stderr.strip()}")
        else:
            fail(f"Missing Search Python venv at {venv_search}")

    # 5. Node.js Google Drive MCP
    print("\n5. Google Drive MCP Node Dependencies")
    gdrive_modules = AGENT0_DIR / "mcp" / "google_drive" / "node_modules" / "googleapis"
    if gdrive_modules.exists():
        ok("Google Drive MCP node_modules/googleapis installed")
    else:
        warn("Google Drive MCP node_modules not found (run: npm --prefix ~/Agents/Agent\\ 0/mcp/google_drive install)")

    # 6. .env & Credentials Check
    print("\n6. Environment Variables & API Keys (~/Agents/Agent 0/.env)")
    env_file = AGENT0_DIR / ".env"
    env_vars = parse_env(env_file)
    if not env_file.exists():
        fail(f"Missing {env_file}")
    else:
        ok(f"Found {env_file}")
        for key in ["GEMINI_API_KEY", "USER_EMAIL", "GMAIL_APP_PASSWORD", "PERPLEXITY_API_KEY"]:
            val = env_vars.get(key, "")
            if not val or val.startswith("YOUR_") or val == "your_email@gmail.com":
                warn(f"{key} is still set to placeholder ({val or 'empty'}). Update ~/Agents/Agent 0/.env and run sync_env_to_mcp.py")
            else:
                ok(f"{key} is configured")

        if "academic" in active_modules:
            for path_key in ["OBSIDIAN_VAULT_PATH", "CLASS_FOLDERS_PATH"]:
                p_str = env_vars.get(path_key, "")
                if p_str and Path(p_str).exists():
                    ok(f"{path_key} exists on disk: {p_str}")
                else:
                    warn(f"{path_key} directory not found yet: {p_str}")

    # 7. ChromaDB HTTP Daemon (Port 8085) — Only required when Academic is active
    if "academic" in active_modules:
        print("\n7. ChromaDB Hybrid Search Daemon (http://127.0.0.1:8085/health)")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8085/health", timeout=3) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    ok(f"ChromaDB Search Daemon is ONLINE (port 8085): {payload}")
                else:
                    warn(f"Search daemon returned HTTP {resp.status}")
        except Exception as e:
            warn(f"Search daemon not currently responding on 127.0.0.1:8085 ({e}). Run watchdog_runner.py to start it.")

    print("\n" + "=" * 72)
    print(f"SUMMARY: {PASS_COUNT} PASSED | {WARN_COUNT} WARNINGS | {FAIL_COUNT} FAILED")
    print("=" * 72)
    return 1 if FAIL_COUNT > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
