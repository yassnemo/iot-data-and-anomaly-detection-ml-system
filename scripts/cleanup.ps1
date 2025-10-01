#!/usr/bin/env pwsh
# Clean up all data and reset the system

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Cleanup Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$confirmation = Read-Host "`nThis will delete all data and volumes. Continue? (yes/no)"
if ($confirmation -ne 'yes') {
    Write-Host "Cleanup cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host "`nStopping and removing containers..." -ForegroundColor Yellow
docker-compose down -v

Write-Host "`nRemoving data directories..." -ForegroundColor Yellow
Remove-Item -Path "data/*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "models/anomaly_detector/*" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`nRecreating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data", "models/anomaly_detector" | Out-Null
New-Item -ItemType File -Force -Path "data/.gitkeep" | Out-Null

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "`nRun '.\scripts\setup.ps1' to reinitialize" -ForegroundColor Yellow
