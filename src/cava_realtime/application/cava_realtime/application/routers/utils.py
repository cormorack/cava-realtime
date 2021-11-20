import warnings
from uuid import uuid4
from confluent_kafka import Consumer


def get_available_topics(conf: dict):
    """Get available topics listing found in kafka cluster"""
    available_topics = {}
    try:
        if 'group.id' not in conf:
            uid = uuid4().hex
            conf = conf.copy()
            conf.update({'group.id': uid})

        consumer = Consumer(conf)
        available_topics = {
            k: v
            for k, v in consumer.list_topics().topics.items()
            if '__consumer_offsets' not in k
        }
    except Exception as e:
        warnings.warn(e)

    return available_topics
