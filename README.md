# sqs-stock

Pipeline assíncrono de estoque: upload de CSV → S3 + evento SQS → worker → saldo no MongoDB. Infra local com Docker; filas e objetos na AWS.

```
CSV → upload-service → S3 + SQS → stock-worker → MongoDB
Infra: Docker → ECR → ECS
```

## Tecnologias utilizadas

- **Python 3.11+** (serviços — etapas seguintes)
- **FastAPI / Uvicorn** — upload-service (planejado)
- **boto3** — S3 e SQS
- **MongoDB 8** — estoque local via Docker Compose
- **Amazon S3** — armazenamento do CSV
- **Amazon SQS** — fila + DLQ para eventos
- **Docker / Docker Compose** — Mongo local; depois containerização dos serviços
- **AWS ECR + ECS Fargate** — deploy (planejado)

## Decisões técnicas

### Banco de dados

MongoDB para o saldo por `sku` e para idempotência (`processed_events` por `event_id`). Modelo documental encaixa em upsert de quantidade e evita schema rígido no lab. Índice unique em `sku` e em `event_id` evita duplicar estoque em reentrega da fila.

### Integração com eventos (S3 + SQS)

O CSV fica no S3; a SQS só carrega metadados (`StockStatementReceived` v1 em `docs/sqs-event.md`). Desacopla upload do processamento, permite retry e DLQ após 3 falhas. Não há integração com LLM neste projeto.

### Multi-tenancy

Não aplicável neste lab: um bucket, uma fila e um banco. Isolamento por tenant ficaria para evolução (prefixos S3 / filas / DB por tenant).

### Desafios e como resolveu

| Desafio | Abordagem |
|---|---|
| Contrato entre serviços | Evento versionado em `docs/` antes do código |
| Mensagens que falham | DLQ com `maxReceiveCount=3`; worker só deleta após sucesso |
| Secrets no git | `.env` local; `.gitignore` já ignora `.env` |
| Infra antes do código | Branch `02-infra-aws` cria S3/SQS sem microsserviços ainda |

## Estado atual (branch `02-infra-aws`)

Scaffold local + infra AWS. Sem `upload-service` / `stock-worker` ainda.

```
sqs-stock/
├── docker-compose.yml      # Mongo local
├── docs/sqs-event.md       # Contrato do evento
├── samples/stock-example.csv
├── .env                    # local, não versionado
└── README.md
```

### Infra AWS (lab)

| Recurso | Config |
|---|---|
| Region | `us-east-1` |
| S3 | bucket privado, Block Public Access, SSE-S3 |
| SQS | `sqs-stock-statements` — visibility 60s, long poll 20s |
| DLQ | `sqs-stock-statements-dlq` — max receives = 3 |

Preencha `S3_BUCKET` e `SQS_QUEUE_URL` no `.env` local (nunca no git).

## Funcionalidades implementadas

### Obrigatórias (entregue até agora)

- [x] Mongo local via Docker Compose
- [x] Contrato do evento SQS documentado
- [x] Sample CSV de movimentos (`IN` / `OUT`)
- [x] Bucket S3 privado com encryption
- [x] Fila SQS + DLQ configuradas
- [x] Variáveis locais em `.env` (fora do git)

### Pendentes / diferenciais

- [ ] `upload-service` — `POST /uploads` → S3 + SQS
- [ ] `stock-worker` — consome fila, parse CSV, atualiza Mongo
- [ ] Idempotência por `event_id`
- [ ] E2E local documentado
- [ ] Dockerize dos serviços
- [ ] Deploy ECR + ECS
- [ ] README final pós-deploy (smoke)

## Setup rápido (máquina)

```powershell
cd sqs-stock
copy .env.example .env   # se existir; senão use o .env local já preenchido
docker compose up -d
docker compose ps
aws sts get-caller-identity
```

## Branches do dia

| Branch | Foco |
|---|---|
| `01-scaffold` | Compose, contrato, sample |
| `02-infra-aws` | S3 + SQS + DLQ ← **atual** |
| `03-upload-service` | API de upload |
| `04-stock-worker` | Consumer + Mongo |
| `05-e2e-local` | Fluxo ponta a ponta |
| `06-dockerize` | Dockerfiles + compose |
| `07-ecr-ecs` | Deploy AWS |
| `08-docs` | Docs e smoke final |
