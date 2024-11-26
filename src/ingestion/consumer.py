import logging
import io
from fastavro import reader
from confluent_kafka import Consumer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def deserialize_avro(message_value):
    """Deserialize Avro bytes into a Python dictionary."""
    try:
        bytes_reader = io.BytesIO(message_value)
        return list(reader(bytes_reader))[0]  # Properly deserialize using fastavro
    except Exception as e:
        logging.error(f"Error deserializing Avro message: {e}")
        logging.error(f"Raw message: {message_value}")
        raise

def read_config(file_path="config/client.properties"):
    """Reads the client configuration from a properties file."""
    config = {}
    try:
        with open(file_path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if '=' not in line:
                    logging.warning(f"Skipping invalid config line: {line}")
                    continue
                parameter, value = line.split('=', 1)
                config[parameter.strip()] = value.strip()

        # Remove invalid or unused properties for Producer
        if 'schema.registry.url' in config:
            del config['schema.registry.url']

    except FileNotFoundError:
        logging.error(f"Configuration file not found at {file_path}.")
    return config

def consume_messages(topic, config):
    """Consumes Avro messages from the specified Kafka topic."""
    config["group.id"] = "python-group-1"
    config["auto.offset.reset"] = "earliest"

    consumer = Consumer(config)
    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logging.error(f"Consumer error: {msg.error()}")
                continue

            try:
                # Deserialize Avro message
                value = deserialize_avro(msg.value())
                logging.info(f"Consumed Avro message: {value}")
            except Exception as e:
                logging.error(f"Error deserializing Avro message. Raw message: {msg.value()}. Exception: {e}")
    except KeyboardInterrupt:
        logging.info("Consumer interrupted by user.")
    except Exception as e:
        logging.error(f"Unexpected error in consumer: {e}")
    finally:
        consumer.close()
        logging.info("Consumer closed.")

if __name__ == "__main__":
    kafka_config = read_config(file_path="config/client.properties")
    topic = "topic_livescores"
    consume_messages(topic, kafka_config)
