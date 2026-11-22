"""
Generate synthetic training data and save to files
"""
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.training.train_model import AnomalyDataGenerator


def _generate_timestamps(
    n_rows: int, end_time: Optional[datetime] = None
) -> List[datetime]:
    if n_rows < 0:
        raise ValueError("n_rows must be non-negative")
    if n_rows == 0:
        return []

    if end_time is None:
        end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    if n_rows == 1:
        return [end_time]

    duration = end_time - start_time
    return [start_time + duration * (index / (n_rows - 1)) for index in range(n_rows)]


def generate_and_save_training_data(
    n_samples: int = 100000, anomaly_ratio: float = 0.05, output_dir: str = "data"
) -> pd.DataFrame:
    """Generate and save training data"""
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    if not 0 <= anomaly_ratio <= 1:
        raise ValueError("anomaly_ratio must be between 0 and 1")

    print(f"Generating {n_samples} samples with {anomaly_ratio*100}% anomalies...")
    
    # Generate data
    n_anomalies = int(n_samples * anomaly_ratio)
    n_normal = n_samples - n_anomalies
    X, y = AnomalyDataGenerator.generate_training_data(
        n_normal=n_normal, anomaly_ratio=anomaly_ratio, n_anomalies=n_anomalies
    )
    
    # Create timestamps
    timestamps = _generate_timestamps(len(X))
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'sensor_id': [f'sensor_{i % 1000:06d}' for i in range(len(X))],
        'mean': X[:, 0],
        'stddev': X[:, 1],
        'min': X[:, 2],
        'max': X[:, 3],
        'count': X[:, 4],
        'range': X[:, 5],
        'is_anomaly': y
    })
    
    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'training_data.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV to: {csv_path}")
    
    # Save to Parquet
    parquet_path = os.path.join(output_dir, 'training_data.parquet')
    df.to_parquet(parquet_path, index=False)
    print(f"Saved Parquet to: {parquet_path}")
    
    # Print statistics
    print(f"\nDataset statistics:")
    print(f"  Total samples: {len(df)}")
    print(f"  Anomalies: {int(np.sum(y))} ({np.mean(y)*100:.2f}%)")
    print(f"  Normal: {int(len(y) - np.sum(y))} ({(1-np.mean(y))*100:.2f}%)")
    print(f"  Features: mean={df['mean'].mean():.2f}, stddev={df['stddev'].mean():.2f}")
    
    return df


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate training data')
    parser.add_argument('--samples', type=int, default=100000,
                       help='Total number of samples to export')
    parser.add_argument('--anomaly-ratio', type=float, default=0.05,
                       help='Ratio of anomalies')
    parser.add_argument('--output-dir', default='data',
                       help='Output directory')
    
    args = parser.parse_args()
    
    generate_and_save_training_data(
        n_samples=args.samples,
        anomaly_ratio=args.anomaly_ratio,
        output_dir=args.output_dir
    )
