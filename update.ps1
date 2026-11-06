# ==============================================================================
# update.ps1 — Windows PowerShell State-Preserving Agent Updater
# ==============================================================================
param(
    [string]$homeDir = $env:USERPROFILE
)

$ErrorActionPreference = "Stop"

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🔄 Updating Multi-Agent Infrastructure (Windows)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

$TARGET_HOME = $homeDir
$AGENTS_DIR  = Join-Path $TARGET_HOME "Agents"
$CONFIG_DIR  = Join-Path $TARGET_HOME ".gemini\config"
$RULES_DIR   = Join-Path $CONFIG_DIR "rules"
$SKILLS_DIR  = Join-Path $CONFIG_DIR "skills"

$SCRIPT_ROOT = $PSScriptRoot
if (-not $SCRIPT_ROOT) { $SCRIPT_ROOT = (Get-Location).Path }

# 1. Pull Latest Upstream Code
Write-Host "📥 Pulling latest updates from GitHub..." -ForegroundColor Cyan
Set-Location $SCRIPT_ROOT
git pull origin main

# 2. Read Active Profile
$PROFILE_FILE = Join-Path $TARGET_HOME ".agents_profile"
$modules = "academic"
if (Test-Path $PROFILE_FILE) {
    $modules = (Get-Content -Path $PROFILE_FILE -Raw).Trim()
}
Write-Host "📋 Active Profile: $modules" -ForegroundColor Cyan

$INSTALL_ACADEMIC = ($modules -match "academic")
$INSTALL_THEOLOGY = ($modules -match "theology")
$INSTALL_FINANCE  = ($modules -match "finance")

# 3. Update Rules & Skills
Write-Host "⚙️  Updating Global Rules & Custom Skills..." -ForegroundColor Cyan
if (Test-Path "$SCRIPT_ROOT\gemini_config\rules") {
    Copy-Item -Path "$SCRIPT_ROOT\gemini_config\rules\*" -Destination $RULES_DIR -Recurse -Force
}
if (Test-Path "$SCRIPT_ROOT\gemini_config\skills") {
    Copy-Item -Path "$SCRIPT_ROOT\gemini_config\skills\*" -Destination $SKILLS_DIR -Recurse -Force
}

# 4. State-Preserving Workspace Update
# Helper function to copy files without overwriting user state (.env, context.md, memory.md)
function Update-WorkspacePreservingState {
    param([string]$src, [string]$dst)
    if (-not (Test-Path $src)) { return }
    if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
    
    Get-ChildItem -Path $src -Recurse | ForEach-Object {
        $relPath = $_.FullName.Substring($src.Length).TrimStart('\', '/')
        $targetFile = Join-Path $dst $relPath
        
        # Protected files that must NEVER be overwritten on update
        if ($relPath -match '(\.env|context\.md|memory\.md|learnings\.md|trading_journal\.md|study_log\.md)$') {
            if (Test-Path $targetFile) {
                return # Preserve existing user state
            }
        }
        
        if ($_.PSIsContainer) {
            if (-not (Test-Path $targetFile)) { New-Item -ItemType Directory -Path $targetFile -Force | Out-Null }
        } else {
            Copy-Item -Path $_.FullName -Destination $targetFile -Force
        }
    }
}

Write-Host "📦 Updating Installed Workspaces..." -ForegroundColor Cyan
Update-WorkspacePreservingState -src "$SCRIPT_ROOT\Agents\Agent 0" -dst "$AGENTS_DIR\Agent 0"

if ($INSTALL_ACADEMIC) {
    Write-Host "   Updating Academic Tutor..." -ForegroundColor Green
    Update-WorkspacePreservingState -src "$SCRIPT_ROOT\Agents\Academic Tutor" -dst "$AGENTS_DIR\Academic Tutor"
}

if ($INSTALL_THEOLOGY) {
    Write-Host "   Updating Theology Agent..." -ForegroundColor Green
    Update-WorkspacePreservingState -src "$SCRIPT_ROOT\Agents\Theology Agent" -dst "$AGENTS_DIR\Theology Agent"
}

if ($INSTALL_FINANCE) {
    Write-Host "   Updating Financial Coach..." -ForegroundColor Green
    Update-WorkspacePreservingState -src "$SCRIPT_ROOT\Agents\Financial_Coach" -dst "$AGENTS_DIR\Financial_Coach"
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "✅ Update Complete! All personal notes and .env settings preserved." -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
