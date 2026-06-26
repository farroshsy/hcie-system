from app.workers.learning_consumer import LearningConsumerService
from app.infrastructure.v3.v3_client import get_v3_client


def test_learning_consumer_can_get_v3_client():
    """Verify learning consumer can get V3 client"""
    client = get_v3_client()
    assert client is not None
    assert client.base_url is not None
