"""
Unit tests for training module
"""
import pytest
import numpy as np
from src.training.train_model import AnomalyDataGenerator, LSTMAutoencoder


class TestAnomalyDataGenerator:
    """Test anomaly data generation"""
    
    def test_generate_normal_data(self):
        """Test normal data generation"""
        data = AnomalyDataGenerator.generate_normal_data(n_samples=100)
        
        assert data.shape == (100, 6)
        assert np.all(data[:, 0] > 0)  # Mean should be positive
        assert np.all(data[:, 1] >= 0)  # Stddev should be non-negative
        
    def test_generate_spike_anomalies(self):
        """Test spike anomaly generation"""
        data = AnomalyDataGenerator.generate_spike_anomalies(n_samples=50)
        
        assert data.shape == (50, 6)
        # Spikes should have extreme mean values
        assert np.any(np.abs(data[:, 0] - 25) > 10)
        
    def test_generate_stuck_anomalies(self):
        """Test stuck sensor anomaly generation"""
        data = AnomalyDataGenerator.generate_stuck_anomalies(n_samples=50)
        
        assert data.shape == (50, 6)
        # Stuck sensors should have zero stddev and range
        assert np.all(data[:, 1] == 0)  # stddev
        assert np.all(data[:, 5] == 0)  # range
        
    def test_generate_training_data(self):
        """Test complete training data generation"""
        X, y = AnomalyDataGenerator.generate_training_data(
            n_normal=1000,
            anomaly_ratio=0.05
        )
        
        assert len(X) == len(y)
        assert X.shape[1] == 6
        # Check anomaly ratio is approximately correct
        anomaly_rate = np.mean(y)
        assert 0.04 <= anomaly_rate <= 0.06


class TestLSTMAutoencoder:
    """Test LSTM Autoencoder model"""
    
    def test_model_initialization(self):
        """Test model initialization"""
        model = LSTMAutoencoder(
            sequence_length=50,
            n_features=6,
            lstm_units=64
        )
        
        assert model.sequence_length == 50
        assert model.n_features == 6
        assert model.lstm_units == 64
        
    def test_build_model(self):
        """Test model building"""
        model = LSTMAutoencoder(
            sequence_length=50,
            n_features=6,
            lstm_units=64
        )
        model.build_model()
        
        assert model.model is not None
        assert len(model.model.layers) > 0
        
    def test_prepare_sequences(self):
        """Test sequence preparation"""
        model = LSTMAutoencoder(sequence_length=10, n_features=6)
        X = np.random.randn(100, 6)
        sequences = model.prepare_sequences(X)
        
        assert sequences.shape == (91, 10, 6)  # 100 - 10 + 1 = 91
        
    def test_train_on_synthetic_data(self):
        """Test training on synthetic data"""
        # Generate small dataset
        X, y = AnomalyDataGenerator.generate_training_data(
            n_normal=500,
            anomaly_ratio=0.05
        )
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_val = X[:split_idx], X[split_idx:]
        
        # Create and train model
        model = LSTMAutoencoder(
            sequence_length=20,
            n_features=6,
            lstm_units=32
        )
        model.build_model()
        
        history = model.train(X_train, X_val, epochs=2, batch_size=32)
        
        assert 'loss' in history
        assert 'val_loss' in history
        assert len(history['loss']) > 0
