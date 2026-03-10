"""Entry-point script to start an infinite Kafka consumer loop.

Usage:
    python consumer.py
"""
from kafka_client import run_consumer

if __name__ == "__main__":
    run_consumer()
