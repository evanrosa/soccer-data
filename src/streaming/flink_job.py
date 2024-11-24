import configparser
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common.serialization import SimpleStringSchema

def load_kafka_config(config_file):
    """Load Kafka configuration from a properties file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return {
        'bootstrap.servers': config.get('default', 'bootstrap.servers'),
        'security.protocol': config.get('default', 'security.protocol'),
        'sasl.mechanisms': config.get('default', 'sasl.mechanisms'),
        'sasl.username': config.get('default', 'sasl.username'),
        'sasl.password': config.get('default', 'sasl.password'),
        'group.id': config.get('default', 'group.id')
    }

def process_soccer_data():
    # Load Kafka configuration
    kafka_config = load_kafka_config('/Users/evro/non_iCloud_files/Code/python/financial_project/config/client.properties')
    print(kafka_config)

    # Initialize Flink execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # Configure Kafka Consumer
    kafka_consumer = FlinkKafkaConsumer(
        topics='topic_livescores',
        deserialization_schema=SimpleStringSchema(),
        properties=kafka_config
    )

    # Add the Kafka source
    stream = env.add_source(kafka_consumer)

    # Example transformation: Append "Processed" to each value
    processed_stream = stream.map(lambda value: f"Processed: {value}")

    # Configure Kafka Producer
    kafka_producer = FlinkKafkaProducer(
        topic='topic_livescores',
        serialization_schema=SimpleStringSchema(),
        producer_config=kafka_config
    )

    # Add the Kafka sink
    processed_stream.add_sink(kafka_producer)

    # Execute the Flink job
    env.execute('Soccer Data Processing')

if __name__ == "__main__":
    process_soccer_data()
