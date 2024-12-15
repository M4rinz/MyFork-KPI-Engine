from aiokafka.admin import AIOKafkaAdminClient


async def delete_kafka_topic(topic_name, bootstrap_servers):
    """Delete a Kafka topic."""
    admin_client = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    try:
        await admin_client.start()
        await admin_client.delete_topics([topic_name])
    except Exception as e:
        print(f"Error deleting topic '{topic_name}': {e}")
