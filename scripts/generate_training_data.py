"""
Generate synthetic training data and save to files
"""
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.training.train_model import AnomalyDataGenerator


def generate_and_save_training_data(
    n_samples: int = 100000,
    anomaly_ratio: float = 0.05,
    output_dir: str = 'data'
):
    """Generate and save training data"""
    print(f"Generating {n_samples} samples with {anomaly_ratio*100}% anomalies...")
    
    # Generate data
    X, y = AnomalyDataGenerator.generate_training_data(
        n_normal=n_samples,
        anomaly_ratio=anomaly_ratio
    )
    
    # Create timestamps
    start_time = datetime.now() - timedelta(days=30)
    timestamps = [
        start_time + timedelta(seconds=i*60)
        for i in range(len(X))
    ]
    
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
                       help='Number of samples to generate')
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
