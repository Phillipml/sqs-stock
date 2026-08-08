# Evento StockStatementReceived v1

Quando um CSV é aceito pelo `upload-service`, a mensagem na SQS é:

```json
{
  "event_id": "uuid",
  "event_type": "StockStatementReceived",
  "schema_version": "1",
  "occurred_at": "2026-08-05T12:00:00Z",
  "payload": {
    "file_id": "uuid",
    "s3_bucket": "nome-do-bucket",
    "s3_key": "stock-statements/{file_id}.csv",
    "original_filename": "estoque.csv"
  }
}
```

## CSV esperado

```text
sku,movement_type,quantity,occurred_at
SKU-001,IN,10,2026-08-05T10:00:00Z
```

- `movement_type`: `IN` | `OUT`
- `quantity`: inteiro > 0

Sample: `samples/stock-example.csv`
