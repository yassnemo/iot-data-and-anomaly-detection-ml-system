#!/usr/bin/env pwsh
# Setup script - Install dependencies and prepare environment

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "IoT Anomaly Detection - Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check Docker
Write-Host "`nChecking Docker..." -ForegroundColor Yellow
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not installed. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Docker Compose
Write-Host "`nChecking Docker Compose..." -ForegroundColor Yellow
docker-compose --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Compose is not installed." -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host "`nCreating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data", "models", "models/anomaly_detector" | Out-Null

# Create .env file
Write-Host "`nCreating .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created from .env.example" -ForegroundColor Green
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

# Build Docker images
Write-Host "`nBuilding Docker images..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build Docker images" -ForegroundColor Red
    exit 1
}

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Run the demo: .\scripts\run_demo.ps1" -ForegroundColor White
Write-Host "2. Or start services manually: docker-compose up -d" -ForegroundColor White
Write-Host ""
