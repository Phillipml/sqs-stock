import boto3

from app.config import get_settings
from app.schemas import StockStatementReceived


def publish_event(queue_url: str, event: StockStatementReceived) -> str:
    settings = get_settings()
    client = boto3.client("sqs", region_name=settings.AWS_REGION)
    response = client.send_message(
        QueueUrl=queue_url, MessageBody=event.model_dump_json()
    )
    return response["MessageId"]
