import random
import time
import logging
import io
from fastavro import writer, parse_schema
from confluent_kafka import Producer

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


def produce_message(topic, config, key, value):
    """Produces an Avro message to the specified Kafka topic."""
    producer = Producer(config)
    try:
        avro_value = serialize_avro(value, parsed_schema)
        producer.produce(topic, key=str(key), value=avro_value)
        producer.flush()
        logging.info(f"Produced Avro message to topic {topic}: key={key}, value={value}")
    except Exception as e:
        logging.error(f"Error producing message to topic {topic}. Key: {key}, Value: {value}. Exception: {e}")

if __name__ == "__main__":
    kafka_config = read_config(file_path="config/client.properties")
    topic = "topic_livescores"
    test_message = {
        "id": 1,
        "sport_id": 1,
        "league_id": 123,
        "season_id": 2023,
        "stage_id": 456,
        "group_id": None,
        "aggregate_id": None,
        "round_id": 1,
        "state_id": 1,
        "venue_id": 1001,
        "name": "Test Match",
        "starting_at": None,
        "result_info": None,
        "leg": "first",
        "details": None,
        "length": 90,
        "placeholder": False,
        "has_odds": True,
        "has_premium_odds": False,
        "starting_at_timestamp": int(time.time())
    }
for i in range(10):
    test_message["id"] = i
    test_message["name"] = f"Match {i}"
    test_message["starting_at_timestamp"] = int(time.time()) + random.randint(0, 3600)
    produce_message(topic, kafka_config, key=test_message["id"], value=test_message)
    time.sleep(1)  # Simulate a delay
