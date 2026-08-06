import boto3
from app.config import get_settings


def upload_csv(bucket: str, key: str, body: bytes) -> None:
    settings = get_settings()
    client = boto3.client("s3", region_name=settings.AWS_REGION)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="text/csv",
    )
