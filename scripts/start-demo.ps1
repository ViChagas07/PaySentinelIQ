<#
.SYNOPSIS
    PaySentinelIQ - Demo/Interview Launcher
    Starts everything needed for a smooth demo in ONE command.
#>

param(
    [switch]$UseMock = $true,
    [switch]$UseOllama = $false,
    [switch]$PullModel = $true,
    [switch]$SkipDocker = $false
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  PaySentinelIQ - Demo Launcher" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$envFile = "Back-end\.env"
$localEnv = "Back-end\.env.local"

if (-not (Test-Path $envFile) -or (Get-Content $envFile -Raw) -notmatch "DEMO_MODE") {
    Write-Host "Copiando .env.local -> .env..." -ForegroundColor Yellow
    Copy-Item $localEnv $envFile -Force
}

$demoMode = if ($UseMock) { "true" } else { "false" }
$scenario = "auto"
if ($UseMock -and $UseOllama) { $scenario = "high_risk" }

$content = Get-Content $envFile -Raw
$content = $content -replace 'DEMO_MODE=.*', "DEMO_MODE=$demoMode"
$content = $content -replace 'DEMO_SCENARIO=.*', "DEMO_SCENARIO=$scenario"
$content = $content -replace 'LLM_PROVIDER=.*', "LLM_PROVIDER=$(if ($UseMock) { 'mock' } else { 'ollama' })"
Set-Content $envFile $content -Encoding utf8

Write-Host "Config: LLM_PROVIDER=$(if ($UseMock) { 'mock (instant)' } else { 'ollama (real)' }), DEMO_MODE=$demoMode" -ForegroundColor Green

if (-not $SkipDocker) {
    Write-Host "Subindo infraestrutura (Postgres + Redis + Ollama)..." -ForegroundColor Yellow
    docker compose -f Back-end\docker\docker-compose.local.yml up -d --remove-orphans

    if ($PullModel -and -not $UseMock) {
        Write-Host "Baixando Qwen3 4B (pode demorar na primeira vez)..." -ForegroundColor Yellow
        docker compose -f Back-end\docker\docker-compose.local.yml exec ollama ollama pull qwen3:4b-q4_k_m
    }

    Write-Host "Aguardando servicos ficarem healthy..." -ForegroundColor Yellow
    Start-Sleep 15
}

Write-Host "Iniciando API (uvicorn + hot reload)..." -ForegroundColor Green
Set-Location Back-end
$env:PYTHONPATH = "$(Get-Location)\.."
python -m uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000