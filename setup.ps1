# ==============================================================================
# setup.ps1 — Windows PowerShell Modular Multi-Agent Installer
# ==============================================================================
param(
    [string]$modules = "",
    [string]$email = "",
    [string]$vault = "",
    [string]$classes = "",
    [string]$homeDir = $env:USERPROFILE,
    [switch]$all = $false,
    [switch]$skipVenvs = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🚀 Installing Modular Multi-Agent & Second Brain Infrastructure (Windows)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Resolve Home Directory
$TARGET_HOME = $homeDir
if (-not (Test-Path $TARGET_HOME)) {
    New-Item -ItemType Directory -Path $TARGET_HOME -Force | Out-Null
}

# 2. Detect Python 3.10+
$PYTHON_BIN = $null
foreach ($candidate in @("python", "py", "python3")) {
    try {
        $testCmd = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}'); raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $testCmd) {
            $PYTHON_BIN = $candidate
            Write-Host "✅ Found Python 3.10+: $testCmd ($candidate)" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $PYTHON_BIN) {
    Write-Host "❌ Error: Python 3.10+ is required." -ForegroundColor Red
    Write-Host "   Please download and install Python from: https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    Write-Host "   (Be sure to check 'Add python.exe to PATH' during installation!)" -ForegroundColor Yellow
    exit 1
}

# 3. Determine Modules
if ($all) {
    $modules = "academic,theology,finance"
}

if ([string]::IsNullOrWhiteSpace($modules)) {
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Yellow
    Write-Host "  Select Agent Modules to Install:" -ForegroundColor Yellow
    Write-Host "===========================================================" -ForegroundColor Yellow
    Write-Host "  [1] Academic Tutor only (Socratic tutor, class notes, TVM/Finance/Accounting)"
    Write-Host "  [2] Theology Agent & Philology DB (Biblical corpus, interlinear, Patristics)"
    Write-Host "  [3] Financial Coach only (Wealth management, factor models, market data)"
    Write-Host "  [4] All Agents (Full Suite: Academic + Theology + Financial + Agent 0)"
    Write-Host "===========================================================" -ForegroundColor Yellow
    $choice = Read-Host "Enter your choice [1-4] (default: 1)"
    switch ($choice) {
        "2" { $modules = "theology" }
        "3" { $modules = "finance" }
        "4" { $modules = "academic,theology,finance" }
        default { $modules = "academic" }
    }
}

# 4. Save & Merge Active Profile
$PROFILE_FILE = Join-Path $TARGET_HOME ".agents_profile"
if (Test-Path $PROFILE_FILE) {
    $existing = (Get-Content -Path $PROFILE_FILE -Raw).Trim()
    if ($existing -and -not $all) {
        $combined = ($existing -split "," + $modules -split ",") | Where-Object { $_ } | Select-Object -Unique
        $modules = ($combined -join ",")
    }
}
$INSTALL_ACADEMIC = ($modules -match "academic")
$INSTALL_THEOLOGY = ($modules -match "theology")
$INSTALL_FINANCE  = ($modules -match "finance")

Write-Host "📦 Active Profile Modules: $modules" -ForegroundColor Cyan
Set-Content -Path $PROFILE_FILE -Value $modules -Force
Write-Host "✅ Recorded active profile in $PROFILE_FILE" -ForegroundColor Green

# 5. Base Directories
$AGENTS_DIR = Join-Path $TARGET_HOME "Agents"
$CONFIG_DIR = Join-Path $TARGET_HOME ".gemini\config"
$RULES_DIR  = Join-Path $CONFIG_DIR "rules"
$SKILLS_DIR = Join-Path $CONFIG_DIR "skills"
$MCP_DIR    = Join-Path $TARGET_HOME ".gemini\antigravity\mcp"

$SCRIPT_ROOT = $PSScriptRoot
if (-not $SCRIPT_ROOT) { $SCRIPT_ROOT = (Get-Location).Path }

New-Item -ItemType Directory -Path $AGENTS_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $RULES_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $SKILLS_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $MCP_DIR -Force | Out-Null

# 6. Deploy Global Rules & Skills
Write-Host "⚙️  Installing Global Rules and Custom Skills..." -ForegroundColor Cyan
if (Test-Path "$SCRIPT_ROOT\gemini_config\rules") {
    Copy-Item -Path "$SCRIPT_ROOT\gemini_config\rules\*" -Destination $RULES_DIR -Recurse -Force
}
if (Test-Path "$SCRIPT_ROOT\gemini_config\skills") {
    Copy-Item -Path "$SCRIPT_ROOT\gemini_config\skills\*" -Destination $SKILLS_DIR -Recurse -Force
}

# 7. Deploy Workspaces
Write-Host "📦 Deploying Selected Agent Workspaces..." -ForegroundColor Cyan

# Always install Agent 0 (Master Node)
$AGENT0_DEST = Join-Path $AGENTS_DIR "Agent 0"
if (-not (Test-Path $AGENT0_DEST)) {
    New-Item -ItemType Directory -Path $AGENT0_DEST -Force | Out-Null
}
Copy-Item -Path "$SCRIPT_ROOT\Agents\Agent 0\*" -Destination $AGENT0_DEST -Recurse -Force

# Academic Tutor
if ($INSTALL_ACADEMIC) {
    Write-Host "   Installing Academic Tutor..." -ForegroundColor Green
    $ACAD_DEST = Join-Path $AGENTS_DIR "Academic Tutor"
    New-Item -ItemType Directory -Path $ACAD_DEST -Force | Out-Null
    Copy-Item -Path "$SCRIPT_ROOT\Agents\Academic Tutor\*" -Destination $ACAD_DEST -Recurse -Force
}

# Theology Agent & Philology DB
if ($INSTALL_THEOLOGY) {
    Write-Host "   Installing Theology Agent & Philology DB..." -ForegroundColor Green
    $THEO_DEST = Join-Path $AGENTS_DIR "Theology Agent"
    New-Item -ItemType Directory -Path $THEO_DEST -Force | Out-Null
    Copy-Item -Path "$SCRIPT_ROOT\Agents\Theology Agent\*" -Destination $THEO_DEST -Recurse -Force

    # Unpack SQLite database if tar.gz exists
    $DB_ARCHIVE = "$THEO_DEST\philology_db\biblical_corpus.db.tar.gz"
    $DB_FILE = "$THEO_DEST\philology_db\biblical_corpus.db"
    if ((Test-Path $DB_ARCHIVE) -and (-not (Test-Path $DB_FILE))) {
        Write-Host "   Unpacking biblical_corpus.db..." -ForegroundColor Cyan
        tar -xzf $DB_ARCHIVE -C "$THEO_DEST\philology_db"
    }
}

# Financial Coach
if ($INSTALL_FINANCE) {
    Write-Host "   Installing Financial Coach..." -ForegroundColor Green
    $FIN_DEST = Join-Path $AGENTS_DIR "Financial_Coach"
    New-Item -ItemType Directory -Path $FIN_DEST -Force | Out-Null
    Copy-Item -Path "$SCRIPT_ROOT\Agents\Financial_Coach\*" -Destination $FIN_DEST -Recurse -Force
}

# 8. Setup Python Virtual Environment
if (-not $skipVenvs) {
    Write-Host "🐍 Setting up Python Virtual Environment..." -ForegroundColor Cyan
    $SEARCH_DIR = "$AGENT0_DEST\mcp\obsidian_search"
    if (Test-Path $SEARCH_DIR) {
        $VENV_DIR = "$SEARCH_DIR\venv"
        if (-not (Test-Path $VENV_DIR)) {
            Write-Host "   Creating virtual environment in $VENV_DIR..." -ForegroundColor Cyan
            & $PYTHON_BIN -m venv $VENV_DIR
        }
        
        $VENV_PYTHON = "$VENV_DIR\Scripts\python.exe"
        if (Test-Path $VENV_PYTHON) {
            Write-Host "   Upgrading pip and installing requirements..." -ForegroundColor Cyan
            & $VENV_PYTHON -m pip install --upgrade pip --quiet
            if (Test-Path "$SEARCH_DIR\requirements.txt") {
                & $VENV_PYTHON -m pip install -r "$SEARCH_DIR\requirements.txt" --quiet
            }
            # Install parsing tools
            & $VENV_PYTHON -m pip install pymupdf python-pptx python-docx openpyxl python-dotenv --quiet
        }
    }
}

# 9. Configure .env file
$ENV_FILE = "$AGENT0_DEST\.env"
if (-not (Test-Path $ENV_FILE)) {
    Write-Host "📝 Creating initial .env configuration..." -ForegroundColor Cyan
    $DEFAULT_EMAIL = if ($email) { $email } else { "user@example.com" }
    $ENV_CONTENT = @"
USER_EMAIL=$DEFAULT_EMAIL
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GMAIL_APP_PASSWORD=
PERPLEXITY_API_KEY=
"@
    Set-Content -Path $ENV_FILE -Value $ENV_CONTENT -Force
}

# 10. Configure mcp_config.json with Clean Windows Paths
Write-Host "🔌 Generating MCP Configuration..." -ForegroundColor Cyan
$SERVER_PY_PATH = ("$AGENT0_DEST\mcp\obsidian_search\server.py").Replace('\', '/')
$VENV_PY_PATH   = ("$AGENT0_DEST\mcp\obsidian_search\venv\Scripts\python.exe").Replace('\', '/')

$MCP_JSON = @"
{
  "mcpServers": {
    "obsidian-search": {
      "command": "$VENV_PY_PATH",
      "args": [
        "$SERVER_PY_PATH"
      ]
    }
  }
}
"@
Set-Content -Path "$CONFIG_DIR\mcp_config.json" -Value $MCP_JSON -Force
Write-Host "✅ Wrote $CONFIG_DIR\mcp_config.json" -ForegroundColor Green

# 11. Create Course Folders & Second Brain Directories
$CLASS_DIR = if ($classes) { $classes } else { "$TARGET_HOME\Class_Folders" }
$VAULT_DIR = if ($vault) { $vault } else { "$TARGET_HOME\Second_Brain" }

New-Item -ItemType Directory -Path "$CLASS_DIR\Fall_2026" -Force | Out-Null
New-Item -ItemType Directory -Path "$VAULT_DIR\1-Inbox" -Force | Out-Null
New-Item -ItemType Directory -Path "$VAULT_DIR\2-Permanent-Notes" -Force | Out-Null
New-Item -ItemType Directory -Path "$VAULT_DIR\3-Archive" -Force | Out-Null

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "🎉 Setup Complete! Active Profile: $modules" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Add your GEMINI_API_KEY to $ENV_FILE" -ForegroundColor Yellow
Write-Host "2. Open Antigravity IDE and click File -> Open Folder -> $AGENT0_DEST" -ForegroundColor Yellow
Write-Host "3. Press Cmd+Shift+P (or Ctrl+Shift+P on Windows) and select 'Developer: Reload Window'" -ForegroundColor Yellow
