import csv
import io
from datetime import datetime

from app.schemas import StockMovement

REQUIRED_HEADER = ["sku", "movement_type", "quantity", "occurred_at"]


def parse_stock_csv(body: bytes) -> list[StockMovement]:
    text = body.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ValueError("CSV sem header")

    header = [h.strip() for h in reader.fieldnames]
    if header != REQUIRED_HEADER:
        raise ValueError(f"Header inválido: {header}")

    movements: list[StockMovement] = []
    for i, row in enumerate(reader, start=2):
        try:
            movements.append(
                StockMovement(
                    sku=row["sku"],
                    movement_type=row["movement_type"].strip().upper(),
                    quantity=int(row["quantity"]),
                    occurred_at=datetime.fromisoformat(
                        row["occurred_at"].strip().replace("Z", "+00:00")
                    ),
                )
            )
        except Exception as exc:
            raise ValueError(f"Linha {i} inválida: {exc}") from exc

    if not movements:
        raise ValueError("CSV sem movimentos")

    return movements
