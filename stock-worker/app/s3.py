import boto3

from app.config import get_settings

ALLOWED_PREFIX = "stock-statements/"


def download_bytes(bucket: str, key: str) -> bytes:
    if not key.startswith(ALLOWED_PREFIX):
        raise ValueError(f"s3_key inválida: {key}")

    settings = get_settings()
    client = boto3.client("s3", region_name=settings.AWS_REGION)
    obj = client.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()
