# Infra lab

- Region: `us-east-1`
- Bucket S3: privado, Block Public Access ON, encryption SSE-S3
- Queue: `sqs-stock-statements` — visibility 60s, long poll 20s, SSE-SQS
- DLQ: `sqs-stock-statements-dlq` — maxReceiveCount = 3

Nomes reais de bucket/URL ficam no `.env` local (não versionado).

## Notas

- Mensagem **sem consumer** permanece na fila principal (não cai na DLQ sozinha).
- DLQ só após N receives sem `DeleteMessage` (N = 3).
- Poll repetido no Console conta como receive — pode empurrar para a DLQ.
