from datetime import datetime, timezone
from fileinput import filename
from pathlib import PurePosixPath
from uuid import uuid4
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.s3 import upload_csv
from app.sqs import publish_event
from app.schemas import (
    ErrorBody,
    HealthResponse,
    StockStatementPayload,
    StockStatementReceived,
    UploadAccepted,
)

app = FastAPI(title="upload-service")


def _error(
    status: int, code: str, message: str, details: dict | None = None
) -> JSONResponse:
    body = ErrorBody(code=code, message=message, details=details)
    return JSONResponse(status_code=status, content=body.model_dump())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post(
    "/uploads",
    response_model=UploadAccepted,
    status_code=202,
    responses={
        400: {"model": ErrorBody},
        413: {"model": ErrorBody},
        415: {"model": ErrorBody},
    },
)
async def upload(file: UploadFile | None = File(None)) -> UploadAccepted | JSONResponse:
    settings = get_settings()

    if file is None or not file.filename:
        return _error(400, "MISSING FILE", "Arquivo é obrigatório")

    filename = PurePosixPath(file.filename).name

    if (
        filename != file.filename
        or ".." in file.filename
        or "/" in file.filename
        or "\\" in file.filename
    ):
        return _error(400, "INVALID_FILENAME", "Nome de arquivo inválido")

    if not filename.lower().endswith(".csv"):
        return _error(415, "UNSUPPORTED_MEDIA_TYPE", "Apenas arquivos .csv são aceitos")

    body = await file.read()

    if len(body) > settings.MAX_UPLOAD_BYTES:
        return _error(
            413,
            "PAYLOAD_TOO_LARGE",
            "Arquivo excede o tamanho máximo",
            {"max_upload_bytes": settings.MAX_UPLOAD_BYTES},
        )

    file_id = str(uuid4())
    event_id = str(uuid4())
    s3_key = f"stock-statements/{file_id}.csv"

    upload_csv(settings.S3_BUCKET, s3_key, body)

    event = StockStatementReceived(
        event_id=event_id,
        occurred_at=datetime.now(timezone.utc),
        payload=StockStatementPayload(
            file_id=file_id,
            s3_bucket=settings.S3_BUCKET,
            s3_key=s3_key,
            original_filename=filename,
        ),
    )
    publish_event(settings.SQS_QUEUE_URL, event)

    return UploadAccepted(file_id=file_id, s3_key=s3_key, event_id=event_id)
