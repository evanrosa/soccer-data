import time
import logging
import io
from fastavro import writer, parse_schema, reader
from confluent_kafka import Producer, Consumer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Define the Avro schema
schema = {
    "type": "record",
    "name": "SoccerMatch",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "sport_id", "type": "int"},
        {"name": "league_id", "type": "int"},
        {"name": "season_id", "type": "int"},
        {"name": "stage_id", "type": "int"},
        {"name": "group_id", "type": ["null", "int"], "default": None},
        {"name": "aggregate_id", "type": ["null", "int"], "default": None},
        {"name": "round_id", "type": "int"},
        {"name": "state_id", "type": "int"},
        {"name": "venue_id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "starting_at", "type": ["null", "string"], "default": None},
        {"name": "result_info", "type": ["null", "string"], "default": None},
        {"name": "leg", "type": "string"},
        {"name": "details", "type": ["null", "string"], "default": None},
        {"name": "length", "type": "int"},
        {"name": "placeholder", "type": "boolean"},
        {"name": "has_odds", "type": "boolean"},
        {"name": "has_premium_odds", "type": "boolean"},
        {"name": "starting_at_timestamp", "type": "long"}
    ]
}
parsed_schema = parse_schema(schema)

def serialize_avro(record, schema):
    """Serialize a Python dictionary into Avro bytes."""
    try:
        bytes_writer = io.BytesIO()
        writer(bytes_writer, schema, [record])
        return bytes_writer.getvalue()
    except Exception as e:
        logging.error(f"Error serializing record: {record}. Exception: {e}")
        raise

def deserialize_avro(message_value):
    """Deserialize Avro bytes into a Python dictionary."""
    try:
        bytes_reader = io.BytesIO(message_value)
        return list(reader(bytes_reader))[0]
    except Exception as e:
        logging.error(f"Error deserializing Avro message. Exception: {e}")
        raise

def read_config(file_path="config/client.properties"):
    """Reads the client configuration from a properties file."""
    config = {}
    try:
        with open(file_path) as fh:
            for line in fh:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Ensure the line contains '='
                if '=' not in line:
                    logging.warning(f"Skipping invalid config line: {line}")
                    continue
                parameter, value = line.split('=', 1)
                config[parameter.strip()] = value.strip()
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {file_path}.")
    except Exception as e:
        logging.error(f"Error reading configuration file: {e}")
    return config

def produce_message(topic, config, key, value):
    """Produces an Avro message to the specified Kafka topic."""
    producer = Producer(config)
    try:
        # Serialize value into Avro format
        avro_value = serialize_avro(value, parsed_schema)

        # Produce the message to Kafka
        producer.produce(topic, key=str(key), value=avro_value)
        producer.flush()  # Ensure the message is delivered
        logging.info(f"Produced Avro message to topic {topic}: key={key}, value={value}")
    except Exception as e:
        logging.error(f"Error producing message to topic {topic}. Key: {key}, Value: {value}. Exception: {e}")

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
                continue  # No message received
            if msg.error():
                logging.error(f"Consumer error: {msg.error()}")
                continue

            # Deserialize Avro message
            try:
                value = deserialize_avro(msg.value())
                logging.info(f"Consumed Avro message: value={value}")
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
    # Read Kafka configuration
    kafka_config = read_config(file_path="config/client.properties")
    
    # Kafka topic to consume from
    topic = "topic_livescores"  # Replace with your topic name if different

    # Start consuming messages
    consume_messages(topic, kafka_config)
