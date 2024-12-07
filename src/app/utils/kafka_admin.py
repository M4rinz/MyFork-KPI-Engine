from aiokafka.admin import AIOKafkaAdminClient


async def delete_kafka_topic(topic_name, bootstrap_servers):
    """Delete a Kafka topic."""
    admin_client = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    await admin_client.start()
    try:
        await admin_client.delete_topics([topic_name])
        print(f"Topic '{topic_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting topic '{topic_name}': {e}")
