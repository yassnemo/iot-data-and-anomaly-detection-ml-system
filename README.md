# Real-Time IoT Anomaly Detection System

A production-ready system for detecting anomalies in 10,000+ IoT sensors using Apache Kafka, Spark Structured Streaming, TensorFlow, and MinIO.

## Architecture

- **Data Ingestion**: Async Kafka producer simulating 10K sensors @ 1 msg/sec
- **Stream Processing**: Spark Structured Streaming with sliding window feature extraction
- **ML Model**: LSTM Autoencoder for anomaly detection
- **Storage**: MinIO for features/scores (Parquet)
- **Serving**: TensorFlow Serving for real-time inference
- **Monitoring**: Prometheus + Grafana for metrics

## Quick Start (Docker Compose)

```powershell
# 1. Start all services
docker-compose up -d

# 2. Wait for services to be ready (~30 seconds)
Start-Sleep -Seconds 30

# 3. Generate synthetic training data
docker-compose exec producer python scripts/generate_training_data.py

# 4. Train the model
docker-compose exec trainer python src/training/train_model.py

# 5. Start Spark streaming job
docker-compose exec spark-master spark-submit `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 `
  --master spark://spark-master:7077 `
  /app/src/streaming/spark_streaming.py

# 6. Start producer (10K sensors)
docker-compose exec producer python src/producer/kafka_producer.py --num-sensors 10000

# 7. Monitor anomalies
docker-compose exec kafka kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 `
  --topic anomalies `
  --from-beginning
```

## Access Services

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Spark UI**: http://localhost:8080

## Kubernetes (k3s) Deployment

```powershell
# 1. Install k3s (Windows: use WSL2)
# Follow: https://docs.k3s.io/installation

# 2. Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/minio.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/spark.yaml
kubectl apply -f k8s/tfserving.yaml
kubectl apply -f k8s/monitoring.yaml
kubectl apply -f k8s/producer.yaml

# 3. Port forward services
kubectl port-forward -n iot-anomaly svc/grafana 3000:3000
kubectl port-forward -n iot-anomaly svc/minio-console 9001:9001
```

## Scaling Guide

### Kafka Partitions
```powershell
# Increase partitions for raw-readings topic (default: 10)
docker-compose exec kafka kafka-topics.sh --alter `
  --bootstrap-server localhost:9092 `
  --topic raw-readings `
  --partitions 20
```

### Spark Executors
Edit `docker-compose.yml`:
```yaml
spark-worker:
  environment:
    - SPARK_WORKER_CORES=4
    - SPARK_WORKER_MEMORY=8G
  deploy:
    replicas: 3
```

### Producer Throughput
```powershell
# Adjust batch size and sensors per instance
docker-compose exec producer python src/producer/kafka_producer.py `
  --num-sensors 20000 `
  --batch-size 200
```

## Tuning for 95% Detection

1. **Data Quality**: Ensure training data includes diverse anomaly patterns
2. **Model Hyperparameters**:
   - `lstm_units`: 128-256
   - `sequence_length`: 50-100
   - `threshold_percentile`: 95-99
3. **Feature Engineering**: Adjust window size (T=60s) and slide (S=10s)
4. **Training**: Use more epochs (50-100) with early stopping

## Configuration

### Environment Variables

Create `.env` file:
```env
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
TFSERVING_URL=http://tfserving:8501
NUM_SENSORS=10000
ANOMALY_THRESHOLD=0.95
WINDOW_DURATION=60s
SLIDE_DURATION=10s
```

### Model Parameters

Edit `src/training/config.py`:
```python
LSTM_UNITS = 128
SEQUENCE_LENGTH = 50
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 0.001
```

## Testing

```powershell
# Run unit tests
docker-compose run --rm test python -m pytest tests/ -v

# Run integration test
.\scripts\run_demo.ps1
```

## Monitoring Metrics

- **events_processed_total**: Total events processed
- **anomalies_detected_total**: Total anomalies detected
- **processing_latency_seconds**: End-to-end latency
- **model_precision**: Precision score
- **model_recall**: Recall score
- **kafka_consumer_lag**: Consumer lag

## Troubleshooting

### Kafka Connection Issues
```powershell
# Check Kafka broker
docker-compose logs kafka
# Verify topics
docker-compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Spark Job Failures
```powershell
# Check Spark logs
docker-compose logs spark-master spark-worker
# Verify checkpoint directory
docker-compose exec spark-master ls -la /tmp/spark-checkpoints
```

### Model Not Loading
```powershell
# Verify model exists
docker-compose exec tfserving ls -la /models/anomaly_detector/1
# Check TF-Serving logs
docker-compose logs tfserving
```

## Project Structure

```
.
├── src/
│   ├── producer/          # Kafka producer (sensor simulator)
│   ├── streaming/         # Spark Structured Streaming job
│   ├── training/          # TensorFlow model training
│   └── common/            # Shared utilities
├── tests/                 # Unit and integration tests
├── scripts/               # Helper scripts
├── k8s/                   # Kubernetes manifests
├── monitoring/            # Prometheus & Grafana configs
├── docker-compose.yml     # Docker Compose configuration
└── requirements.txt       # Python dependencies
```

## License

MIT
