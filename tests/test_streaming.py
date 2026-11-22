"""Tests for streaming inference failure handling."""

from unittest.mock import MagicMock, Mock

import pytest
import requests

from src.streaming import spark_streaming


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=None):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeBatch:
    def __init__(self, rows):
        self.rows = rows

    def collect(self):
        return self.rows


def make_row(sensor_id):
    return {
        "sensor_id": sensor_id,
        "window_start": "2026-11-22 12:00:00",
        "window_end": "2026-11-22 12:01:00",
        "mean": 20.0,
        "stddev": 1.0,
        "min": 18.0,
        "max": 22.0,
        "count": 4,
        "range": 4.0,
    }


def capture_batch_callback(monkeypatch, responses):
    monkeypatch.setattr(spark_streaming.requests, "post", Mock(side_effect=responses))
    monkeypatch.setattr(spark_streaming, "col", Mock(return_value=MagicMock()))
    monkeypatch.setattr(spark_streaming, "struct", Mock(return_value=MagicMock()))
    monkeypatch.setattr(spark_streaming, "to_json", Mock(return_value=MagicMock()))
    monkeypatch.setattr(spark_streaming, "current_timestamp", Mock(return_value="now"))

    job = spark_streaming.SparkStreamingJob()
    job.anomaly_threshold = 0.95
    job.spark = Mock()

    scored_df = Mock()
    anomalies_df = Mock()
    kafka_df = Mock()
    job.spark.createDataFrame.return_value = scored_df
    scored_df.filter.return_value = anomalies_df
    anomalies_df.count.return_value = 1
    anomalies_df.select.return_value = kafka_df

    stream_writer = Mock()
    callbacks = []

    def capture(callback):
        callbacks.append(callback)
        return stream_writer

    stream_writer.foreachBatch.side_effect = capture
    stream_writer.option.return_value = stream_writer
    stream_writer.start.return_value = stream_writer
    features_df = Mock()
    features_df.writeStream = stream_writer

    job.write_anomalies_to_kafka(features_df, "test")
    return callbacks[0], job, scored_df, kafka_df


@pytest.mark.parametrize(
    ("failure", "expected_exception"),
    [
        (requests.Timeout("timed out"), requests.Timeout),
        (FakeResponse(status_code=503), requests.HTTPError),
        (FakeResponse(json_error=ValueError("invalid JSON")), ValueError),
        (FakeResponse(payload=[]), ValueError),
        (FakeResponse(payload={"predictions": []}), ValueError),
        (FakeResponse(payload={"predictions": [[0.5], [0.6]]}), ValueError),
        (FakeResponse(payload={"predictions": [[]]}), ValueError),
        (FakeResponse(payload={"predictions": [[True]]}), ValueError),
        (FakeResponse(payload={"predictions": [["not-a-number"]]}), ValueError),
        (FakeResponse(payload={"predictions": [[float("nan")]]}), ValueError),
        (FakeResponse(payload={"predictions": [[float("inf")]]}), ValueError),
    ],
)
def test_inference_failure_aborts_batch_before_any_sink_write(
    monkeypatch, failure, expected_exception
):
    callback, job, scored_df, kafka_df = capture_batch_callback(
        monkeypatch,
        [FakeResponse(payload={"predictions": [[0.99]]}), failure],
    )

    with pytest.raises(expected_exception):
        callback(FakeBatch([make_row("sensor-1"), make_row("sensor-2")]), 7)

    job.spark.createDataFrame.assert_not_called()
    kafka_df.write.format.assert_not_called()
    scored_df.write.mode.assert_not_called()


def test_failed_batch_can_be_replayed_after_inference_recovers(monkeypatch):
    callback, job, scored_df, kafka_df = capture_batch_callback(
        monkeypatch,
        [
            requests.Timeout("temporary outage"),
            FakeResponse(payload={"predictions": [[0.99]]}),
        ],
    )
    batch = FakeBatch([make_row("sensor-1")])

    with pytest.raises(requests.Timeout):
        callback(batch, 11)
    job.spark.createDataFrame.assert_not_called()

    callback(batch, 11)

    written_rows = job.spark.createDataFrame.call_args.args[0]
    assert written_rows[0]["anomaly_score"] == 0.99
    assert written_rows[0]["is_anomaly"] is True
    kafka_df.write.format.return_value.option.return_value.option.return_value.save.assert_called_once()
    scored_df.write.mode.return_value.parquet.assert_called_once()


def test_valid_scores_are_persisted_and_anomalies_are_routed(monkeypatch):
    callback, job, scored_df, kafka_df = capture_batch_callback(
        monkeypatch,
        [
            FakeResponse(payload={"predictions": [[0.99]]}),
            FakeResponse(payload={"predictions": [[0.25]]}),
        ],
    )

    callback(FakeBatch([make_row("sensor-1"), make_row("sensor-2")]), 12)

    written_rows = job.spark.createDataFrame.call_args.args[0]
    assert [row["anomaly_score"] for row in written_rows] == [0.99, 0.25]
    assert [row["is_anomaly"] for row in written_rows] == [True, False]
    kafka_df.write.format.return_value.option.return_value.option.return_value.save.assert_called_once()
    scored_df.write.mode.return_value.parquet.assert_called_once()
