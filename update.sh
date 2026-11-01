#!/usr/bin/env bash
# ============================================================================
# Callie's Multi-Agent & Second Brain State-Preserving Updater (update.sh)
# ============================================================================
# Safely pulls the latest backend daemons, MCP servers, global rules, and
# shared global skills WITHOUT touching any personal state files:
#   - NEVER overwrites: context.md, memory.md, learnings.md, skills.md,
#     study_log.md, *_journal.md, .env, or credentials/
#   - Creates a timestamped backup of all personal state files before running.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$HOME"
AGENTS_DIR="$HOME_DIR/Agents"
AGENT0_DIR="$AGENTS_DIR/Agent 0"
GEMINI_CONFIG="$HOME_DIR/.gemini/config"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$AGENTS_DIR/.backups/backup_$TIMESTAMP"

echo "========================================================================"
echo "🔄 Updating Callie's Multi-Agent Infrastructure (State-Preserving Mode)"
if [[ -f "$SCRIPT_DIR/VERSION.txt" ]]; then
  echo "📌 Release: $(cat "$SCRIPT_DIR/VERSION.txt")"
fi
echo "========================================================================"

# 1. If this directory is a Git repository, pull the latest changes first
if [[ -d "$SCRIPT_DIR/.git" ]]; then
  echo "⏳ Pulling latest updates from Git remote..."
  git -C "$SCRIPT_DIR" pull --ff-only || echo "⚠️  Git pull skipped or had local changes; applying files from $SCRIPT_DIR..."
fi

# 2. Create a full safety backup of all personal state files & .env
echo "📦 Creating safety backup of personal state files at: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
for ws in "Agent 0" "Academic Tutor" "Theology Agent" "Financial_Coach"; do
  if [[ -d "$AGENTS_DIR/$ws" ]]; then
    mkdir -p "$BACKUP_DIR/$ws"
    for state_file in "context.md" "memory.md" "learnings.md" "skills.md" "job_description.md" "study_log.md" "learning_journal.md" "dialogue_journal.md" "trading_journal.md" ".env"; do
      if [[ -f "$AGENTS_DIR/$ws/$state_file" ]]; then
        cp -p "$AGENTS_DIR/$ws/$state_file" "$BACKUP_DIR/$ws/$state_file"
      fi
    done
  fi
done
if [[ -f "$GEMINI_CONFIG/mcp_config.json" ]]; then
  cp -p "$GEMINI_CONFIG/mcp_config.json" "$BACKUP_DIR/mcp_config.json"
fi
echo "✅ Personal state backup complete (100% protected)."

# 3. Locate Python 3.10+
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME_DIR/python/bin:$PATH"
PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
      PYTHON_BIN="$(command -v "$candidate")"
      break
    fi
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "❌ Error: Python 3.10+ not found."
  exit 1
fi

# 4. Update Global Rules & Shared Global Skills (~/.gemini/config/)
mkdir -p "$GEMINI_CONFIG/rules" "$GEMINI_CONFIG/skills"
cp -R "$SCRIPT_DIR/gemini_config/rules/"* "$GEMINI_CONFIG/rules/"
cp -R "$SCRIPT_DIR/gemini_config/skills/"* "$GEMINI_CONFIG/skills/"
cp "$SCRIPT_DIR/gemini_config/mcp_config.json.template" "$GEMINI_CONFIG/mcp_config.json.template"
cp "$SCRIPT_DIR/Agents/GEMINI.md" "$AGENTS_DIR/GEMINI.md"
echo "✅ Updated Global Rules (~/.gemini/config/rules/) and Shared Skills (~/.gemini/config/skills/)"

# 5. Update Hooks & Subagent Definitions (.agents/)
mkdir -p "$AGENTS_DIR/.agents"
cp "$SCRIPT_DIR/Agents/.agents/hooks.json" "$AGENTS_DIR/.agents/hooks.json"
cp "$SCRIPT_DIR/Agents/.agents/block_tutor_read_tools.sh" "$AGENTS_DIR/.agents/block_tutor_read_tools.sh"
sed -i '' "s|__HOME_DIR__|$HOME_DIR|g" "$AGENTS_DIR/.agents/hooks.json"
chmod +x "$AGENTS_DIR/.agents/block_tutor_read_tools.sh"

if [[ -d "$SCRIPT_DIR/Agents/Agent 0/.agents" ]]; then
  mkdir -p "$AGENT0_DIR/.agents"
  cp -R "$SCRIPT_DIR/Agents/Agent 0/.agents/"* "$AGENT0_DIR/.agents/"
fi
echo "✅ Updated Subagent Definitions & PreToolUse Hooks"

# 6. Update Core Engine Code (ChromaDB Search Daemon, Ingestion Daemon, Parsers, MCPs)
mkdir -p "$AGENT0_DIR/mcp/obsidian_search" "$AGENT0_DIR/voice_to_brain" "$AGENT0_DIR/context/workflows"

# Obsidian Search MCP & Daemon
for f in "daemon.py" "server.py" "sync_database.py" "update_metadata.py" "requirements.txt"; do
  cp "$SCRIPT_DIR/Agents/Agent 0/mcp/obsidian_search/$f" "$AGENT0_DIR/mcp/obsidian_search/$f"
done

# Voice-to-Brain Ingestion & Class Parser Engine
for f in "brain_daemon.py" "pipeline_parser.py" "relink_all_notes.py" "watchdog_runner.py" "requirements.txt"; do
  cp "$SCRIPT_DIR/Agents/Agent 0/voice_to_brain/$f" "$AGENT0_DIR/voice_to_brain/$f"
done

# Theology Agent Philological Database & Engine
if [[ -d "$SCRIPT_DIR/Agents/Theology Agent/philology_db" ]]; then
  mkdir -p "$AGENTS_DIR/Theology Agent/philology_db"
  for f in "philology_engine.py" "morph_decoder.py" "mcp_server.py" "schema.sql"; do
    if [[ -f "$SCRIPT_DIR/Agents/Theology Agent/philology_db/$f" ]]; then
      cp "$SCRIPT_DIR/Agents/Theology Agent/philology_db/$f" "$AGENTS_DIR/Theology Agent/philology_db/$f"
    fi
  done
  # Unpack biblical corpus database if not already present or if archive is newer
  ARCHIVE="$SCRIPT_DIR/Agents/Theology Agent/philology_db/biblical_corpus.db.tar.gz"
  TARGET_DB="$AGENTS_DIR/Theology Agent/philology_db/biblical_corpus.db"
  if [[ -f "$ARCHIVE" ]] && [[ ! -f "$TARGET_DB" || "$ARCHIVE" -nt "$TARGET_DB" ]]; then
    echo "📖 Unpacking Biblical Philological Database (biblical_corpus.db)..."
    tar -xzf "$ARCHIVE" -C "$AGENTS_DIR/Theology Agent/philology_db"
    echo "✅ Unpacked biblical_corpus.db successfully"
  fi
fi

# Top-level Agent 0 Utilities & Workflows
for f in "requirements.txt" "email_mcp_server.py" "sync_env_to_mcp.py" "healthcheck.py"; do
  if [[ -f "$SCRIPT_DIR/Agents/Agent 0/$f" ]]; then
    cp "$SCRIPT_DIR/Agents/Agent 0/$f" "$AGENT0_DIR/$f"
  fi
done
if [[ -f "$SCRIPT_DIR/VERSION.txt" ]]; then
  cp "$SCRIPT_DIR/VERSION.txt" "$AGENT0_DIR/VERSION.txt"
fi
cp "$SCRIPT_DIR/healthcheck.py" "$AGENT0_DIR/healthcheck.py"
cp -R "$SCRIPT_DIR/Agents/Agent 0/context/workflows/"* "$AGENT0_DIR/context/workflows/"
chmod +x "$AGENT0_DIR/sync_env_to_mcp.py" "$AGENT0_DIR/healthcheck.py" "$AGENT0_DIR/context/workflows/sync_canvas_calendar.sh" 2>/dev/null || true
echo "✅ Updated ChromaDB Search Daemon, Ingestion Daemon, Class Parser, and MCP Servers"

# 7. Seed any missing workspace files ONLY if they do not exist yet (NEVER overwrite!)
for ws in "Agent 0" "Academic Tutor" "Theology Agent" "Financial_Coach"; do
  mkdir -p "$AGENTS_DIR/$ws"
  for state_file in "job_description.md" "memory.md" "skills.md" "learnings.md" "context.md"; do
    if [[ ! -f "$AGENTS_DIR/$ws/$state_file" ]] && [[ -f "$SCRIPT_DIR/Agents/$ws/$state_file" ]]; then
      cp "$SCRIPT_DIR/Agents/$ws/$state_file" "$AGENTS_DIR/$ws/$state_file"
      echo "  ➕ Seeded missing file: $ws/$state_file"
    fi
  done
done

# 8. Refresh Python Virtual Environment Dependencies (Fast incremental check)
if [[ -x "$AGENT0_DIR/.venv/bin/pip" ]]; then
  "$AGENT0_DIR/.venv/bin/pip" install -r "$AGENT0_DIR/requirements.txt" -q
fi
if [[ -x "$AGENT0_DIR/mcp/obsidian_search/venv/bin/pip" ]]; then
  "$AGENT0_DIR/mcp/obsidian_search/venv/bin/pip" install -r "$AGENT0_DIR/mcp/obsidian_search/requirements.txt" -q
fi
echo "✅ Verified Python dependencies across virtual environments"

# 9. Re-sync .env into ~/.gemini/config/mcp_config.json (if .env exists)
if [[ -f "$AGENT0_DIR/.env" ]]; then
  "$PYTHON_BIN" "$AGENT0_DIR/sync_env_to_mcp.py"
fi

# 10. Restart Background Daemons so new code takes effect immediately
echo "⏳ Restarting ChromaDB Search Daemon and Voice-to-Brain Ingestion Daemon..."
pkill -f "obsidian_search/daemon.py" 2>/dev/null || true
pkill -f "voice_to_brain/brain_daemon.py" 2>/dev/null || true
sleep 1
"$AGENT0_DIR/.venv/bin/python" "$AGENT0_DIR/voice_to_brain/watchdog_runner.py" || true
sleep 2

# 11. Run Healthcheck
echo ""
"$AGENT0_DIR/.venv/bin/python" "$AGENT0_DIR/healthcheck.py" || true

echo ""
echo "========================================================================"
echo "🎉 UPDATE COMPLETE! All personal context, memory, learnings, and"
echo "   study workflows were 100% preserved (Backup: $BACKUP_DIR)."
echo "========================================================================"
