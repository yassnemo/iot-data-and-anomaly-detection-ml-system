"""
Prometheus metrics exporter for monitoring
"""
import time
from prometheus_client import Counter, Histogram, Gauge, start_http_server


# Define metrics
events_processed = Counter(
    'events_processed_total',
    'Total number of events processed',
    ['status']
)

anomalies_detected = Counter(
    'anomalies_detected_total',
    'Total number of anomalies detected'
)

processing_latency = Histogram(
    'processing_latency_seconds',
    'Time spent processing events',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

model_precision = Gauge(
    'model_precision',
    'Model precision score'
)

model_recall = Gauge(
    'model_recall',
    'Model recall score'
)

kafka_consumer_lag = Gauge(
    'kafka_consumer_lag',
    'Kafka consumer lag',
    ['topic', 'partition']
)


class MetricsExporter:
    """Metrics exporter for Prometheus"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        
    def start(self):
        """Start metrics HTTP server"""
        start_http_server(self.port)
        print(f"Metrics server started on port {self.port}")
        
    @staticmethod
    def record_event(status: str = 'success'):
        """Record an event"""
        events_processed.labels(status=status).inc()
        
    @staticmethod
    def record_anomaly():
        """Record an anomaly detection"""
        anomalies_detected.inc()
        
    @staticmethod
    def record_latency(duration: float):
        """Record processing latency"""
        processing_latency.observe(duration)
        
    @staticmethod
    def update_model_metrics(precision: float, recall: float):
        """Update model performance metrics"""
        model_precision.set(precision)
        model_recall.set(recall)
        
    @staticmethod
    def update_consumer_lag(topic: str, partition: int, lag: int):
        """Update Kafka consumer lag"""
        kafka_consumer_lag.labels(topic=topic, partition=partition).set(lag)


if __name__ == '__main__':
    # Start metrics exporter
    exporter = MetricsExporter()
    exporter.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down metrics exporter...")
