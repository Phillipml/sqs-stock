from pymongo import ASCENDING, MongoClient, ReturnDocument

from app.config import get_settings


class StockRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = MongoClient(settings.MONGO_URI)
        self._db = self._client[settings.MONGO_DB]
        self._products = self._db["products"]
        self._events = self._db["processed_events"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._products.create_index([("sku", ASCENDING)], unique=True)
        self._events.create_index([("event_id", ASCENDING)], unique=True)

    def already_processed(self, event_id: str) -> bool:
        return self._events.find_one({"event_id": event_id}) is not None

    def mark_processed(self, event_id: str, file_id: str) -> None:
        self._events.insert_one({"event_id": event_id, "file_id": file_id})

    def apply_movement(self, sku: str, delta: int) -> int:
        doc = self._products.find_one_and_update(
            {"sku": sku},
            {"$inc": {"quantity": delta}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(doc["quantity"])
