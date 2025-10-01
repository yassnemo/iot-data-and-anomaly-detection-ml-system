"""
Kafka Producer - IoT Sensor Simulator
Simulates N sensors sending time-series data to Kafka topic 'raw-readings'
"""
import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, Any
import argparse
import os

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError


class SensorSimulator:
    """Simulates IoT sensor data with configurable anomaly injection"""
    
    def __init__(self, sensor_id: str, anomaly_rate: float = 0.05):
        self.sensor_id = sensor_id
        self.anomaly_rate = anomaly_rate
        self.base_value = random.uniform(20.0, 30.0)  # Base temperature
        self.drift = 0.0
        self.stuck_counter = 0
        
    def generate_reading(self) -> Dict[str, Any]:
        """Generate a single sensor reading with possible anomalies"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Determine if this should be an anomaly
        is_anomaly = random.random() < self.anomaly_rate
        anomaly_type = None
        
        if is_anomaly:
            anomaly_type = random.choice(['spike', 'drift', 'stuck', 'noise'])
            
            if anomaly_type == 'spike':
                # Sudden spike or drop
                value = self.base_value + random.uniform(-20, 20)
            elif anomaly_type == 'drift':
                # Gradual drift
                self.drift += random.uniform(-0.5, 0.5)
                value = self.base_value + self.drift
            elif anomaly_type == 'stuck':
                # Stuck at same value
                if self.stuck_counter == 0:
                    self.stuck_value = self.base_value + random.uniform(-5, 5)
                value = self.stuck_value
                self.stuck_counter += 1
                if self.stuck_counter > 10:
                    self.stuck_counter = 0
            else:  # noise
                # High frequency noise
                value = self.base_value + random.gauss(0, 5)
        else:
            # Normal reading with small variation
            value = self.base_value + random.gauss(0, 0.5)
            self.drift *= 0.95  # Gradually reduce drift
        
        return {
            'sensor_id': self.sensor_id,
            'timestamp': timestamp,
            'metric': 'temperature',
            'value': round(value, 2),
            'meta': {
                'unit': 'celsius',
                'location': f'zone_{hash(self.sensor_id) % 100}',
                'is_anomaly': is_anomaly,
                'anomaly_type': anomaly_type
            }
        }


class KafkaProducerService:
    """Async Kafka producer for sensor data"""
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        num_sensors: int = 10000,
        messages_per_second: int = 1,
        anomaly_rate: float = 0.05
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.num_sensors = num_sensors
        self.messages_per_second = messages_per_second
        self.producer = None
        
        # Create sensors
        self.sensors = [
            SensorSimulator(f'sensor_{i:06d}', anomaly_rate)
            for i in range(num_sensors)
        ]
        
        # Metrics
        self.total_sent = 0
        self.total_errors = 0
        self.start_time = None
        
    async def start(self):
        """Initialize Kafka producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip',
            max_batch_size=16384,
            linger_ms=10
        )
        await self.producer.start()
        self.start_time = time.time()
        print(f"Producer started. Simulating {self.num_sensors} sensors...")
        
    async def stop(self):
        """Shutdown producer"""
        if self.producer:
            await self.producer.stop()
            
    async def send_batch(self, batch_size: int):
        """Send a batch of sensor readings"""
        tasks = []
        
        for i in range(batch_size):
            sensor = self.sensors[i % len(self.sensors)]
            reading = sensor.generate_reading()
            
            task = self.producer.send(
                self.topic,
                value=reading,
                key=reading['sensor_id'].encode('utf-8')
            )
            tasks.append(task)
        
        # Wait for all sends to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and errors
        for result in results:
            if isinstance(result, Exception):
                self.total_errors += 1
            else:
                self.total_sent += 1
                
    async def run(self):
        """Main producer loop"""
        print(f"Starting to produce {self.messages_per_second} messages/sec...")
        
        interval = 1.0 / self.messages_per_second if self.messages_per_second > 0 else 1.0
        
        try:
            while True:
                loop_start = time.time()
                
                # Send one reading per sensor
                await self.send_batch(len(self.sensors))
                
                # Print metrics every 10 seconds
                elapsed = time.time() - self.start_time
                if int(elapsed) % 10 == 0 and elapsed > 1:
                    rate = self.total_sent / elapsed
                    print(f"Metrics: {self.total_sent} sent, {self.total_errors} errors, "
                          f"{rate:.1f} msg/sec, {elapsed:.1f}s elapsed")
                
                # Sleep to maintain target rate
                loop_duration = time.time() - loop_start
                sleep_time = max(0, interval - loop_duration)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nShutting down producer...")
        finally:
            elapsed = time.time() - self.start_time
            final_rate = self.total_sent / elapsed if elapsed > 0 else 0
            print(f"\nFinal stats: {self.total_sent} sent, {self.total_errors} errors, "
                  f"{final_rate:.1f} msg/sec average")


async def main():
    parser = argparse.ArgumentParser(description='IoT Sensor Simulator - Kafka Producer')
    parser.add_argument('--bootstrap-servers', 
                       default=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                       help='Kafka bootstrap servers')
    parser.add_argument('--topic',
                       default=os.getenv('KAFKA_RAW_TOPIC', 'raw-readings'),
                       help='Kafka topic name')
    parser.add_argument('--num-sensors', type=int,
                       default=int(os.getenv('NUM_SENSORS', 10000)),
                       help='Number of sensors to simulate')
    parser.add_argument('--messages-per-second', type=int,
                       default=int(os.getenv('MESSAGES_PER_SECOND', 1)),
                       help='Messages per second per sensor')
    parser.add_argument('--anomaly-rate', type=float,
                       default=float(os.getenv('ANOMALY_RATE', 0.05)),
                       help='Probability of anomaly (0.0-1.0)')
    
    args = parser.parse_args()
    
    producer_service = KafkaProducerService(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        num_sensors=args.num_sensors,
        messages_per_second=args.messages_per_second,
        anomaly_rate=args.anomaly_rate
    )
    
    await producer_service.start()
    try:
        await producer_service.run()
    finally:
        await producer_service.stop()


if __name__ == '__main__':
    asyncio.run(main())
