#!/usr/bin/env pwsh
# Monitor system status and metrics

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "System Status Monitor" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if services are running
Write-Host "`nDocker Services:" -ForegroundColor Yellow
docker-compose ps

# Check Kafka topics
Write-Host "`n`nKafka Topics:" -ForegroundColor Yellow
docker-compose exec -T kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Check topic details
Write-Host "`n`nRaw Readings Topic:" -ForegroundColor Yellow
docker-compose exec -T kafka kafka-topics.sh --describe --bootstrap-server localhost:9092 --topic raw-readings

Write-Host "`n`nAnomalies Topic:" -ForegroundColor Yellow
docker-compose exec -T kafka kafka-topics.sh --describe --bootstrap-server localhost:9092 --topic anomalies

# Check consumer groups
Write-Host "`n`nConsumer Groups:" -ForegroundColor Yellow
docker-compose exec -T kafka kafka-consumer-groups.sh --list --bootstrap-server localhost:9092

# Check MinIO buckets
Write-Host "`n`nMinIO Buckets:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:9000/minio/health/live" -Method Get
    Write-Host "MinIO is healthy" -ForegroundColor Green
}
catch {
    Write-Host "MinIO is not responding" -ForegroundColor Red
}

# Check TF-Serving models
Write-Host "`n`nTF-Serving Models:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8501/v1/models/anomaly_detector" -Method Get
    Write-Host "Model Status: $($response.model_version_status[0].state)" -ForegroundColor Green
}
catch {
    Write-Host "TF-Serving is not responding" -ForegroundColor Red
}

# Check Spark jobs
Write-Host "`n`nSpark Master UI: http://localhost:8080" -ForegroundColor Yellow
Write-Host "Grafana Dashboard: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Prometheus: http://localhost:9090" -ForegroundColor Yellow

Write-Host "`n=====================================" -ForegroundColor Cyan
