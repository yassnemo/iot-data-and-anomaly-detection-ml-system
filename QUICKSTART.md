# Quick Start Guide

## Prerequisites

- Docker Desktop for Windows
- PowerShell 5.1 or higher
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

## Installation

1. Clone the repository:
```powershell
git clone https://github.com/yassnemo/iot-data-and-anomaly-detection-ml-system.git
cd iot-data-and-anomaly-detection-ml-system
```

2. Enable PowerShell script execution (if needed):
```powershell
# Check current policy
Get-ExecutionPolicy

# If Restricted, set to RemoteSigned for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Run setup:
```powershell
.\scripts\setup.ps1
```

## Running the Demo

Execute the end-to-end demo:
```powershell
.\scripts\run_demo.ps1
```

This will:
1. Start all services (Kafka, Spark, MinIO, TF-Serving, Prometheus, Grafana)
2. Generate synthetic training data
3. Train the LSTM Autoencoder model
4. Deploy the model to TF-Serving
5. Start the Spark streaming job
6. Start the producer (1000 sensors)
7. Show detected anomalies

## Manual Steps

### 1. Start Services
```powershell
docker-compose up -d
```

### 2. Train Model
```powershell
docker-compose exec trainer python src/training/train_model.py
```

### 3. Start Streaming Job
```powershell
docker-compose exec spark-master spark-submit `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 `
  --master spark://spark-master:7077 `
  /app/src/streaming/spark_streaming.py
```

### 4. Start Producer
```powershell
docker-compose exec producer python src/producer/kafka_producer.py --num-sensors 10000
```

### 5. Monitor Anomalies
```powershell
docker-compose exec kafka kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 `
  --topic anomalies
```

## Accessing Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |
| Spark UI | http://localhost:8080 | - |

## Running Tests

```powershell
# Unit tests only
docker-compose run --rm test python -m pytest tests/ -v

# Include integration tests
docker-compose run --rm test python -m pytest tests/ -v --integration
```

## Scaling

### Increase Kafka Partitions
```powershell
docker-compose exec kafka kafka-topics.sh --alter `
  --bootstrap-server localhost:9092 `
  --topic raw-readings `
  --partitions 20
```

### Scale Spark Workers
```powershell
docker-compose up -d --scale spark-worker=3
```

### Increase Sensors
```powershell
docker-compose exec producer python src/producer/kafka_producer.py --num-sensors 20000
```

## Troubleshooting

### PowerShell Script Execution Error
If you get "scripts is disabled on this system" error:
```powershell
# Option 1: Run with bypass (one-time)
PowerShell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# Option 2: Change policy for current user (permanent)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Check Service Logs
```powershell
docker-compose logs -f [service-name]
```

### Restart a Service
```powershell
docker-compose restart [service-name]
```

### Reset Everything
```powershell
docker-compose down -v
.\scripts\setup.ps1
```

## Performance Tuning

See [README.md](README.md) for detailed tuning guide to achieve 95% detection accuracy.
