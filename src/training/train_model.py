"""
Model Training Script
Trains LSTM Autoencoder for anomaly detection
"""
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Tuple, Dict
import pickle

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_recall_curve, roc_auc_score, roc_curve, auc

from minio import Minio
from minio.error import S3Error


class AnomalyDataGenerator:
    """Generate synthetic training data with anomalies"""
    
    @staticmethod
    def generate_normal_data(n_samples: int, n_features: int = 6) -> np.ndarray:
        """Generate normal sensor readings"""
        # Base patterns: mean, stddev, min, max, count, range
        data = []
        for _ in range(n_samples):
            mean_val = np.random.normal(25, 2)  # Temperature around 25°C
            stddev_val = np.random.uniform(0.1, 1.0)
            count_val = np.random.randint(50, 100)
            min_val = mean_val - np.random.uniform(1, 3)
            max_val = mean_val + np.random.uniform(1, 3)
            range_val = max_val - min_val
            
            data.append([mean_val, stddev_val, min_val, max_val, count_val, range_val])
        
        return np.array(data)
    
    @staticmethod
    def generate_spike_anomalies(n_samples: int) -> np.ndarray:
        """Generate spike anomalies"""
        data = []
        for _ in range(n_samples):
            mean_val = np.random.normal(25, 2) + np.random.choice([-1, 1]) * np.random.uniform(15, 30)
            stddev_val = np.random.uniform(0.1, 1.0)
            count_val = np.random.randint(50, 100)
            min_val = mean_val - np.random.uniform(1, 3)
            max_val = mean_val + np.random.uniform(1, 3)
            range_val = max_val - min_val
            
            data.append([mean_val, stddev_val, min_val, max_val, count_val, range_val])
        
        return np.array(data)
    
    @staticmethod
    def generate_drift_anomalies(n_samples: int) -> np.ndarray:
        """Generate drift anomalies"""
        data = []
        for _ in range(n_samples):
            mean_val = np.random.normal(25, 2) + np.random.uniform(5, 15)
            stddev_val = np.random.uniform(0.1, 1.0)
            count_val = np.random.randint(50, 100)
            min_val = mean_val - np.random.uniform(1, 3)
            max_val = mean_val + np.random.uniform(1, 3)
            range_val = max_val - min_val
            
            data.append([mean_val, stddev_val, min_val, max_val, count_val, range_val])
        
        return np.array(data)
    
    @staticmethod
    def generate_stuck_anomalies(n_samples: int) -> np.ndarray:
        """Generate stuck sensor anomalies"""
        data = []
        for _ in range(n_samples):
            stuck_val = np.random.uniform(15, 35)
            mean_val = stuck_val
            stddev_val = 0.0  # No variation
            count_val = np.random.randint(50, 100)
            min_val = stuck_val
            max_val = stuck_val
            range_val = 0.0
            
            data.append([mean_val, stddev_val, min_val, max_val, count_val, range_val])
        
        return np.array(data)
    
    @staticmethod
    def generate_noise_anomalies(n_samples: int) -> np.ndarray:
        """Generate high noise anomalies"""
        data = []
        for _ in range(n_samples):
            mean_val = np.random.normal(25, 2)
            stddev_val = np.random.uniform(5, 15)  # High stddev
            count_val = np.random.randint(50, 100)
            min_val = mean_val - np.random.uniform(10, 20)
            max_val = mean_val + np.random.uniform(10, 20)
            range_val = max_val - min_val
            
            data.append([mean_val, stddev_val, min_val, max_val, count_val, range_val])
        
        return np.array(data)
    
    @classmethod
    def generate_training_data(cls, n_normal: int = 10000, anomaly_ratio: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
        """Generate complete training dataset"""
        # Normal data
        normal_data = cls.generate_normal_data(n_normal)
        normal_labels = np.zeros(n_normal)
        
        # Anomaly data (distributed across types)
        n_anomalies = int(n_normal * anomaly_ratio)
        n_per_type = n_anomalies // 4
        
        spike_data = cls.generate_spike_anomalies(n_per_type)
        drift_data = cls.generate_drift_anomalies(n_per_type)
        stuck_data = cls.generate_stuck_anomalies(n_per_type)
        noise_data = cls.generate_noise_anomalies(n_per_type)
        
        anomaly_data = np.vstack([spike_data, drift_data, stuck_data, noise_data])
        anomaly_labels = np.ones(len(anomaly_data))
        
        # Combine and shuffle
        X = np.vstack([normal_data, anomaly_data])
        y = np.hstack([normal_labels, anomaly_labels])
        
        # Shuffle
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        return X, y


class LSTMAutoencoder:
    """LSTM Autoencoder model for anomaly detection"""
    
    def __init__(
        self,
        sequence_length: int = 50,
        n_features: int = 6,
        lstm_units: int = 128,
        learning_rate: float = 0.001
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = StandardScaler()
        
    def build_model(self):
        """Build LSTM Autoencoder architecture"""
        # Encoder
        encoder_inputs = layers.Input(shape=(self.sequence_length, self.n_features))
        encoder_lstm1 = layers.LSTM(self.lstm_units, return_sequences=True)(encoder_inputs)
        encoder_lstm2 = layers.LSTM(self.lstm_units // 2, return_sequences=False)(encoder_lstm1)
        
        # Decoder
        decoder_repeat = layers.RepeatVector(self.sequence_length)(encoder_lstm2)
        decoder_lstm1 = layers.LSTM(self.lstm_units // 2, return_sequences=True)(decoder_repeat)
        decoder_lstm2 = layers.LSTM(self.lstm_units, return_sequences=True)(decoder_lstm1)
        decoder_outputs = layers.TimeDistributed(layers.Dense(self.n_features))(decoder_lstm2)
        
        # Model
        self.model = keras.Model(encoder_inputs, decoder_outputs)
        
        # Compile
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return self.model
    
    def prepare_sequences(self, X: np.ndarray) -> np.ndarray:
        """Convert flat features to sequences"""
        sequences = []
        for i in range(len(X) - self.sequence_length + 1):
            sequences.append(X[i:i + self.sequence_length])
        return np.array(sequences)
    
    def train(
        self,
        X_train: np.ndarray,
        X_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 64
    ) -> Dict:
        """Train the model"""
        # Scale data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Prepare sequences
        X_train_seq = self.prepare_sequences(X_train_scaled)
        X_val_seq = self.prepare_sequences(X_val_scaled)
        
        # Callbacks
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        reduce_lr = keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7
        )
        
        # Train
        history = self.model.fit(
            X_train_seq, X_train_seq,
            validation_data=(X_val_seq, X_val_seq),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping, reduce_lr],
            verbose=1
        )
        
        return history.history
    
    def compute_reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """Compute reconstruction error for anomaly detection"""
        X_scaled = self.scaler.transform(X)
        X_seq = self.prepare_sequences(X_scaled)
        
        reconstructions = self.model.predict(X_seq, verbose=0)
        mse = np.mean(np.square(X_seq - reconstructions), axis=(1, 2))
        
        return mse
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate model performance"""
        # Compute reconstruction errors
        errors = self.compute_reconstruction_error(X_test)
        
        # Adjust labels for sequence length
        y_test_adjusted = y_test[self.sequence_length - 1:]
        
        # Calculate metrics
        roc_auc = roc_auc_score(y_test_adjusted, errors)
        precision, recall, thresholds = precision_recall_curve(y_test_adjusted, errors)
        pr_auc = auc(recall, precision)
        
        # Find optimal threshold
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        optimal_idx = np.argmax(f1_scores)
        optimal_threshold = thresholds[optimal_idx]
        
        metrics = {
            'roc_auc': float(roc_auc),
            'pr_auc': float(pr_auc),
            'optimal_threshold': float(optimal_threshold),
            'precision_at_optimal': float(precision[optimal_idx]),
            'recall_at_optimal': float(recall[optimal_idx]),
            'f1_at_optimal': float(f1_scores[optimal_idx])
        }
        
        return metrics


class ModelTrainer:
    """Main training pipeline"""
    
    def __init__(self):
        self.minio_endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        self.minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.lstm_units = int(os.getenv('LSTM_UNITS', '128'))
        self.sequence_length = int(os.getenv('SEQUENCE_LENGTH', '50'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '64'))
        self.epochs = int(os.getenv('EPOCHS', '50'))
        self.learning_rate = float(os.getenv('LEARNING_RATE', '0.001'))
        
    def train_model(self):
        """Execute full training pipeline"""
        print("=" * 60)
        print("IoT Anomaly Detection - Model Training")
        print("=" * 60)
        
        # Generate training data
        print("\n1. Generating synthetic training data...")
        X, y = AnomalyDataGenerator.generate_training_data(n_normal=10000, anomaly_ratio=0.05)
        print(f"   Generated {len(X)} samples ({np.sum(y)} anomalies)")
        
        # Split data
        print("\n2. Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42, stratify=y_train)
        print(f"   Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # Build model
        print("\n3. Building LSTM Autoencoder...")
        autoencoder = LSTMAutoencoder(
            sequence_length=self.sequence_length,
            n_features=6,
            lstm_units=self.lstm_units,
            learning_rate=self.learning_rate
        )
        autoencoder.build_model()
        print(f"   LSTM Units: {self.lstm_units}, Sequence Length: {self.sequence_length}")
        autoencoder.model.summary()
        
        # Train model
        print("\n4. Training model...")
        history = autoencoder.train(X_train, X_val, epochs=self.epochs, batch_size=self.batch_size)
        print(f"   Final train loss: {history['loss'][-1]:.4f}")
        print(f"   Final val loss: {history['val_loss'][-1]:.4f}")
        
        # Evaluate model
        print("\n5. Evaluating model...")
        metrics = autoencoder.evaluate(X_test, y_test)
        print(f"   ROC AUC: {metrics['roc_auc']:.4f}")
        print(f"   PR AUC: {metrics['pr_auc']:.4f}")
        print(f"   Optimal Threshold: {metrics['optimal_threshold']:.4f}")
        print(f"   Precision: {metrics['precision_at_optimal']:.4f}")
        print(f"   Recall: {metrics['recall_at_optimal']:.4f}")
        print(f"   F1 Score: {metrics['f1_at_optimal']:.4f}")
        
        # Save model
        print("\n6. Saving model...")
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"models/anomaly_detector/{version}"
        os.makedirs(model_path, exist_ok=True)
        
        # Save in SavedModel format for TF-Serving
        autoencoder.model.save(model_path)
        
        # Save scaler
        scaler_path = f"{model_path}/scaler.pkl"
        with open(scaler_path, 'wb') as f:
            pickle.dump(autoencoder.scaler, f)
        
        # Save metrics
        metrics_path = f"{model_path}/metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Create version 1 symlink for TF-Serving
        latest_path = "models/anomaly_detector/1"
        if os.path.exists(latest_path):
            os.remove(latest_path)
        os.symlink(version, latest_path, target_is_directory=True)
        
        print(f"   Model saved to: {model_path}")
        print(f"   TF-Serving path: {latest_path}")
        
        print("\n" + "=" * 60)
        print("Training completed successfully!")
        print("=" * 60)
        
        return metrics


if __name__ == '__main__':
    trainer = ModelTrainer()
    trainer.train_model()
