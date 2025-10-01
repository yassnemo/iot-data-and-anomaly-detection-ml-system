# System Design

## Architecture Overview

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   10,000+   │──────▶│    Kafka    │──────▶│    Spark    │
│   Sensors   │       │  (KRaft)    │       │  Streaming  │
│  Simulator  │       │             │       │             │
└─────────────┘       └─────────────┘       └──────┬──────┘
                                                    │
                                                    ▼
                            ┌──────────────────────┴────────────────────┐
                            │                                            │
                            ▼                                            ▼
                     ┌──────────────┐                            ┌──────────────┐
                     │  TF-Serving  │                            │    MinIO     │
                     │   (Model)    │                            │  (Storage)   │
                     └──────┬───────┘                            └──────────────┘
                            │
                            ▼
                     ┌──────────────┐       ┌──────────────┐
                     │    Kafka     │──────▶│  Prometheus  │
                     │  (Anomalies) │       │   Grafana    │
                     └──────────────┘       └──────────────┘
```

## Data Flow

1. **Ingestion**: Async producer simulates 10K+ sensors sending readings to Kafka `raw-readings` topic
2. **Processing**: Spark Structured Streaming reads from Kafka, performs windowed aggregation
3. **Feature Engineering**: Extract statistical features (mean, stddev, min, max, count, range)
4. **Inference**: Call TF-Serving REST API for anomaly scoring using LSTM Autoencoder
5. **Output**: 
   - Anomalies → Kafka `anomalies` topic
   - Features + Scores → MinIO (Parquet)
6. **Monitoring**: Prometheus scrapes metrics, Grafana visualizes dashboards

## Components

### Producer (Async Kafka)
- Language: Python 3.10+ with aiokafka
- Simulates N sensors (configurable, default 10,000)
- Generates time-series JSON messages
- Injects synthetic anomalies (spike, drift, stuck, noise)
- Target: 1 msg/sec per sensor = 10K msg/sec total

### Kafka (KRaft Mode)
- Version: 3.6.0 (no Zookeeper dependency)
- Topics:
  - `raw-readings`: 10 partitions, replication factor 1
  - `anomalies`: 3 partitions, replication factor 1
- Compression: gzip

### Spark Structured Streaming
- Version: 3.4.1 (PySpark)
- Sliding window: 60s window, 10s slide
- Features extracted per sensor per window
- Checkpointing enabled for fault tolerance
- Writes to MinIO using S3A connector

### TensorFlow Model (LSTM Autoencoder)
- Input: 6 features (mean, stddev, min, max, count, range)
- Architecture: Encoder-Decoder with LSTM layers
- Training: On synthetic data with labeled anomalies
- Evaluation: ROC-AUC, PR-AUC, Precision, Recall, F1
- Threshold: Configurable (default 95th percentile)

### TF-Serving
- Version: 2.14.0
- REST API on port 8501
- Serves SavedModel format
- Batched inference for efficiency

### MinIO
- S3-compatible object storage
- Buckets: `iot-data`, `models`
- Stores: Parquet files (features + scores)

### Monitoring
- Prometheus: Metrics collection
- Grafana: Dashboard visualization
- Metrics: events/sec, latency, anomalies/sec, model metrics

## Scaling Considerations

### Horizontal Scaling
- **Kafka**: Increase partitions (10 → 20+)
- **Spark**: Add worker nodes (1 → 3+)
- **Producer**: Deploy multiple instances

### Vertical Scaling
- **Spark Workers**: Increase cores (4 → 8) and memory (4G → 8G)
- **TF-Serving**: Use GPU for faster inference

### Optimization
- **Batch Size**: Tune Spark micro-batch size
- **Window Size**: Adjust feature extraction window
- **Model Complexity**: Balance accuracy vs latency

## Fault Tolerance

- **Kafka**: Persistent logs with configurable retention
- **Spark**: Checkpointing to HDFS/S3
- **MinIO**: Distributed storage (erasure coding in production)
- **TF-Serving**: Stateless, can restart without data loss

## Security (Production)

- **Kafka**: SASL/SSL authentication
- **MinIO**: IAM policies, encryption at rest
- **TF-Serving**: Token-based authentication
- **Network**: Private VPC, security groups

## Performance Targets

- **Throughput**: 10K events/sec sustained
- **Latency**: End-to-end < 1 second (p95)
- **Accuracy**: 95% detection rate
- **Uptime**: 99.9% availability
