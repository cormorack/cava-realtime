import warnings
from confluent_kafka.admin import AdminClient


def get_available_topics(conf: dict):
    """Get available topics listing found in kafka cluster"""
    available_topics = {}
    try:
        consumer = AdminClient(conf)
        available_topics = consumer.list_topics().topics
    except Exception as e:
        warnings.warn(e)

    return available_topics
