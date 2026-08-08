from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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


class StockMovement(BaseModel):
    sku: str
    movement_type: Literal["IN", "OUT"]
    quantity: int = Field(gt=0)
    occurred_at: datetime

    @field_validator("sku")
    @classmethod
    def sku_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("sku vazio")
        return v
