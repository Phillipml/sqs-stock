import logging
import time

import boto3
from pydantic import ValidationError

from app.config import get_settings
from app.csv_parser import parse_stock_csv
from app.repository import StockRepository
from app.s3 import download_bytes
from app.schemas import StockStatementReceived

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("stock-worker")


def _delta(movement_type: str, quantity: int) -> int:
    return quantity if movement_type == "IN" else -quantity


def process_message(body: str, repo: StockRepository) -> None:
    event = StockStatementReceived.model_validate_json(body)
    event_id = event.event_id
    file_id = event.payload.file_id
    log.info("processing event_id=%s file_id=%s", event_id, file_id)

    if repo.already_processed(event_id):
        log.info("skip already processed event_id=%s", event_id)
        return

    raw = download_bytes(event.payload.s3_bucket, event.payload.s3_key)
    movements = parse_stock_csv(raw)

    for m in movements:
        new_qty = repo.apply_movement(m.sku, _delta(m.movement_type, m.quantity))
        log.info(
            "sku=%s delta=%s quantity=%s",
            m.sku,
            _delta(m.movement_type, m.quantity),
            new_qty,
        )

    repo.mark_processed(event_id, file_id)
    log.info("done event_id=%s file_id=%s", event_id, file_id)


def run() -> None:
    settings = get_settings()
    sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
    repo = StockRepository()
    log.info("worker started queue=%s", settings.SQS_QUEUE_URL)

    while True:
        resp = sqs.receive_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=60,
        )
        messages = resp.get("Messages", [])
        if not messages:
            continue

        msg = messages[0]
        receipt = msg["ReceiptHandle"]
        try:
            process_message(msg["Body"], repo)
            sqs.delete_message(QueueUrl=settings.SQS_QUEUE_URL, ReceiptHandle=receipt)
        except (ValidationError, ValueError, Exception) as exc:
            log.exception("failed to process message: %s", exc)


if __name__ == "__main__":
    run()
