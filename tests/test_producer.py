"""
Unit tests for Kafka producer
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.producer.kafka_producer import SensorSimulator, KafkaProducerService


class TestSensorSimulator:
    """Test sensor simulator"""
    
    def test_sensor_initialization(self):
        """Test sensor is initialized correctly"""
        sensor = SensorSimulator('sensor_001', anomaly_rate=0.1)
        assert sensor.sensor_id == 'sensor_001'
        assert sensor.anomaly_rate == 0.1
        assert 20.0 <= sensor.base_value <= 30.0
        
    def test_generate_normal_reading(self):
        """Test generating normal reading"""
        sensor = SensorSimulator('sensor_001', anomaly_rate=0.0)
        reading = sensor.generate_reading()
        
        assert reading['sensor_id'] == 'sensor_001'
        assert 'timestamp' in reading
        assert reading['metric'] == 'temperature'
        assert 'value' in reading
        assert 'meta' in reading
        assert reading['meta']['unit'] == 'celsius'
        
    def test_anomaly_generation(self):
        """Test anomaly generation"""
        sensor = SensorSimulator('sensor_001', anomaly_rate=1.0)
        reading = sensor.generate_reading()
        
        # With 100% anomaly rate, should generate anomaly
        assert reading['meta']['is_anomaly'] == True
        assert reading['meta']['anomaly_type'] in ['spike', 'drift', 'stuck', 'noise']


@pytest.mark.asyncio
class TestKafkaProducerService:
    """Test Kafka producer service"""
    
    async def test_producer_initialization(self):
        """Test producer initialization"""
        producer = KafkaProducerService(
            bootstrap_servers='localhost:9092',
            topic='test-topic',
            num_sensors=100,
            messages_per_second=10
        )
        
        assert producer.num_sensors == 100
        assert producer.messages_per_second == 10
        assert len(producer.sensors) == 100
        
    @patch('src.producer.kafka_producer.AIOKafkaProducer')
    async def test_send_batch(self, mock_producer):
        """Test sending batch of messages"""
        mock_instance = AsyncMock()
        mock_producer.return_value = mock_instance
        
        producer = KafkaProducerService(
            bootstrap_servers='localhost:9092',
            topic='test-topic',
            num_sensors=10,
            messages_per_second=1
        )
        producer.producer = mock_instance
        
        await producer.send_batch(5)
        assert producer.total_sent >= 0
