# sqs-stock

Pipeline assíncrono de estoque: upload de CSV → S3 + evento SQS → worker → saldo no MongoDB. Infra local com Docker; filas e objetos na AWS.

```
CSV → upload-service → S3 + SQS → stock-worker → MongoDB
Infra: Docker → ECR → ECS
```

## Tecnologias utilizadas

- **Python 3.11+** / **FastAPI** / **Uvicorn** — `upload-service`
- **Python** / **boto3** / **pymongo** — `stock-worker`
- **pydantic / pydantic-settings** — schemas e config tipados
- **MongoDB 8** — estoque local via Docker Compose
- **Amazon S3** — armazenamento do CSV
- **Amazon SQS** — fila + DLQ para eventos (consumida pelo worker local)
- **Docker / Docker Compose** — Mongo local; depois containerização dos serviços
- **AWS ECR + ECS Fargate** — deploy (planejado)

## Decisões técnicas

### Banco de dados

MongoDB para o saldo por `sku` (`products`) e idempotência por `event_id` (`processed_events`). Upsert com `$inc` aplica `IN`/`OUT`. Índices unique em `sku` e `event_id` evitam duplicar estoque em reentrega da fila.

### Integração com eventos (S3 + SQS)

O CSV fica no S3; a SQS só carrega metadados (`StockStatementReceived` v1 em `docs/sqs-event.md`). O `upload-service` publica; o `stock-worker` faz long poll, baixa o CSV, atualiza o Mongo e só então deleta a mensagem. Falha → não deleta → retry → DLQ após 3 receives. Não há integração com LLM neste projeto.

### Multi-tenancy

Não aplicável neste lab: um bucket, uma fila e um banco. Isolamento por tenant ficaria para evolução (prefixos S3 / filas / DB por tenant).

### Desafios e como resolveu

| Desafio | Abordagem |
|---|---|
| Contrato entre serviços | Evento versionado em `docs/sqs-event.md` |
| Mensagens que falham | DLQ `maxReceiveCount=3`; worker só deleta após sucesso |
| Reentrega / duplicata | `processed_events` por `event_id` — skip sem reaplicar saldo |
| Secrets no git | `.env` local; credenciais AWS em `~/.aws` |
| PowerShell `curl` | Usar `curl.exe` |
| Ver msg na fila com worker ligado | Msg some rápido; pare o worker para inspecionar no Console |
| Compass “desatualizado” | Refresh manual — GUI não faz live reload |

## Estado atual (branch `04-stock-worker`)

Fluxo local completo: upload → S3/SQS (AWS) → worker → Mongo (Docker).

```
sqs-stock/
├── docker-compose.yml
├── .env.example
├── docs/sqs-event.md
├── infra/README.md
├── samples/stock-example.csv
├── upload-service/
│   ├── requirements.txt
│   └── app/ (config, schemas, s3, sqs, main)
├── stock-worker/
│   ├── requirements.txt
│   └── app/ (config, schemas, s3, csv_parser, repository, worker)
└── README.md
```

### Infra AWS (lab)

| Recurso | Config |
|---|---|
| Region | `us-east-1` |
| S3 | bucket privado, Block Public Access, SSE-S3 |
| SQS | `sqs-stock-statements` — visibility 60s, long poll 20s |
| DLQ | `sqs-stock-statements-dlq` — max receives = 3 |

Preencha `S3_BUCKET`, `SQS_QUEUE_URL`, `MONGO_URI`, `MONGO_DB` no `.env` (nunca no git).

## Funcionalidades implementadas

### Obrigatórias (entregue até agora)

- [x] Mongo local via Docker Compose
- [x] Contrato do evento SQS documentado
- [x] Sample CSV de movimentos (`IN` / `OUT`)
- [x] Bucket S3 privado com encryption
- [x] Fila SQS + DLQ configuradas
- [x] Variáveis locais em `.env` / `.env.example`
- [x] `upload-service` — `GET /health`, `POST /uploads` → S3 + SQS (202)
- [x] Validação de arquivo (`.csv`, tamanho, nome)
- [x] `stock-worker` — consome SQS, baixa S3, parse CSV, atualiza Mongo
- [x] Idempotência por `event_id` (`processed_events`)
- [x] Delete na fila só após sucesso

### Pendentes / diferenciais

- [ ] E2E documentado em `docs/e2e.md` (branch `05`)
- [ ] Dockerize dos serviços
- [ ] Deploy ECR + ECS
- [ ] Smoke pós-deploy

## Setup rápido

```powershell
cd sqs-stock
copy .env.example .env
# preencha S3_BUCKET e SQS_QUEUE_URL
docker compose up -d
aws sts get-caller-identity
```

### Terminal A — upload-service

```powershell
cd upload-service
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Terminal B — stock-worker

```powershell
cd stock-worker
.\.venv\Scripts\activate
python -m app.worker
```

Log esperado: `worker started queue=https://sqs.us-east-1.amazonaws.com/...`

### Terminal C — enviar CSV

```powershell
cd d:\01-code\00-AWS\SQS\sqs-stock
curl.exe -X POST "http://localhost:8000/uploads" -F "file=@samples/stock-example.csv"
```

Esperado: **202** + logs no worker (`processing` → `done`).

### Conferir Mongo

```powershell
docker compose exec mongo mongosh --eval "db.getSiblingDB('stock').products.find().toArray()"
```

Sample (`stock-example.csv`): por upload → `SKU-001 +7`, `SKU-002 +5`.

No Compass: dar **Refresh** na collection — a GUI não atualiza sozinha.

### Ver mensagem na SQS (opcional)

1. Pare o worker  
2. Faça o upload  
3. Console → SQS → `sqs-stock-statements` → **Poll for messages**  
4. Suba o worker de novo → msg some e Mongo atualiza  

Sem consumer a mensagem **fica** na fila (não vai à DLQ sozinha).

## Branches do dia

| Branch | Foco |
|---|---|
| `01-scaffold` | Compose, contrato, sample |
| `02-infra-aws` | S3 + SQS + DLQ |
| `03-upload-service` | API de upload |
| `04-stock-worker` | Consumer + Mongo ← **atual** |
| `05-e2e-local` | Fluxo ponta a ponta documentado |
| `06-dockerize` | Dockerfiles + compose |
| `07-ecr-ecs` | Deploy AWS |
| `08-docs` | Docs e smoke final |
