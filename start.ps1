<#
.SYNOPSIS
    Launcher script for Multi-Agent Sandbox Compiler & Debugger
    Starts FastAPI backend (port 8000) and React Vite frontend (port 5173).
#>

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Multi-Agent Sandbox Compiler & Debugger" -ForegroundColor Green
Write-Host "  FastAPI + React 19 + Monaco + Ollama Multi-Agent Platform" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Ensure Node & Python exist
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js / npm is not installed or not in PATH."
    exit 1
}

# Start Backend Process
Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload" `
    -WorkingDirectory $BackendDir `
    -PassThru

# Start Frontend Process
Write-Host "[2/2] Starting Vite Dev Server on http://localhost:5173 ..." -ForegroundColor Yellow
$FrontendProcess = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173" `
    -WorkingDirectory $FrontendDir `
    -PassThru

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Services are now running:" -ForegroundColor Green
Write-Host "  Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press [Ctrl+C] to stop all servers." -ForegroundColor DarkGray

try {
    # Keep the parent process waiting until Ctrl+C
    while ($true) {
        if ($BackendProcess.HasExited) {
            Write-Warning "FastAPI backend process exited unexpectedly."
            break
        }
        if ($FrontendProcess.HasExited) {
            Write-Warning "Vite frontend process exited unexpectedly."
            break
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "All processes stopped cleanly." -ForegroundColor Green
}
