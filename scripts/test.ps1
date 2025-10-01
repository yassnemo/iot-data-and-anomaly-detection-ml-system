#!/usr/bin/env pwsh
# Test script - Run all tests

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Running Tests" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`n[1] Running unit tests..." -ForegroundColor Yellow
docker-compose run --rm test python -m pytest tests/ -v -m "not integration"

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nUnit tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2] Running integration tests..." -ForegroundColor Yellow
docker-compose run --rm test python -m pytest tests/ -v --integration

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nIntegration tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "All tests passed!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
