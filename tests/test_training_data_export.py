from datetime import datetime, timedelta
from typing import List

import pandas as pd
import pytest

import scripts.generate_training_data as training_data
from src.training.train_model import AnomalyDataGenerator


def _capture_parquet_frames(
    monkeypatch: pytest.MonkeyPatch,
) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    monkeypatch.setattr(
        pd.DataFrame,
        "to_parquet",
        lambda self, *args, **kwargs: frames.append(self.copy()),
    )
    return frames


def test_default_export_respects_total_count_and_historical_window(
    tmp_path, monkeypatch
):
    parquet_frames = _capture_parquet_frames(monkeypatch)
    end_time = datetime(2026, 11, 22, 12, 0, 0)
    original_timestamp_generator = training_data._generate_timestamps
    monkeypatch.setattr(
        training_data,
        "_generate_timestamps",
        lambda n_rows: original_timestamp_generator(n_rows, end_time),
    )
    frame = training_data.generate_and_save_training_data(output_dir=str(tmp_path))

    assert len(frame) == 100000
    assert list(frame.columns) == [
        "timestamp",
        "sensor_id",
        "mean",
        "stddev",
        "min",
        "max",
        "count",
        "range",
        "is_anomaly",
    ]
    assert int(frame["is_anomaly"].sum()) == 5000
    assert frame["timestamp"].min() == end_time - timedelta(days=30)
    assert frame["timestamp"].max() == end_time
    assert len(parquet_frames) == 1
    assert parquet_frames[0].equals(frame)
    assert len(pd.read_csv(tmp_path / "training_data.csv")) == 100000


@pytest.mark.parametrize(
    ("n_samples", "anomaly_ratio", "expected_anomalies"),
    [(1, 0, 0), (3, 0.5, 1), (7, 0.5, 3), (17, 0.2, 3), (1, 1, 1)],
)
def test_export_preserves_small_requested_counts(
    tmp_path, monkeypatch, n_samples, anomaly_ratio, expected_anomalies
):
    parquet_frames = _capture_parquet_frames(monkeypatch)

    frame = training_data.generate_and_save_training_data(
        n_samples=n_samples,
        anomaly_ratio=anomaly_ratio,
        output_dir=str(tmp_path),
    )

    assert len(frame) == n_samples
    assert int(frame["is_anomaly"].sum()) == expected_anomalies
    assert len(parquet_frames) == 1
    assert len(parquet_frames[0]) == n_samples


@pytest.mark.parametrize(
    ("n_rows", "expected"),
    [
        (0, []),
        (1, [datetime(2026, 1, 31)]),
        (
            3,
            [
                datetime(2026, 1, 1),
                datetime(2026, 1, 16),
                datetime(2026, 1, 31),
            ],
        ),
    ],
)
def test_timestamps_cover_only_the_inclusive_historical_window(n_rows, expected):
    end_time = datetime(2026, 1, 31)

    timestamps = training_data._generate_timestamps(n_rows, end_time)

    assert timestamps == expected
    assert all(timestamp <= end_time for timestamp in timestamps)


@pytest.mark.parametrize(
    ("n_samples", "anomaly_ratio"),
    [(0, 0.05), (-1, 0.05), (10, -0.01), (10, 1.01)],
)
def test_export_rejects_invalid_count_or_anomaly_ratio(n_samples, anomaly_ratio):
    with pytest.raises(ValueError):
        training_data.generate_and_save_training_data(
            n_samples=n_samples,
            anomaly_ratio=anomaly_ratio,
        )


def test_training_generator_keeps_anomaly_remainders():
    features, labels = AnomalyDataGenerator.generate_training_data(
        n_normal=8,
        n_anomalies=3,
    )

    assert features.shape == (11, 6)
    assert int(labels.sum()) == 3


def test_training_generator_preserves_ratio_based_default():
    features, labels = AnomalyDataGenerator.generate_training_data(
        n_normal=80,
        anomaly_ratio=0.1,
    )

    assert features.shape == (88, 6)
    assert int(labels.sum()) == 8
