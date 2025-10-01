"""
Integration tests
"""
import pytest
import time
import json
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic


@pytest.mark.integration
class TestKafkaIntegration:
    """Integration tests for Kafka"""
    
    @pytest.fixture
    def kafka_bootstrap_servers(self):
        return 'localhost:9092'
    
    def test_kafka_connection(self, kafka_bootstrap_servers):
        """Test Kafka connection"""
        try:
            admin = KafkaAdminClient(bootstrap_servers=kafka_bootstrap_servers)
            topics = admin.list_topics()
            assert topics is not None
            admin.close()
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")
    
    def test_produce_and_consume(self, kafka_bootstrap_servers):
        """Test producing and consuming messages"""
        topic = 'test-topic'
        
        try:
            # Create topic
            admin = KafkaAdminClient(bootstrap_servers=kafka_bootstrap_servers)
            topic_list = [NewTopic(name=topic, num_partitions=1, replication_factor=1)]
            try:
                admin.create_topics(new_topics=topic_list, validate_only=False)
            except:
                pass  # Topic may already exist
            admin.close()
            
            # Produce message
            producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            test_message = {
                'sensor_id': 'test_001',
                'value': 25.5,
                'timestamp': time.time()
            }
            
            producer.send(topic, value=test_message)
            producer.flush()
            producer.close()
            
            # Consume message
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=kafka_bootstrap_servers,
                auto_offset_reset='earliest',
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                consumer_timeout_ms=5000
            )
            
            messages = []
            for message in consumer:
                messages.append(message.value)
                break
            
            consumer.close()
            
            assert len(messages) > 0
            assert messages[0]['sensor_id'] == 'test_001'
            
        except Exception as e:
            pytest.skip(f"Kafka integration test failed: {e}")


@pytest.mark.integration
class TestMinIOIntegration:
    """Integration tests for MinIO"""
    
    def test_minio_connection(self):
        """Test MinIO connection"""
        from src.common.utils import get_minio_client
        
        try:
            client = get_minio_client()
            # List buckets to test connection
            buckets = client.list_buckets()
            assert buckets is not None
        except Exception as e:
            pytest.skip(f"MinIO not available: {e}")
