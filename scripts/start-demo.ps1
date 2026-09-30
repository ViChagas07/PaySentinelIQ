<#
.SYNOPSIS
    PaySentinelIQ - Demo/Interview Launcher
    Uses ENVIRONMENT variable to auto-configure everything.
#>

param(
    [ValidateSet("demo", "development", "production")]
    [string]$Environment = "demo",   # demo = mock (instant), development = Ollama Qwen3 4B
    [switch]$PullModel = $true,      # Download Qwen3 4B if missing
    [switch]$SkipDocker = $false     # Run services manually
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  PaySentinelIQ - Launcher" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Mode: $Environment" -ForegroundColor Yellow

# 1. Copy appropriate .env
$envFile = "Back-end\.env"
$localEnv = "Back-end\.env.local"
if ($Environment -eq "production") {
    # Production uses the existing .env (already configured)
    Write-Host "Using existing .env (production config)" -ForegroundColor Green
} else {
    Write-Host "Copiando .env.local -> .env..." -ForegroundColor Yellow
    Copy-Item $localEnv $envFile -Force
    
    # Override ENVIRONMENT if different from .env.local
    if ($Environment -ne "demo") {
        $content = Get-Content $envFile -Raw
        $content = $content -replace 'ENVIRONMENT=.*', "ENVIRONMENT=$Environment"
        Set-Content $envFile $content -Encoding utf8
    }
}

# 2. Start infrastructure
if (-not $SkipDocker) {
    $profile = switch ($Environment) {
        "demo" { "demo" }
        "development" { "local" }
        "production" { "production" }
        default { "local" }
    }
    
    Write-Host "🐳 Subindo infraestrutura (profile: $profile)..." -ForegroundColor Yellow
    docker compose -f Back-end\docker\docker-compose.yml --profile $profile up -d --remove-orphans

    if ($PullModel -and $Environment -in @("demo", "development")) {
        Write-Host "⬇️  Baixando Qwen3 4B (pode demorar na primeira vez)..." -ForegroundColor Yellow
        docker compose -f Back-end\docker\docker-compose.yml exec ollama ollama pull qwen3:4b-q4_k_m
    }

    Write-Host "⏳ Aguardando serviços..." -ForegroundColor Yellow
    Start-Sleep 10
}

# 3. Start API
Write-Host "🚀 Iniciando API..." -ForegroundColor Green
Set-Location Back-end
$env:PYTHONPATH = "$(Get-Location)\.."
$target = if ($Environment -in @("demo", "development")) { "development" } else { "production" }
$env:DOCKER_TARGET = $target
python -m uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000