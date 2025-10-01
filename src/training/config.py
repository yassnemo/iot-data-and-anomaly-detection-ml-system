"""
Training configuration
"""

# Model architecture
LSTM_UNITS = 128
SEQUENCE_LENGTH = 50
N_FEATURES = 6

# Training hyperparameters
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 0.001
VALIDATION_SPLIT = 0.2

# Data generation
N_TRAINING_SAMPLES = 10000
ANOMALY_RATIO = 0.05

# Anomaly detection
ANOMALY_THRESHOLD_PERCENTILE = 95

# Model versioning
MODEL_BASE_PATH = 'models/anomaly_detector'
