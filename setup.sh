#!/usr/bin/env bash
# ============================================================================
# Modular Multi-Agent & Second Brain Infrastructure Automated Installer
# ============================================================================
# Safe, idempotent setup script for macOS.
# Supports both interactive terminal runs and non-interactive CLI execution:
#   ./setup.sh [--all] [--modules "academic,theology,finance"]
#              [--non-interactive] [--email "user@gmail.com"]
#              [--vault "/path/to/Obsidian Vault"]
#              [--classes "/path/to/Class Folders"]
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIG_HOME="${HOME}"
HOME_DIR="${HOME}"
NON_INTERACTIVE=0
SKIP_VENVS=0
MODULES_ARG=""
USER_EMAIL_ARG=""
VAULT_PATH_ARG=""
CLASSES_PATH_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --non-interactive)
      NON_INTERACTIVE=1
      shift
      ;;
    --all)
      MODULES_ARG="academic,theology,finance"
      shift
      ;;
    --modules)
      MODULES_ARG="$2"
      shift 2
      ;;
    --email)
      USER_EMAIL_ARG="$2"
      shift 2
      ;;
    --vault)
      VAULT_PATH_ARG="$2"
      shift 2
      ;;
    --classes)
      CLASSES_PATH_ARG="$2"
      shift 2
      ;;
    --home-dir)
      HOME_DIR="$2"
      export HOME="$HOME_DIR"
      shift 2
      ;;
    --skip-venvs)
      SKIP_VENVS=1
      shift
      ;;
    *)
      shift
      ;;
  esac
done

echo "========================================================================"
echo "🚀 Installing Modular Multi-Agent & Second Brain Infrastructure"
echo "========================================================================"

# 1. Verify Prerequisites (Python 3.10+ & Node.js)
export PATH="/opt/homebrew/bin:/usr/local/bin:$ORIG_HOME/python/bin:$HOME_DIR/python/bin:$PATH"
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
  echo "❌ Error: Python 3.10+ is required (macOS system /usr/bin/python3 is 3.9, which is too old for MCP & ChromaDB)."
  echo "   Install Python 3.12 via Homebrew:  brew install python@3.12"
  exit 1
fi
echo "✅ Found Python 3.10+: $("$PYTHON_BIN" --version) ($PYTHON_BIN)"

if ! command -v node >/dev/null 2>&1; then
  echo "⚠️  Warning: Node.js (node) is not installed. Optional Perplexity MCP requires Node.js."
  echo "   Install via: brew install node"
else
  echo "✅ Found Node.js: $(node --version) ($(command -v node))"
fi

# 2. Module Selection (Interactive Numbered Menu or CLI Flag)
ENABLE_ACADEMIC=0
ENABLE_THEOLOGY=0
ENABLE_FINANCE=0

if [[ -z "$MODULES_ARG" ]]; then
  if [[ "$NON_INTERACTIVE" -eq 1 ]]; then
    MODULES_ARG="academic,theology,finance"
  else
    echo ""
    echo "========================================================================"
    echo "📦 Select Infrastructure Modules to Install:"
    echo "========================================================================"
    echo "  [1] Academic Tutor & Second Brain (Class notes, PDF parser, ChromaDB)"
    echo "  [2] Theology & Biblical Philology Engine (WLC/SBLGNT/LXX, interlinear)"
    echo "  [3] Financial Coach (Wealth management, factor regressions)"
    echo "  [4] All Modules (Full Suite — Default)"
    echo ""
    read -r -p "👉 Enter choices (e.g. 1,2 or 4) [4]: " MENU_CHOICE
    MENU_CHOICE="${MENU_CHOICE:-4}"
    if [[ "$MENU_CHOICE" == *"4"* ]] || [[ "$MENU_CHOICE" == *"all"* ]]; then
      MODULES_ARG="academic,theology,finance"
    else
      SELECTED_LIST=()
      [[ "$MENU_CHOICE" == *"1"* ]] && SELECTED_LIST+=("academic")
      [[ "$MENU_CHOICE" == *"2"* ]] && SELECTED_LIST+=("theology")
      [[ "$MENU_CHOICE" == *"3"* ]] && SELECTED_LIST+=("finance")
      if [[ "${#SELECTED_LIST[@]}" -eq 0 ]]; then
        MODULES_ARG="academic,theology,finance"
      else
        MODULES_ARG=$(IFS=,; echo "${SELECTED_LIST[*]}")
      fi
    fi
  fi
fi

# If .agents_profile exists, merge existing modules unless --all was passed
if [[ -f "$HOME_DIR/.agents_profile" && "$MODULES_ARG" != "all" && "$MODULES_ARG" != "academic,theology,finance" ]]; then
  EXISTING_PROFILE=$(cat "$HOME_DIR/.agents_profile" | tr -d '[:space:]')
  if [[ -n "$EXISTING_PROFILE" && -n "$MODULES_ARG" ]]; then
    MODULES_ARG="$EXISTING_PROFILE,$MODULES_ARG"
  fi
fi

# Parse MODULES_ARG
IFS=',' read -ra RAW_MODS <<< "$MODULES_ARG"
ACTIVE_MOD_LIST=()
for m in "${RAW_MODS[@]}"; do
  clean_m=$(echo "$m" | tr '[:upper:]' '[:lower:]' | xargs)
  case "$clean_m" in
    academic|tutor|1)
      ENABLE_ACADEMIC=1
      ;;
    theology|philology|2)
      ENABLE_THEOLOGY=1
      ;;
    finance|financial|3)
      ENABLE_FINANCE=1
      ;;
    all|4)
      ENABLE_ACADEMIC=1
      ENABLE_THEOLOGY=1
      ENABLE_FINANCE=1
      ;;
  esac
done

[[ "$ENABLE_ACADEMIC" -eq 1 ]] && ACTIVE_MOD_LIST+=("academic")
[[ "$ENABLE_THEOLOGY" -eq 1 ]] && ACTIVE_MOD_LIST+=("theology")
[[ "$ENABLE_FINANCE" -eq 1 ]] && ACTIVE_MOD_LIST+=("finance")

if [[ "${#ACTIVE_MOD_LIST[@]}" -eq 0 ]]; then
  ENABLE_ACADEMIC=1
  ENABLE_THEOLOGY=1
  ENABLE_FINANCE=1
  ACTIVE_MOD_LIST=("academic" "theology" "finance")
fi

echo "✅ Selected Modules: Agent 0 (Core) + ${ACTIVE_MOD_LIST[*]}"

# 3. Auto-detect Google Drive or Default Local Second Brain Paths
DEFAULT_GDRIVE=""
if [[ -d "$HOME_DIR/Library/CloudStorage" ]]; then
  FOUND_GDRIVE=$(find "$HOME_DIR/Library/CloudStorage" -maxdepth 1 -name "GoogleDrive-*" -type d 2>/dev/null | head -n 1 || true)
  if [[ -n "$FOUND_GDRIVE" && -d "$FOUND_GDRIVE/My Drive" ]]; then
    DEFAULT_GDRIVE="$FOUND_GDRIVE/My Drive"
  fi
fi

if [[ -n "$DEFAULT_GDRIVE" ]]; then
  DEFAULT_VAULT="$DEFAULT_GDRIVE/Obsidian Vault"
  DEFAULT_CLASSES="$DEFAULT_GDRIVE/Class Folders"
else
  DEFAULT_VAULT="$HOME_DIR/SecondBrain/Obsidian_Vault"
  DEFAULT_CLASSES="$HOME_DIR/SecondBrain/Class_Folders"
fi

if [[ -n "$VAULT_PATH_ARG" ]]; then
  OBSIDIAN_VAULT_PATH="$VAULT_PATH_ARG"
elif [[ "$NON_INTERACTIVE" -eq 1 || "$ENABLE_ACADEMIC" -eq 0 ]]; then
  OBSIDIAN_VAULT_PATH="$DEFAULT_VAULT"
else
  read -r -p "📂 Obsidian Vault Path [$DEFAULT_VAULT]: " INPUT_VAULT
  OBSIDIAN_VAULT_PATH="${INPUT_VAULT:-$DEFAULT_VAULT}"
fi

if [[ -n "$CLASSES_PATH_ARG" ]]; then
  CLASS_FOLDERS_PATH="$CLASSES_PATH_ARG"
elif [[ "$NON_INTERACTIVE" -eq 1 || "$ENABLE_ACADEMIC" -eq 0 ]]; then
  CLASS_FOLDERS_PATH="$DEFAULT_CLASSES"
else
  read -r -p "📚 Class Folders Path [$DEFAULT_CLASSES]: " INPUT_CLASSES
  CLASS_FOLDERS_PATH="${INPUT_CLASSES:-$DEFAULT_CLASSES}"
fi

if [[ -n "$USER_EMAIL_ARG" ]]; then
  USER_EMAIL="$USER_EMAIL_ARG"
elif [[ "$NON_INTERACTIVE" -eq 1 ]]; then
  USER_EMAIL="your_email@gmail.com"
else
  read -r -p "✉️  Your Gmail Address [your_email@gmail.com]: " INPUT_EMAIL
  USER_EMAIL="${INPUT_EMAIL:-your_email@gmail.com}"
fi

echo ""
echo "Configuration Summary:"
echo "  • Home Directory:      $HOME_DIR"
echo "  • Active Modules:      ${ACTIVE_MOD_LIST[*]}"
[[ "$ENABLE_ACADEMIC" -eq 1 ]] && echo "  • Obsidian Vault Path: $OBSIDIAN_VAULT_PATH"
[[ "$ENABLE_ACADEMIC" -eq 1 ]] && echo "  • Class Folders Path:  $CLASS_FOLDERS_PATH"
echo "  • Primary Email:       $USER_EMAIL"
echo ""

# 4. Backup existing ~/.gemini/config/mcp_config.json if present
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$HOME_DIR/.gemini/config/rules" "$HOME_DIR/.gemini/config/skills"
if [[ -f "$HOME_DIR/.gemini/config/mcp_config.json" ]]; then
  cp "$HOME_DIR/.gemini/config/mcp_config.json" "$HOME_DIR/.gemini/config/mcp_config.json.bak.$TIMESTAMP"
  echo "📦 Backed up existing mcp_config.json -> mcp_config.json.bak.$TIMESTAMP"
fi

# 5. Install Global Rules, Skills, and MCP Template into ~/.gemini/config/
cp -R "$SCRIPT_DIR/gemini_config/rules/"* "$HOME_DIR/.gemini/config/rules/"
cp -R "$SCRIPT_DIR/gemini_config/skills/"* "$HOME_DIR/.gemini/config/skills/"
cp "$SCRIPT_DIR/gemini_config/mcp_config.json.template" "$HOME_DIR/.gemini/config/mcp_config.json.template"
echo "✅ Installed Global Rules and Custom Skills into ~/.gemini/config/"

# 6. Install Selected ~/Agents Workspaces, Daemons, and Subagent Plugins
mkdir -p "$HOME_DIR/Agents" "$HOME_DIR/Agents/.agents"

# Write ~/Agents/.agents_profile for state-preserving updates and MCP filtering
JSON_MODS=$(printf '"%s",' "${ACTIVE_MOD_LIST[@]}" | sed 's/,$//')
cat > "$HOME_DIR/Agents/.agents_profile" <<EOF
{
  "modules": [$JSON_MODS],
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "$(cat "$SCRIPT_DIR/VERSION.txt" 2>/dev/null || echo "1.1.0")"
}
EOF
echo "✅ Saved module profile to ~/Agents/.agents_profile"

# Always install Workspace Root Rules & Agent 0 Core
cp "$SCRIPT_DIR/Agents/GEMINI.md" "$HOME_DIR/Agents/GEMINI.md"
cp "$SCRIPT_DIR/Agents/.agents/hooks.json" "$HOME_DIR/Agents/.agents/hooks.json"
cp "$SCRIPT_DIR/Agents/.agents/block_tutor_read_tools.sh" "$HOME_DIR/Agents/.agents/block_tutor_read_tools.sh"
sed -i '' "s|__HOME_DIR__|$HOME_DIR|g" "$HOME_DIR/Agents/.agents/hooks.json"
chmod +x "$HOME_DIR/Agents/.agents/block_tutor_read_tools.sh"

mkdir -p "$HOME_DIR/Agents/Agent 0"
cp -R "$SCRIPT_DIR/Agents/Agent 0/." "$HOME_DIR/Agents/Agent 0/"
cp "$SCRIPT_DIR/AGENT_SETUP_WIZARD.md" "$HOME_DIR/Agents/Agent 0/AGENT_SETUP_WIZARD.md"
cp "$SCRIPT_DIR/README_HUMAN_SETUP.md" "$HOME_DIR/Agents/Agent 0/README_HUMAN_SETUP.md"
cp "$SCRIPT_DIR/update.sh" "$HOME_DIR/Agents/Agent 0/update.sh"
chmod +x "$HOME_DIR/Agents/Agent 0/update.sh"
chmod +x "$HOME_DIR/Agents/Agent 0/context/workflows/sync_canvas_calendar.sh" 2>/dev/null || true
chmod +x "$HOME_DIR/Agents/Agent 0/sync_env_to_mcp.py"
chmod +x "$HOME_DIR/Agents/Agent 0/healthcheck.py"

# Prune unselected Subagents from ~/Agents/Agent 0/.agents/plugins/agent-0-subagents/agents/
SUBAGENTS_DIR="$HOME_DIR/Agents/Agent 0/.agents/plugins/agent-0-subagents/agents"
if [[ "$ENABLE_ACADEMIC" -eq 0 ]]; then
  rm -rf "$SUBAGENTS_DIR/academic_tutor" "$SUBAGENTS_DIR/knowledge_librarian_v2"
fi
if [[ "$ENABLE_THEOLOGY" -eq 0 ]]; then
  rm -rf "$SUBAGENTS_DIR/theology_philosophical_agent" "$SUBAGENTS_DIR/biblical_philologist"
fi
if [[ "$ENABLE_FINANCE" -eq 0 ]]; then
  rm -rf "$SUBAGENTS_DIR/financial_coach"
fi

# Conditionally install Domain Workspaces
if [[ "$ENABLE_ACADEMIC" -eq 1 ]]; then
  mkdir -p "$HOME_DIR/Agents/Academic Tutor"
  cp -R "$SCRIPT_DIR/Agents/Academic Tutor/." "$HOME_DIR/Agents/Academic Tutor/"
  echo "  ✅ Installed Workspace: Academic Tutor (+ academic_tutor & knowledge_librarian_v2 subagents)"
fi

if [[ "$ENABLE_THEOLOGY" -eq 1 ]]; then
  mkdir -p "$HOME_DIR/Agents/Theology Agent"
  cp -R "$SCRIPT_DIR/Agents/Theology Agent/." "$HOME_DIR/Agents/Theology Agent/"
  # Unpack biblical_corpus.db if archive exists
  ARCHIVE="$HOME_DIR/Agents/Theology Agent/philology_db/biblical_corpus.db.tar.gz"
  TARGET_DB="$HOME_DIR/Agents/Theology Agent/philology_db/biblical_corpus.db"
  if [[ -f "$ARCHIVE" && ! -f "$TARGET_DB" ]]; then
    echo "  📖 Unpacking Biblical Philological Database (biblical_corpus.db)..."
    tar -xzf "$ARCHIVE" -C "$HOME_DIR/Agents/Theology Agent/philology_db"
  fi
  echo "  ✅ Installed Workspace: Theology Agent & Biblical Philology Engine"
fi

if [[ "$ENABLE_FINANCE" -eq 1 ]]; then
  mkdir -p "$HOME_DIR/Agents/Financial_Coach"
  cp -R "$SCRIPT_DIR/Agents/Financial_Coach/." "$HOME_DIR/Agents/Financial_Coach/"
  echo "  ✅ Installed Workspace: Financial Coach"
fi

# 7. Create ~/Agents/Agent 0/.env from .env.template (if not already customized)
ENV_FILE="$HOME_DIR/Agents/Agent 0/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cp "$HOME_DIR/Agents/Agent 0/.env.template" "$ENV_FILE"
  sed -i '' "s|__HOME_DIR__|$HOME_DIR|g" "$ENV_FILE"
  sed -i '' "s|__OBSIDIAN_VAULT_PATH__|$OBSIDIAN_VAULT_PATH|g" "$ENV_FILE"
  sed -i '' "s|__CLASS_FOLDERS_PATH__|$CLASS_FOLDERS_PATH|g" "$ENV_FILE"
  sed -i '' "s|__USER_EMAIL__|$USER_EMAIL|g" "$ENV_FILE"
  echo "✅ Created $ENV_FILE"
else
  echo "ℹ️  Existing $ENV_FILE found — preserving your existing keys."
fi

# Create or update accounts.json if placeholder present
ACCOUNTS_FILE="$HOME_DIR/Agents/Agent 0/credentials/accounts.json"
if [[ ! -f "$ACCOUNTS_FILE" ]] || grep -Fq "__USER_EMAIL__" "$ACCOUNTS_FILE"; then
  cp "$HOME_DIR/Agents/Agent 0/credentials/accounts.json.template" "$ACCOUNTS_FILE"
  sed -i '' "s|__USER_EMAIL__|$USER_EMAIL|g" "$ACCOUNTS_FILE"
fi

# Sync .env and active module filter into ~/.gemini/config/mcp_config.json
"$PYTHON_BIN" "$HOME_DIR/Agents/Agent 0/sync_env_to_mcp.py"

# 8. Seed Second Brain Vault & Class Folder Directories (Only when Academic is enabled)
if [[ "$ENABLE_ACADEMIC" -eq 1 ]]; then
  mkdir -p "$OBSIDIAN_VAULT_PATH/00_Inbox/Voice_Notes/Processed_Audio"
  mkdir -p "$OBSIDIAN_VAULT_PATH/01_Daily_Notes"
  mkdir -p "$OBSIDIAN_VAULT_PATH/02_Permanent_Notes"
  mkdir -p "$OBSIDIAN_VAULT_PATH/03_Theology_Synthesis"
  mkdir -p "$OBSIDIAN_VAULT_PATH/04_Master_Indexes"

  if [[ ! -f "$OBSIDIAN_VAULT_PATH/04_Master_Indexes/Welcome_to_Your_Second_Brain.md" ]]; then
    cp "$SCRIPT_DIR/Starter_Vault_Templates/Obsidian_Vault/04_Master_Indexes/Welcome_to_Your_Second_Brain.md" "$OBSIDIAN_VAULT_PATH/04_Master_Indexes/Welcome_to_Your_Second_Brain.md"
  fi

  mkdir -p "$CLASS_FOLDERS_PATH/EXAMPLE_COURSE_101/1_Syllabus_and_Schedule"
  mkdir -p "$CLASS_FOLDERS_PATH/EXAMPLE_COURSE_101/1_Lectures_and_Slides"
  mkdir -p "$CLASS_FOLDERS_PATH/EXAMPLE_COURSE_101/1_Homework_and_Problems"
  mkdir -p "$CLASS_FOLDERS_PATH/EXAMPLE_COURSE_101/1_Exams_and_Reviews"
  mkdir -p "$CLASS_FOLDERS_PATH/EXAMPLE_COURSE_101/2_Parsed_Markdown"

  if [[ ! -f "$CLASS_FOLDERS_PATH/EXAMPLE_COURSE_101/2_Parsed_Markdown/Course_Overview_Template.md" ]]; then
    cp "$SCRIPT_DIR/Starter_Vault_Templates/Class_Folders/EXAMPLE_COURSE_101/2_Parsed_Markdown/Course_Overview_Template.md" "$CLASS_FOLDERS_PATH/EXAMPLE_COURSE_101/2_Parsed_Markdown/Course_Overview_Template.md"
  fi
  echo "✅ Seeded Obsidian Vault & Class Folders directory trees"
fi

# 9. Build Python Virtual Environments (unless --skip-venvs passed for dry-run testing)
if [[ "$SKIP_VENVS" -eq 0 ]]; then
  echo "⏳ Building main Python virtual environment (~/Agents/Agent 0/.venv)..."
  "$PYTHON_BIN" -m venv "$HOME_DIR/Agents/Agent 0/.venv"
  "$HOME_DIR/Agents/Agent 0/.venv/bin/pip" install --upgrade pip -q
  "$HOME_DIR/Agents/Agent 0/.venv/bin/pip" install -r "$HOME_DIR/Agents/Agent 0/requirements.txt" -q
  echo "✅ Installed main Python venv dependencies"

  if [[ "$ENABLE_ACADEMIC" -eq 1 || "$ENABLE_THEOLOGY" -eq 1 ]]; then
    echo "⏳ Building Vector & Search virtual environment (~/Agents/Agent 0/mcp/obsidian_search/venv)..."
    "$PYTHON_BIN" -m venv "$HOME_DIR/Agents/Agent 0/mcp/obsidian_search/venv"
    "$HOME_DIR/Agents/Agent 0/mcp/obsidian_search/venv/bin/pip" install --upgrade pip -q
    "$HOME_DIR/Agents/Agent 0/mcp/obsidian_search/venv/bin/pip" install -r "$HOME_DIR/Agents/Agent 0/mcp/obsidian_search/requirements.txt" -q
    echo "✅ Installed Vector & Search venv dependencies"
  fi

  # 10. Initialize ChromaDB & Start Background Daemons (Only when Academic is enabled)
  if [[ "$ENABLE_ACADEMIC" -eq 1 ]]; then
    echo "⏳ Initializing ChromaDB collections and pre-warming local vector embeddings..."
    "$HOME_DIR/Agents/Agent 0/mcp/obsidian_search/venv/bin/python" "$HOME_DIR/Agents/Agent 0/mcp/obsidian_search/sync_database.py" || true

    echo "⏳ Starting background daemons via watchdog_runner.py..."
    "$HOME_DIR/Agents/Agent 0/.venv/bin/python" "$HOME_DIR/Agents/Agent 0/voice_to_brain/watchdog_runner.py" || true
    sleep 2

    # 12. Configure Idempotent 15-Minute Watchdog Cron Job
    CRON_CMD="*/15 * * * * \"$HOME_DIR/Agents/Agent 0/.venv/bin/python\" \"$HOME_DIR/Agents/Agent 0/voice_to_brain/watchdog_runner.py\" >> \"$HOME_DIR/Agents/Agent 0/voice_to_brain/watchdog_cron.log\" 2>&1"
    EXISTING_CRON=$(crontab -l 2>/dev/null || true)
    if ! echo "$EXISTING_CRON" | grep -Fq "watchdog_runner.py"; then
      (echo "$EXISTING_CRON"; echo "$CRON_CMD") | sed '/^$/d' | crontab - 2>/dev/null || echo "⚠️  Note: Could not update crontab automatically (you can add it manually if desired)."
      echo "✅ Added 15-minute self-healing watchdog cron job"
    else
      echo "✅ Watchdog cron job already present in crontab"
    fi
  fi

  # 13. Run System Healthcheck
  echo ""
  "$HOME_DIR/Agents/Agent 0/.venv/bin/python" "$HOME_DIR/Agents/Agent 0/healthcheck.py" || true
fi

echo ""
echo "========================================================================"
echo "🎉 INSTALLATION COMPLETE! (Modules: ${ACTIVE_MOD_LIST[*]})"
echo "Next Steps:"
echo "  1. Add your API keys to: ~/Agents/Agent 0/.env"
echo "  2. Run: python3 ~/Agents/Agent 0/sync_env_to_mcp.py"
echo "  3. Open ~/Agents/Agent 0 in Antigravity, reload the window, and paste"
echo "     the onboarding prompt from README_HUMAN_SETUP.md!"
echo "========================================================================"
