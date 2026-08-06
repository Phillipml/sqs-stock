# sqs-stock

Pipeline assíncrono de estoque: upload de CSV → S3 + evento SQS → worker → saldo no MongoDB. Infra local com Docker; filas e objetos na AWS.

```
CSV → upload-service → S3 + SQS → stock-worker → MongoDB
Infra: Docker → ECR → ECS
```

## Tecnologias utilizadas

- **Python 3.11+** / **FastAPI** / **Uvicorn** — `upload-service`
- **boto3** — S3 (`put_object`) e SQS (`send_message`)
- **pydantic / pydantic-settings** — schemas e config tipados
- **MongoDB 8** — estoque local via Docker Compose (consumo na etapa do worker)
- **Amazon S3** — armazenamento do CSV
- **Amazon SQS** — fila + DLQ para eventos
- **Docker / Docker Compose** — Mongo local; depois containerização dos serviços
- **AWS ECR + ECS Fargate** — deploy (planejado)

## Decisões técnicas

### Banco de dados

MongoDB para o saldo por `sku` e para idempotência (`processed_events` por `event_id`). Modelo documental encaixa em upsert de quantidade e evita schema rígido no lab. Índice unique em `sku` e em `event_id` evita duplicar estoque em reentrega da fila. O worker que grava no Mongo ainda não existe (branch `04`).

### Integração com eventos (S3 + SQS)

O CSV fica no S3; a SQS só carrega metadados (`StockStatementReceived` v1 em `docs/sqs-event.md`). Desacopla upload do processamento, permite retry e DLQ após 3 falhas. Não há integração com LLM neste projeto.

### Multi-tenancy

Não aplicável neste lab: um bucket, uma fila e um banco. Isolamento por tenant ficaria para evolução (prefixos S3 / filas / DB por tenant).

### Desafios e como resolveu

| Desafio | Abordagem |
|---|---|
| Contrato entre serviços | Evento versionado em `docs/sqs-event.md` antes do worker |
| Mensagens que falham | DLQ com `maxReceiveCount=3`; worker só deleta após sucesso |
| Secrets no git | `.env` local; credenciais AWS em `~/.aws` (Access Key), nunca no repo |
| PowerShell `curl` | Usar `curl.exe` — o alias aponta para `Invoke-WebRequest` |
| Credencial `login` / CRT | Preferir Access Key clássica no IAM user de lab |
| Mensagem sem consumer | Fica na fila principal; **não** vai à DLQ sozinha |

## Estado atual (branch `03-upload-service`)

Infra AWS + `upload-service` operacional: CSV → S3 + mensagem SQS. Sem `stock-worker` ainda.

```
sqs-stock/
├── docker-compose.yml
├── .env.example
├── docs/sqs-event.md
├── infra/README.md
├── samples/stock-example.csv
├── upload-service/
│   ├── requirements.txt
│   └── app/
│       ├── config.py
│       ├── schemas.py
│       ├── s3.py
│       ├── sqs.py
│       └── main.py
└── README.md
```

### Infra AWS (lab)

| Recurso | Config |
|---|---|
| Region | `us-east-1` |
| S3 | bucket privado, Block Public Access, SSE-S3 |
| SQS | `sqs-stock-statements` — visibility 60s, long poll 20s |
| DLQ | `sqs-stock-statements-dlq` — max receives = 3 |

Preencha `S3_BUCKET` e `SQS_QUEUE_URL` no `.env` (nunca no git).

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

### Pendentes / diferenciais

- [ ] `stock-worker` — consome fila, parse CSV, atualiza Mongo
- [ ] Idempotência por `event_id`
- [ ] E2E local documentado
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

### Rodar o upload-service

```powershell
cd upload-service
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Testar upload (PowerShell)

```powershell
curl.exe http://localhost:8000/health

cd ..   # raiz do repo
curl.exe -X POST "http://localhost:8000/uploads" -F "file=@samples/stock-example.csv"
```

Esperado: **202** com `file_id`, `s3_key`, `event_id`, `status: accepted`.

Conferir:

- S3 → `stock-statements/{file_id}.csv`
- SQS Console → fila → **Send and receive messages** → **Poll for messages**
- Swagger → `http://localhost:8000/docs`

## Branches do dia

| Branch | Foco |
|---|---|
| `01-scaffold` | Compose, contrato, sample |
| `02-infra-aws` | S3 + SQS + DLQ |
| `03-upload-service` | API de upload ← **atual** |
| `04-stock-worker` | Consumer + Mongo |
| `05-e2e-local` | Fluxo ponta a ponta |
| `06-dockerize` | Dockerfiles + compose |
| `07-ecr-ecs` | Deploy AWS |
| `08-docs` | Docs e smoke final |
