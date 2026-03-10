"""Entry-point script to start an infinite Kafka producer loop.

Usage:
    python producer.py
"""
from kafka_client import run_producer

if __name__ == "__main__":
    run_producer()
