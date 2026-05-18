# setup.ps1 - First-time setup for memclaw-cross-fleet-gov (Windows)
# Run once from the repo root in an elevated PowerShell session (Run as Administrator).
# After this script completes, day-to-day use is just: openclaw gateway restart

$ErrorActionPreference = "Stop"
$REPO = $PSScriptRoot

function Write-Step { param($msg) Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "   OK: $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "   WARN: $msg" -ForegroundColor Yellow }

Write-Host "`nMemClaw Cross-Fleet Gov - Setup" -ForegroundColor White
Write-Host "Repo: $REPO"

# ── 1. Prerequisites ──────────────────────────────────────────────────────────

Write-Step "Checking prerequisites"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker not found. Install Docker Desktop and try again."
}
Write-OK "Docker found"

if (-not (Get-Command openclaw -ErrorAction SilentlyContinue)) {
    throw "OpenClaw not found. Run: npm install -g openclaw@latest"
}
Write-OK "OpenClaw found: $(openclaw --version 2>$null)"

# ── 2. .env ───────────────────────────────────────────────────────────────────

Write-Step "Environment file"

if (-not (Test-Path "$REPO\.env")) {
    Copy-Item "$REPO\.env.example" "$REPO\.env"
    Write-Warn ".env created from .env.example - open it and fill in LLM_GATEWAY_API_KEY before starting the gateway"
} else {
    Write-OK ".env already exists"
}

# ── 3. MemClaw Docker ─────────────────────────────────────────────────────────

Write-Step "Starting MemClaw (Docker)"

$running = docker ps --filter "name=memclaw" --format "{{.Names}}" 2>$null
if ($running -match "memclaw") {
    Write-OK "MemClaw container already running"
} else {
    $exists = docker ps -a --filter "name=^memclaw$" --format "{{.Names}}" 2>$null
    if ($exists -eq "memclaw") {
        docker start memclaw | Out-Null
        Write-OK "MemClaw container restarted"
    } else {
        docker run -d --name memclaw -p 8000:8000 ghcr.io/caura-ai/caura-memclaw:latest | Out-Null
        Write-OK "MemClaw container started on http://localhost:8000"
    }
}

# Wait for MemClaw to be ready
Write-Host "   Waiting for MemClaw to be ready..." -NoNewline
$attempts = 0
$ready = $false
while ($attempts -lt 20 -and -not $ready) {
    Start-Sleep -Seconds 2
    $attempts++
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) { $ready = $true }
    } catch {}
    Write-Host "." -NoNewline
}
Write-Host ""
if (-not $ready) {
    throw "MemClaw did not become ready after 40s. Check: docker logs memclaw"
}
Write-OK "MemClaw is ready at http://localhost:8000"

# ── 4. Agent workspace junctions ─────────────────────────────────────────────

Write-Step "Creating workspace junctions in ~/.openclaw"

$openclawHome = "$HOME\.openclaw"
if (-not (Test-Path $openclawHome)) {
    New-Item -ItemType Directory -Force $openclawHome | Out-Null
}

foreach ($agent in @("sales-agent", "legal-agent", "admin-agent")) {
    $junctionPath = "$openclawHome\workspace-$agent"
    $targetPath   = "$REPO\agents\$agent"

    if (-not (Test-Path $targetPath)) {
        throw "Agent directory not found: $targetPath"
    }

    if (Test-Path $junctionPath) {
        # If it exists but points somewhere wrong, remove and recreate
        $existing = (Get-Item $junctionPath).Target
        if ($existing -ne $targetPath) {
            Remove-Item $junctionPath -Force
            New-Item -ItemType Junction -Path $junctionPath -Target $targetPath | Out-Null
            Write-OK "Junction recreated: $junctionPath -> $targetPath"
        } else {
            Write-OK "Junction already correct: workspace-$agent"
        }
    } else {
        New-Item -ItemType Junction -Path $junctionPath -Target $targetPath | Out-Null
        Write-OK "Junction created: workspace-$agent"
    }
}

# ── 5. Governance skill ───────────────────────────────────────────────────────

Write-Step "Copying governance skill into agent workspaces"

$skillSrc = "$REPO\skills\memclaw-governance.md"
foreach ($agent in @("sales-agent", "legal-agent", "admin-agent")) {
    $skillDir = "$REPO\agents\$agent\skills"
    New-Item -ItemType Directory -Force $skillDir | Out-Null
    Copy-Item $skillSrc "$skillDir\memclaw-governance.md" -Force
    Write-OK "Skill copied to agents/$agent/skills/"
}

# ── 6. Register agents ────────────────────────────────────────────────────────

Write-Step "Registering agents with OpenClaw"

foreach ($agent in @("sales-agent", "legal-agent", "admin-agent")) {
    $workspace = "$openclawHome\workspace-$agent"
    try {
        openclaw agents add $agent --workspace $workspace --non-interactive 2>$null
        Write-OK "Registered: $agent"
    } catch {
        Write-Warn "$agent may already be registered (run 'openclaw agents list' to confirm)"
    }
}

# ── 7. Install MemClaw plugin ─────────────────────────────────────────────────

Write-Step "Installing MemClaw plugin"

$fleets = @(
    @{ fleet = "fleet-org-shared"; label = "shared" },
    @{ fleet = "fleet-sales";      label = "sales"  },
    @{ fleet = "fleet-legal";      label = "legal"  }
)

foreach ($f in $fleets) {
    try {
        $url = "http://localhost:8000/api/v1/install-plugin?fleet_id=$($f.fleet)&api_url=http://localhost:8000"
        $script = Invoke-RestMethod $url
        Invoke-Expression $script
        Write-OK "Plugin installed for $($f.fleet)"
    } catch {
        Write-Warn "Plugin install for $($f.fleet) failed or already installed: $_"
    }
}

# ── 8. Start gateway ──────────────────────────────────────────────────────────

Write-Step "Starting OpenClaw gateway"

openclaw gateway restart
Start-Sleep -Seconds 3

Write-Step "Verifying agent bindings"
openclaw agents list --bindings

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host @"

Setup complete.

Next steps:
  1. Open .env and set your LLM gateway key
     -- or set LLM_GATEWAY_BASE_URL=http://localhost:11434/v1 and LLM_GATEWAY_API_KEY=ollama for Ollama
  2. Run: openclaw gateway restart   (after saving .env)
  3. Run: openclaw dashboard         (opens http://127.0.0.1:18789)
  4. Follow the Governance Validation steps in README.md

"@ -ForegroundColor Green
