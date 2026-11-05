#!/usr/bin/env python3
"""
Syncs credentials and paths from ~/Agents/Agent 0/.env directly into
~/.gemini/config/mcp_config.json, filtering active MCP servers based on
~/Agents/.agents_profile (if present). Defaults to all modules if no profile
exists, preserving 100% backward compatibility.
"""
import json
import os
from pathlib import Path

HOME = Path(os.environ.get("HOME", str(Path.home())))
AGENTS_ROOT = HOME / "Agents"
PROFILE_PATH = AGENTS_ROOT / ".agents_profile"
ENV_PATH = AGENTS_ROOT / "Agent 0" / ".env"
MCP_TEMPLATE_PATH = HOME / ".gemini" / "config" / "mcp_config.json.template"
MCP_CONFIG_PATH = HOME / ".gemini" / "config" / "mcp_config.json"


def parse_env(env_file: Path) -> dict:
    values = {}
    if not env_file.exists():
        return values
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        values[k] = v
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
    if not MCP_TEMPLATE_PATH.exists():
        print(f"❌ Missing template at {MCP_TEMPLATE_PATH}")
        return 1

    env_vars = parse_env(ENV_PATH)
    home_str = str(HOME)
    vault_path = env_vars.get("OBSIDIAN_VAULT_PATH", f"{home_str}/SecondBrain/Obsidian_Vault")
    classes_path = env_vars.get("CLASS_FOLDERS_PATH", f"{home_str}/SecondBrain/Class_Folders")
    user_email = env_vars.get("USER_EMAIL", "your_email@gmail.com")
    gemini_key = env_vars.get("GEMINI_API_KEY", "") or "YOUR_GEMINI_API_KEY"
    perplexity_key = env_vars.get("PERPLEXITY_API_KEY", "") or "YOUR_PERPLEXITY_API_KEY"
    gmail_app_pw = env_vars.get("GMAIL_APP_PASSWORD", "") or "YOUR_16_CHAR_GMAIL_APP_PASSWORD"

    raw = MCP_TEMPLATE_PATH.read_text(encoding="utf-8")
    raw = raw.replace("__HOME_DIR__", home_str)
    raw = raw.replace("__OBSIDIAN_VAULT_PATH__", vault_path)
    raw = raw.replace("__CLASS_FOLDERS_PATH__", classes_path)
    raw = raw.replace("__USER_EMAIL__", user_email)
    raw = raw.replace("__GEMINI_API_KEY__", gemini_key)
    raw = raw.replace("YOUR_GEMINI_API_KEY", gemini_key)
    raw = raw.replace("__PERPLEXITY_API_KEY__", perplexity_key)
    raw = raw.replace("YOUR_PERPLEXITY_API_KEY", perplexity_key)
    raw = raw.replace("__GMAIL_APP_PASSWORD__", gmail_app_pw)
    raw = raw.replace("YOUR_16_CHAR_GMAIL_APP_PASSWORD", gmail_app_pw)

    # Validate JSON and filter by active modules
    parsed = json.loads(raw)
    servers = parsed.get("mcpServers", {})
    active_modules = get_active_modules()

    if "academic" not in active_modules:
        servers.pop("obsidian-search", None)
    if "theology" not in active_modules:
        servers.pop("biblical-philology", None)
    if "finance" not in active_modules:
        servers.pop("yfinance", None)
        servers.pop("robinhood", None)

    parsed["mcpServers"] = servers
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MCP_CONFIG_PATH.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
    print(f"✅ Synced .env settings into {MCP_CONFIG_PATH} (Active modules: {', '.join(sorted(active_modules))})")

    # Also sync USER_EMAIL into credentials/accounts.json
    accounts_tpl = AGENTS_ROOT / "Agent 0" / "credentials" / "accounts.json.template"
    accounts_out = AGENTS_ROOT / "Agent 0" / "credentials" / "accounts.json"
    if accounts_tpl.exists():
        acc_raw = accounts_tpl.read_text(encoding="utf-8").replace("__USER_EMAIL__", user_email)
        accounts_out.write_text(acc_raw, encoding="utf-8")
        print(f"✅ Synced USER_EMAIL ({user_email}) into {accounts_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
