import configparser
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common.serialization import SimpleStringSchema
import logging

def load_kafka_config(config_file):
    """Load Kafka configuration from a properties file."""
    config = configparser.ConfigParser()
    config.read(config_file)

    # Return a dictionary of Kafka properties (excluding schema.registry.url if not used)
    kafka_properties = {
        'bootstrap.servers': config.get('default', 'bootstrap.servers'),
        'security.protocol': config.get('default', 'security.protocol'),
        'sasl.mechanisms': config.get('default', 'sasl.mechanisms'),
        'sasl.username': config.get('default', 'sasl.username'),
        'sasl.password': config.get('default', 'sasl.password'),
        'group.id': config.get('default', 'group.id'),
        'schema.registry.url': config.get('default', 'schema.registry.url')
    }

    # Log Kafka properties for debugging
    logging.info(f"Loaded Kafka configuration: {kafka_properties}")

    return kafka_properties

def process_soccer_data():
    """Flink job to process soccer data."""
    try:
        # Load Kafka configuration
        kafka_config = load_kafka_config('/flink/config/client.properties')

        # Initialize Flink execution environment
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(1)  # Adjust based on your environment and use case

        # Configure Kafka Consumer
        kafka_consumer = FlinkKafkaConsumer(
            topics='topic_livescores',
            deserialization_schema=SimpleStringSchema(),  # Assuming messages are plain strings
            properties=kafka_config
        )

        # Add the Kafka source
        stream = env.add_source(kafka_consumer)

        # Example transformation: Append "Processed" to each value
        processed_stream = stream.map(lambda value: f"Processed: {value}")

        # Configure Kafka Producer
        kafka_producer = FlinkKafkaProducer(
            topic='topic_livescores_processed',
            serialization_schema=SimpleStringSchema(),  # Assuming processed data is plain strings
            producer_config=kafka_config
        )

        # Add the Kafka sink
        processed_stream.add_sink(kafka_producer)

        # Execute the Flink job
        env.execute('Soccer Data Processing')
    except Exception as e:
        logging.error(f"Error in processing soccer data: {e}", exc_info=True)

if __name__ == "__main__":
    process_soccer_data()