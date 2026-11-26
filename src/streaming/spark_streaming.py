"""
Spark Structured Streaming Job
Reads from Kafka, performs windowed feature extraction, inference, and writes to MinIO/Kafka
"""
import logging
import os
import sys
import json
from typing import Iterator, Optional
import requests
import numpy as np

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    abs as spark_abs,
    avg,
    col,
    count,
    current_timestamp,
    from_json,
    isnan,
    lit,
    max as spark_max,
    min as spark_min,
    stddev,
    struct,
    sum as spark_sum,
    to_json,
    when,
    window,
    udf,
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType, 
    BooleanType, MapType, ArrayType
)
from pyspark.sql.streaming import StreamingQueryListener
from pyspark.sql.streaming.listener import (
    QueryProgressEvent,
    QueryStartedEvent,
    QueryTerminatedEvent,
)


logger = logging.getLogger(__name__)
KAFKA_VALIDATION_OBSERVATION = "kafka_reading_validation"


class _KafkaValidationListener(StreamingQueryListener):
    """Log rejected Kafka readings by reason for each streaming trigger."""

    def onQueryStarted(self, event: QueryStartedEvent) -> None:
        pass

    def onQueryProgress(self, event: QueryProgressEvent) -> None:
        metrics = event.progress.observedMetrics.get(KAFKA_VALIDATION_OBSERVATION)
        if metrics is None:
            return

        counts = metrics.asDict()
        if any(counts.values()):
            logger.warning(
                "Rejected Kafka readings in batch %s by reason: %s",
                event.progress.batchId,
                counts,
            )

    def onQueryTerminated(self, event: QueryTerminatedEvent) -> None:
        pass


# Schema for raw Kafka messages
RAW_SCHEMA = StructType([
    StructField('sensor_id', StringType(), False),
    StructField('timestamp', StringType(), False),
    StructField('metric', StringType(), False),
    StructField('value', DoubleType(), False),
    StructField('meta', MapType(StringType(), StringType()), True)
])


class SparkStreamingJob:
    """Spark Structured Streaming job for anomaly detection"""
    
    def __init__(self):
        self.kafka_bootstrap = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        self.kafka_raw_topic = os.getenv('KAFKA_RAW_TOPIC', 'raw-readings')
        self.kafka_anomaly_topic = os.getenv('KAFKA_ANOMALY_TOPIC', 'anomalies')
        self.minio_endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        self.minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.minio_bucket = os.getenv('MINIO_BUCKET', 'iot-data')
        self.tfserving_url = os.getenv('TFSERVING_URL', 'http://tfserving:8501')
        self.model_name = os.getenv('MODEL_NAME', 'anomaly_detector')
        self.window_duration = os.getenv('WINDOW_DURATION', '60 seconds')
        self.slide_duration = os.getenv('SLIDE_DURATION', '10 seconds')
        self.checkpoint_location = os.getenv('CHECKPOINT_LOCATION', '/tmp/spark-checkpoints')
        self.anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', '0.95'))
        
        self.spark = None
        self._validation_listener: Optional[_KafkaValidationListener] = None
        
    def create_spark_session(self):
        """Create Spark session with required configurations"""
        self.spark = SparkSession.builder \
            .appName("IoT-Anomaly-Detection-Streaming") \
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_location) \
            .config("spark.hadoop.fs.s3a.endpoint", f"http://{self.minio_endpoint}") \
            .config("spark.hadoop.fs.s3a.access.key", self.minio_access_key) \
            .config("spark.hadoop.fs.s3a.secret.key", self.minio_secret_key) \
            .config("spark.hadoop.fs.s3a.path.style.access", "true") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        if self._validation_listener is None:
            self._validation_listener = _KafkaValidationListener()
            self.spark.streams.addListener(self._validation_listener)
        print("Spark session created successfully")
        
    def read_kafka_stream(self):
        """Read streaming data from Kafka"""
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_bootstrap) \
            .option("subscribe", self.kafka_raw_topic) \
            .option("startingOffsets", "latest") \
            .option("maxOffsetsPerTrigger", 10000) \
            .load()
        
        return self._parse_kafka_readings(df)

    def _parse_kafka_readings(self, kafka_df: DataFrame) -> DataFrame:
        """Parse and validate Kafka readings before downstream aggregation."""
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), RAW_SCHEMA).alias("data"),
            col("timestamp").alias("kafka_timestamp"),
        ).select("data.*", "kafka_timestamp")
        
        # Convert timestamp string to timestamp type
        parsed_df = parsed_df.withColumn(
            "timestamp", col("timestamp").cast(TimestampType())
        )

        return self._validate_kafka_readings(parsed_df)

    def _validate_kafka_readings(self, parsed_df: DataFrame) -> DataFrame:
        """Observe rejection counts, then exclude invalid readings."""
        invalid_sensor_id = col("sensor_id").isNull() | col("sensor_id").rlike(r"^\s*$")
        invalid_timestamp = col("timestamp").isNull()
        value = col("value")
        invalid_value = (
            value.isNull() | isnan(value) | (spark_abs(value) == lit(float("inf")))
        )

        observed_df = parsed_df.observe(
            KAFKA_VALIDATION_OBSERVATION,
            spark_sum(when(invalid_sensor_id, 1).otherwise(0)).alias(
                "invalid_sensor_id"
            ),
            spark_sum(when(invalid_timestamp, 1).otherwise(0)).alias(
                "invalid_timestamp"
            ),
            spark_sum(when(invalid_value, 1).otherwise(0)).alias("invalid_value"),
        )
        return observed_df.filter(
            ~invalid_sensor_id & ~invalid_timestamp & ~invalid_value
        )
    
    def extract_features(self, df):
        """Extract windowed features from raw data"""
        # Perform windowed aggregation
        windowed_df = df \
            .withWatermark("timestamp", "30 seconds") \
            .groupBy(
                window(col("timestamp"), self.window_duration, self.slide_duration),
                col("sensor_id")
            ) \
            .agg(
                avg("value").alias("mean"),
                stddev("value").alias("stddev"),
                spark_min("value").alias("min"),
                spark_max("value").alias("max"),
                count("value").alias("count")
            )
        
        # Add derived features
        features_df = windowed_df \
            .withColumn("range", col("max") - col("min")) \
            .withColumn("window_start", col("window.start")) \
            .withColumn("window_end", col("window.end")) \
            .drop("window")
        
        # Fill null stddev with 0 (for windows with single value)
        features_df = features_df.fillna(0.0, subset=["stddev"])
        
        return features_df
    
    def predict_anomaly(self, features_df):
        """Call TF-Serving for anomaly detection"""
        
        # Define UDF for inference
        def score_batch(iterator: Iterator) -> Iterator:
            """Process batches and call TF-Serving"""
            for batch in iterator:
                # Convert to list of feature vectors
                features = []
                metadata = []
                
                for row in batch:
                    feature_vector = [
                        row['mean'],
                        row['stddev'],
                        row['min'],
                        row['max'],
                        row['count'],
                        row['range']
                    ]
                    features.append(feature_vector)
                    metadata.append({
                        'sensor_id': row['sensor_id'],
                        'window_start': str(row['window_start']),
                        'window_end': str(row['window_end'])
                    })
                
                if not features:
                    yield batch
                    continue
                
                # Call TF-Serving
                try:
                    url = f"{self.tfserving_url}/v1/models/{self.model_name}:predict"
                    payload = {"instances": features}
                    response = requests.post(url, json=payload, timeout=5)
                    
                    if response.status_code == 200:
                        predictions = response.json()['predictions']
                        
                        # Add predictions to rows
                        for i, row in enumerate(batch):
                            row['anomaly_score'] = float(predictions[i][0])
                            row['is_anomaly'] = float(predictions[i][0]) > self.anomaly_threshold
                    else:
                        # If TF-Serving fails, mark as unknown
                        for row in batch:
                            row['anomaly_score'] = 0.0
                            row['is_anomaly'] = False
                            
                except Exception as e:
                    print(f"TF-Serving error: {e}")
                    for row in batch:
                        row['anomaly_score'] = 0.0
                        row['is_anomaly'] = False
                
                yield batch
        
        # Note: For production, use mapInPandas with a proper schema
        # For simplicity, using foreachBatch pattern
        return features_df
    
    def write_to_minio(self, df, query_name):
        """Write features and scores to MinIO in Parquet format"""
        query = df \
            .writeStream \
            .format("parquet") \
            .outputMode("append") \
            .option("path", f"s3a://{self.minio_bucket}/features/") \
            .option("checkpointLocation", f"{self.checkpoint_location}/{query_name}") \
            .start()
        
        return query
    
    def write_anomalies_to_kafka(self, df, query_name):
        """Write detected anomalies to Kafka"""
        
        def process_batch(batch_df, batch_id):
            """Process each micro-batch"""
            # Call TF-Serving for scoring
            collected = batch_df.collect()
            scored_rows = []
            
            for row in collected:
                feature_vector = [
                    row['mean'],
                    row['stddev'],
                    row['min'],
                    row['max'],
                    row['count'],
                    row['range']
                ]
                
                try:
                    url = f"{self.tfserving_url}/v1/models/{self.model_name}:predict"
                    payload = {"instances": [feature_vector]}
                    response = requests.post(url, json=payload, timeout=5)
                    
                    if response.status_code == 200:
                        score = float(response.json()['predictions'][0][0])
                    else:
                        score = 0.0
                except Exception as e:
                    print(f"Inference error: {e}")
                    score = 0.0
                
                scored_rows.append({
                    'sensor_id': row['sensor_id'],
                    'window_start': str(row['window_start']),
                    'window_end': str(row['window_end']),
                    'mean': row['mean'],
                    'stddev': row['stddev'],
                    'min': row['min'],
                    'max': row['max'],
                    'count': row['count'],
                    'range': row['range'],
                    'anomaly_score': score,
                    'is_anomaly': score > self.anomaly_threshold,
                    'detection_time': str(current_timestamp())
                })
            
            # Create DataFrame and filter anomalies
            if scored_rows:
                scored_df = self.spark.createDataFrame(scored_rows)
                anomalies_df = scored_df.filter(col('is_anomaly') == True)
                
                if anomalies_df.count() > 0:
                    # Write to Kafka
                    kafka_df = anomalies_df.select(
                        col('sensor_id').alias('key'),
                        to_json(struct('*')).alias('value')
                    )
                    
                    kafka_df.write \
                        .format("kafka") \
                        .option("kafka.bootstrap.servers", self.kafka_bootstrap) \
                        .option("topic", self.kafka_anomaly_topic) \
                        .save()
                    
                    print(f"Batch {batch_id}: Detected {anomalies_df.count()} anomalies")
                
                # Write all features to MinIO
                scored_df.write \
                    .mode("append") \
                    .parquet(f"s3a://{self.minio_bucket}/features/")
        
        query = df \
            .writeStream \
            .foreachBatch(process_batch) \
            .option("checkpointLocation", f"{self.checkpoint_location}/{query_name}") \
            .start()
        
        return query
    
    def run(self):
        """Main streaming job"""
        print("Starting Spark Structured Streaming job...")
        
        # Create Spark session
        self.create_spark_session()
        
        # Read from Kafka
        raw_df = self.read_kafka_stream()
        print("Reading from Kafka topic:", self.kafka_raw_topic)
        
        # Extract features
        features_df = self.extract_features(raw_df)
        print(f"Extracting features with window={self.window_duration}, slide={self.slide_duration}")
        
        # Write features and anomalies
        query = self.write_anomalies_to_kafka(features_df, "anomaly-detection")
        
        print("Streaming job started. Waiting for data...")
        print(f"Anomaly threshold: {self.anomaly_threshold}")
        print(f"Writing to Kafka topic: {self.kafka_anomaly_topic}")
        print(f"Writing features to MinIO: s3a://{self.minio_bucket}/features/")
        
        # Wait for termination
        query.awaitTermination()


if __name__ == '__main__':
    job = SparkStreamingJob()
    job.run()
