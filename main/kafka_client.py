"""Reusable Kafka Producer and Consumer helpers.

This module exposes two functions – ``run_producer`` and ``run_consumer`` –
that block indefinitely and print every message they send/receive.

Import ``BOOTSTRAP_SERVER`` and ``TOPIC`` from ``config.py`` so the connection
settings stay in one place.
"""
from __future__ import annotations

import sys
import time
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

from config import BOOTSTRAP_SERVER, TOPIC


def _setup_logging() -> None:
    """Configure basic stdout logging for demo/debug purposes."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )


# ----------------------------- PRODUCER ------------------------------------ #

def run_producer(sleep_seconds: int = 5) -> None:  # pragma: no cover
    """Continuously send timestamp messages to the Kafka topic."""
    _setup_logging()
    logging.info("Initializing producer ...")
    producer: KafkaProducer | None = None
    while producer is None:  # retry until broker reachable
        try:
            producer = KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVER,
                security_protocol='PLAINTEXT',
                api_version=(2, 6, 0)
            )
        except NoBrokersAvailable:
            logging.warning("Broker unavailable – retrying in %s s", sleep_seconds)
            time.sleep(sleep_seconds)

    logging.info("Producer ready. Entering send loop → topic '%s'", TOPIC)
    try:
        while True:
            msg = f"Data packet sent by rajnish at {time.ctime()}".encode()
            producer.send(TOPIC, msg)
            producer.flush()
            logging.info("[PRODUCER] -> %s", msg.decode())
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        logging.info("Producer interrupted; closing…")
    finally:
        producer.close()


# ----------------------------- CONSUMER ------------------------------------ #

def run_consumer() -> None:  # pragma: no cover
    """Consume messages from the Kafka topic and print them."""
    _setup_logging()
    logging.info("Initializing consumer …")
    consumer: KafkaConsumer | None = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVER,
                auto_offset_reset="earliest",
                group_id="demo-group",
                security_protocol='PLAINTEXT',
                api_version=(2, 6, 0)
            )
        except NoBrokersAvailable:
            logging.warning("Broker unavailable – retrying in 5 s")
            time.sleep(5)

    logging.info("Consumer ready. Waiting for records on '%s'", TOPIC)
    try:
        for msg in consumer:
            logging.info("[CONSUMER] <- %s", msg.value.decode())
    except KeyboardInterrupt:
        logging.info("Consumer interrupted; closing…")
    finally:
        consumer.close()
