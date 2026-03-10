"""Shared Kafka configuration for producer and consumer scripts."""

# Kafka connection settings
BOOTSTRAP_SERVER: list[str] = [
    "20.121.149.203:9094"
]

# Kafka topic to publish/consume
TOPIC: str = "test-pipeline"

# Authentication: PLAINTEXT (no credentials required)
