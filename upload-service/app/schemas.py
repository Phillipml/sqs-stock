from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class UploadAccepted(BaseModel):
    file_id: str
    s3_key: str
    event_id: str
    status: Literal["accepted"] = "accepted"


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class StockStatementPayload(BaseModel):
    file_id: str
    s3_bucket: str
    s3_key: str
    original_filename: str


class StockStatementReceived(BaseModel):
    event_id: str
    event_type: Literal["StockStatementReceived"] = "StockStatementReceived"
    schema_version: Literal["1"] = "1"
    occurred_at: datetime
    payload: StockStatementPayload
