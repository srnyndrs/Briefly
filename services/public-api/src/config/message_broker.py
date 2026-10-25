import pika

from src.config.settings import settings


def create_connection_parameters() -> pika.URLParameters:
    params = pika.URLParameters(settings.rabbitmq_url)
    params.blocked_connection_timeout = settings.blocked_timeout_seconds

    return params
