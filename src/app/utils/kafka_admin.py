from aiokafka.admin import AIOKafkaAdminClient


async def delete_kafka_topic(topic_name, bootstrap_servers):
    """Deletes a Kafka topic asynchronously.

    This function connects to a Kafka cluster using the provided bootstrap servers,
    and deletes the specified topic. It uses the `AIOKafkaAdminClient` for asynchronous 
    operations.

    :param topic_name: The name of the Kafka topic to delete.
    :type topic_name: str
    :param bootstrap_servers: A list or string of Kafka bootstrap servers to connect to.
    :type bootstrap_servers: str or list of str
    :raises Exception: If there is an error while deleting the topic, an exception is raised.
    :return: None
    :rtype: None
    """
    admin_client = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    await admin_client.start()
    try:
        await admin_client.delete_topics([topic_name])
        print(f"Topic '{topic_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting topic '{topic_name}': {e}")
