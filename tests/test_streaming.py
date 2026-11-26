"""Tests for Kafka reading validation in the streaming job."""

import json
import logging
import shutil
from types import SimpleNamespace

import pytest
from pyspark.sql import Row, SparkSession

from src.streaming.spark_streaming import (
    KAFKA_VALIDATION_OBSERVATION,
    SparkStreamingJob,
)


@pytest.fixture(scope="module")
def spark():
    if not shutil.which("java"):
        pytest.skip("A local Java runtime is required for Spark tests")

    session = (
        SparkSession.builder.master("local[1]")
        .appName("malformed-kafka-reading-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def test_invalid_kafka_readings_are_counted_and_filtered_before_aggregation(
    spark, caplog
):
    readings = [
        {
            "sensor_id": "sensor-1",
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
            "value": 10.0,
        },
        {
            "sensor_id": "sensor-1",
            "timestamp": "2026-01-01 00:00:06",
            "metric": "temperature",
            "value": 20.0,
        },
        {
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
            "value": 30.0,
        },
        {
            "sensor_id": " \t ",
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
            "value": 30.0,
        },
        {
            "sensor_id": "sensor-1",
            "timestamp": "not-a-timestamp",
            "metric": "temperature",
            "value": 30.0,
        },
        {"sensor_id": "sensor-1", "metric": "temperature", "value": 30.0},
        {
            "sensor_id": "sensor-1",
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
        },
        {
            "sensor_id": "sensor-1",
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
            "value": None,
        },
        {
            "sensor_id": "sensor-1",
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
            "value": float("nan"),
        },
        {
            "sensor_id": "sensor-1",
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
            "value": float("inf"),
        },
        {
            "sensor_id": "sensor-1",
            "timestamp": "2026-01-01 00:00:05",
            "metric": "temperature",
            "value": float("-inf"),
        },
    ]
    source_sql = " UNION ALL ".join(
        "SELECT CAST('{}' AS BINARY) AS value, "
        "TIMESTAMP '2026-01-01 00:00:00' AS timestamp".format(
            json.dumps(reading).replace("'", "''")
        )
        for reading in readings
    )
    source = spark.sql(source_sql)

    job = SparkStreamingJob()
    job.create_spark_session()
    validated = job._parse_kafka_readings(source)

    valid_readings = validated.collect()
    assert len(valid_readings) == 2
    assert {row["value"] for row in valid_readings} == {10.0, 20.0}
    assert {row["sensor_id"] for row in valid_readings} == {"sensor-1"}

    features = job.extract_features(validated).collect()
    assert features
    assert all(row["sensor_id"] == "sensor-1" for row in features)
    assert all(row["count"] == 2 for row in features)
    assert all(row["mean"] == 15.0 for row in features)

    nonfinite_values = spark.sql(
        "SELECT 'sensor-1' AS sensor_id, "
        "TIMESTAMP '2026-01-01 00:00:00' AS timestamp, "
        "CAST('NaN' AS DOUBLE) AS value "
        "UNION ALL SELECT 'sensor-1', TIMESTAMP '2026-01-01 00:00:00', "
        "CAST('Infinity' AS DOUBLE) "
        "UNION ALL SELECT 'sensor-1', TIMESTAMP '2026-01-01 00:00:00', "
        "CAST('-Infinity' AS DOUBLE) "
        "UNION ALL SELECT 'sensor-1', TIMESTAMP '2026-01-01 00:00:00', "
        "42.0"
    )
    finite_values = (
        job._validate_kafka_readings(nonfinite_values).select("value").collect()
    )
    assert [row["value"] for row in finite_values] == [42.0]

    listener = job._validation_listener
    assert listener is not None
    progress = SimpleNamespace(
        batchId=0,
        observedMetrics={
            KAFKA_VALIDATION_OBSERVATION: Row(
                invalid_sensor_id=2,
                invalid_timestamp=2,
                invalid_value=5,
            )
        },
    )
    with caplog.at_level(logging.WARNING, logger="src.streaming.spark_streaming"):
        listener.onQueryProgress(SimpleNamespace(progress=progress))
    assert "invalid_sensor_id" in caplog.text
    assert "invalid_timestamp" in caplog.text
    assert "invalid_value" in caplog.text
    assert "sensor-1" not in caplog.text
