#!/usr/bin/env pwsh
# End-to-End Demo Script for Windows PowerShell

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "IoT Anomaly Detection - E2E Demo" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Function to check if service is ready
function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxRetries = 30
    )
    
    Write-Host "`nWaiting for $ServiceName to be ready..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "$ServiceName is ready!" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Write-Host "Attempt $i/$MaxRetries..." -NoNewline
            Start-Sleep -Seconds 2
        }
    }
    
    Write-Host "`n$ServiceName failed to start" -ForegroundColor Red
    return $false
}

# Step 1: Start Docker Compose
Write-Host "`n[Step 1] Starting Docker Compose services..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start Docker Compose" -ForegroundColor Red
    exit 1
}

# Step 2: Wait for services
Write-Host "`n[Step 2] Waiting for services to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Wait-ForService "Kafka" "http://localhost:9092" | Out-Null
Wait-ForService "MinIO" "http://localhost:9000/minio/health/live" | Out-Null
Wait-ForService "Prometheus" "http://localhost:9090/-/healthy" | Out-Null
Wait-ForService "Grafana" "http://localhost:3000/api/health" | Out-Null

# Step 3: Create Kafka topics
Write-Host "`n[Step 3] Creating Kafka topics..." -ForegroundColor Cyan
docker-compose exec -T kafka kafka-topics.sh --create `
    --bootstrap-server localhost:9092 `
    --topic raw-readings `
    --partitions 10 `
    --replication-factor 1 `
    --if-not-exists

docker-compose exec -T kafka kafka-topics.sh --create `
    --bootstrap-server localhost:9092 `
    --topic anomalies `
    --partitions 3 `
    --replication-factor 1 `
    --if-not-exists

# Step 4: Generate training data
Write-Host "`n[Step 4] Generating synthetic training data..." -ForegroundColor Cyan
docker-compose exec -T producer python scripts/generate_training_data.py --samples 10000

# Step 5: Train model
Write-Host "`n[Step 5] Training LSTM Autoencoder model..." -ForegroundColor Cyan
docker-compose exec -T trainer python src/training/train_model.py

# Step 6: Wait for TF-Serving
Write-Host "`n[Step 6] Waiting for TF-Serving to load model..." -ForegroundColor Cyan
Start-Sleep -Seconds 10
Wait-ForService "TF-Serving" "http://localhost:8501/v1/models/anomaly_detector" | Out-Null

# Step 7: Start Spark Streaming (background)
Write-Host "`n[Step 7] Starting Spark Streaming job..." -ForegroundColor Cyan
Start-Job -ScriptBlock {
    docker-compose exec spark-master spark-submit `
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 `
        --master spark://spark-master:7077 `
        --executor-memory 2G `
        --total-executor-cores 2 `
        /app/src/streaming/spark_streaming.py
} | Out-Null

Write-Host "Spark job started in background" -ForegroundColor Green
Start-Sleep -Seconds 10

# Step 8: Start producer with 1000 sensors (for demo)
Write-Host "`n[Step 8] Starting sensor data producer (1000 sensors)..." -ForegroundColor Cyan
Write-Host "Producer will run for 60 seconds..." -ForegroundColor Yellow

$producerJob = Start-Job -ScriptBlock {
    docker-compose exec producer python src/producer/kafka_producer.py --num-sensors 1000 --messages-per-second 1
}

Start-Sleep -Seconds 30

# Step 9: Monitor anomalies
Write-Host "`n[Step 9] Monitoring anomalies (showing last 10)..." -ForegroundColor Cyan
docker-compose exec -T kafka kafka-console-consumer.sh `
    --bootstrap-server localhost:9092 `
    --topic anomalies `
    --from-beginning `
    --max-messages 10

# Cleanup
Write-Host "`nStopping producer..." -ForegroundColor Yellow
Stop-Job $producerJob -ErrorAction SilentlyContinue
Remove-Job $producerJob -ErrorAction SilentlyContinue

# Step 10: Show URLs
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "Demo Complete! Access the following:" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Grafana Dashboard:  http://localhost:3000 (admin/admin)" -ForegroundColor Green
Write-Host "Prometheus:         http://localhost:9090" -ForegroundColor Green
Write-Host "MinIO Console:      http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor Green
Write-Host "Spark UI:           http://localhost:8080" -ForegroundColor Green
Write-Host ""
Write-Host "To view continuous anomalies, run:" -ForegroundColor Yellow
Write-Host "docker-compose exec kafka kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic anomalies" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "docker-compose down" -ForegroundColor White
Write-Host ""
