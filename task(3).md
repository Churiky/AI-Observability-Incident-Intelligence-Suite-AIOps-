# AI Observability & Incident Intelligence Platform

> **Project type:** Production-oriented AI/ML + Backend system  
> **Target roles:** AI Engineer / ML Engineer / Software Engineer / Backend Engineer  
> **Goal:** Build a system that ingests application/system logs and metrics, detects abnormal behavior, identifies incident patterns, estimates severity, correlates related events, and generates an explainable incident report for developers.

---

## 1. Project Overview

Build an **AI-powered observability and incident intelligence platform** for software systems.

Instead of simply displaying logs, the system automatically:

1. Collect logs and time-series metrics.
2. Parse and normalize heterogeneous log formats.
3. Analyze logs in real-time (streaming analysis) and discard normal logs to prevent database bloat.
4. Detect anomalies in application behavior using statistical and ML methods.
5. Persist only anomalies, aggregated metrics, and incidents to PostgreSQL.
6. Group related anomalies into incidents.
7. Classify incident type and severity.
8. Correlate logs, metrics, and temporal patterns using local FAISS vector search.
9. Estimate the likely root cause and generate an incident report using a local LLM via Ollama.
10. Expose all capabilities through a production-style REST API and WebSocket connection.
11. Provide a real-time dashboard for monitoring incidents and system health.

### Core Architecture & Data Flow

```text
[Synthetic Generator] ──(HTTP POST logs/s)──> [FastAPI Ingestion]
                                                    │ (Publish)
                                                    ▼
                                          [Redis Pub/Sub Channel]
                                                    │
                               ┌────────────────────┴────────────────────┐
                               ▼                                         ▼
                     [Streaming Analytics]                    [WebSocket Server]
                  (Redis Sorted Sets + ML)                              │
                               │                                        ▼
                  (If Anomaly / Incident)                      [React Dashboard]
                               │ (Save & Publish)                    (Real-time UI)
                               ▼
               [PostgreSQL] <──┴── [Celery Worker] ──(Query)──> [Ollama (Local LLM)]
                                        │
                                        ▼ (RAG)
                                   [FAISS / Chroma]
```

---

# 2. Main Objectives

The completed project must demonstrate the ability to work across:

### AI / Machine Learning
- Unsupervised anomaly detection
- Supervised classification
- Time-series feature engineering
- Model evaluation
- Feature engineering
- Model inference
- Explainable predictions

### Data Engineering
- Log ingestion
- Data cleaning
- Parsing semi-structured data
- Time-series processing
- Feature pipelines
- Dataset generation
- Data validation

### Backend Engineering
- FastAPI
- REST API design
- Pydantic
- Async processing
- Background jobs
- Error handling
- Authentication-ready architecture
- API documentation

### AI Engineering
- Embeddings
- Semantic similarity
- LLM integration
- Incident summarization
- Root-cause explanation
- Prompt engineering
- AI evaluation

### Software Engineering
- OOP
- Modular architecture
- Repository/service pattern
- Configuration management
- Logging
- Unit/integration testing
- Docker
- Git/GitHub
- CI pipeline

---

# 3. Functional Requirements

## 3.1 Log Ingestion

The system must support:

- JSON logs
- Plain-text logs
- Application logs
- System logs
- HTTP access logs

Example:

```json
{
  "timestamp": "2026-08-16T10:23:41",
  "service": "payment-service",
  "level": "ERROR",
  "message": "Database connection timeout",
  "host": "server-03",
  "request_id": "req_82a91"
}
```

The ingestion layer must:

- Validate input
- Normalize timestamps
- Normalize severity levels
- Extract service name
- Extract request ID where available
- Extract HTTP status code where available
- Extract latency where available
- Publish normalized events to Redis Pub/Sub (channel `log-stream`) for real-time analysis
- Store only events flagged as anomalies, incidents, or aggregated metrics in PostgreSQL to prevent database bloat

---

# 4. Log Parsing Pipeline

Implement a reusable parser:

```text
Raw Log
   ↓
Format Detection
   ↓
Field Extraction
   ↓
Normalization
   ↓
Validation
   ↓
Normalized Event
```

Normalized event schema:

```text
timestamp
service
host
level
message
request_id
status_code
latency_ms
endpoint
exception_type
environment
```

The parser should tolerate missing fields.

---

# 5. Feature Engineering

Create ML features from logs and metrics.

## Log features

- Error count
- Warning count
- Error rate
- Unique exception count
- Message frequency
- Message entropy
- Service error ratio
- Request failure ratio
- Average latency
- P95 latency
- P99 latency

## Time-series features

- Rolling mean
- Rolling standard deviation
- Rate of change
- Moving average
- Difference from baseline
- Z-score
- Seasonal deviation

## Text features

Use embeddings to represent:

```text
log message
exception message
incident description
```

Possible embedding model:

- Sentence Transformers
- OpenAI-compatible embedding API
- Local embedding model

---

# 6. Anomaly Detection

Implement at least **two anomaly detection approaches**.

### Model A — Statistical baseline

Implement:

- Z-score
- Rolling mean
- Rolling standard deviation

Example:

```text
score = abs(value - rolling_mean) / rolling_std
```

### Model B — Machine Learning

Use one of:

- Isolation Forest
- Local Outlier Factor
- One-Class SVM

Recommended:

```text
Isolation Forest
```

The system should output:

```json
{
  "anomaly_score": 0.91,
  "is_anomaly": true,
  "detected_at": "2026-08-16T10:23:41"
}
```

---

# 7. Incident Detection

An anomaly should not automatically become an incident.

Implement an event aggregation layer:

```text
Anomaly Events
      ↓
Temporal Window
      ↓
Service Correlation
      ↓
Similarity Check
      ↓
Incident Cluster
```

Example:

```text
10:23:41 Database timeout
10:23:43 Payment request failed
10:23:45 HTTP 500 spike
10:23:47 Connection pool exhausted
```

These should be grouped into:

```text
INC-20260816-001
Payment Service Database Failure
```

---

# 8. Event Correlation

Correlate events using:

### Temporal correlation
Events occurring within the same time window.

### Service correlation
Events affecting dependent services.

### Request correlation
Use:

```text
request_id
trace_id
```

when available.

### Semantic correlation

Calculate embedding similarity between log messages.

Example:

```text
"DB connection timeout"
        ≈
"Unable to connect to PostgreSQL"
```

These should be treated as potentially related.

---

# 9. Incident Classification

Train a classification model to predict:

### Incident Type

```text
DATABASE
NETWORK
APPLICATION
AUTHENTICATION
PERFORMANCE
MEMORY
CPU
STORAGE
DEPENDENCY
UNKNOWN
```

### Severity

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Possible models:

- Logistic Regression
- Random Forest
- XGBoost
- LightGBM

Recommended baseline:

```text
Random Forest
```

Compare the baseline against one stronger model.

---

# 10. Root Cause Analysis

Build a rule + ML-assisted root cause engine.

Example:

```text
Observed:
- DB timeout ↑
- DB connection pool exhausted
- HTTP 500 ↑
- Payment latency ↑

Possible root cause:
Database connection saturation
```

The engine should produce:

```json
{
  "root_cause": "Database connection saturation",
  "confidence": 0.87,
  "evidence": [
    "Connection timeout increased by 340%",
    "Database pool utilization reached 98%",
    "Payment service latency increased simultaneously",
    "HTTP 500 rate increased after database degradation"
  ]
}
```

Important:

**Do not let the LLM invent the root cause.**

The system must first produce structured evidence from deterministic/ML analysis, then provide that evidence to the LLM.

---

# 11. LLM Incident Intelligence

Integrate an LLM only after the structured incident pipeline is complete.

Input:

```text
Incident metadata
+
Detected anomalies
+
Correlated logs
+
Metrics
+
Root-cause candidates
+
Historical incidents
```

The LLM should generate:

### Incident Summary

```text
Payment service experienced a database connectivity
incident between 10:23 and 10:31.
```

### Impact

```text
HTTP 500 responses increased by 18%.
Average request latency increased from 240ms to 1.8s.
```

### Probable Cause

```text
Database connection pool saturation.
```

### Recommended Investigation

```text
1. Inspect PostgreSQL connection utilization.
2. Check connection pool configuration.
3. Inspect long-running queries.
4. Verify database host health.
```

### Confidence

The LLM must distinguish:

```text
Confirmed
Probable
Possible
Unknown
```

---

# 12. Historical Incident Knowledge Base

Store resolved incidents.

Each incident should contain:

```text
incident_id
title
severity
services
root_cause
resolution
timeline
logs
metrics
created_at
resolved_at
```

Create embeddings for historical incidents.

Use semantic retrieval to find similar incidents:

```text
Current Incident
      ↓
Embedding
      ↓
Vector Search
      ↓
Similar Historical Incidents
      ↓
LLM Context
```

This allows:

> "This incident is similar to INC-20260718-004, which was caused by database connection pool exhaustion."

---

# 13. RAG Layer

Use a vector database such as:

```text
FAISS
```

or:

```text
ChromaDB
```

The RAG pipeline should retrieve:

- Historical incidents
- Runbooks
- Troubleshooting documents
- Service documentation

### Required safeguards

The AI response must:

- Cite retrieved evidence
- Clearly separate evidence from inference
- Avoid unsupported claims
- Return "insufficient evidence" when retrieval confidence is low

---

# 14. Incident Scoring

Create a deterministic incident score.

Example:

```text
Incident Score =
    0.30 × Error Rate
  + 0.20 × Latency Deviation
  + 0.20 × Affected Services
  + 0.15 × Request Failure Rate
  + 0.15 × Anomaly Confidence
```

Map the score to:

```text
0.00 - 0.25 → LOW
0.25 - 0.50 → MEDIUM
0.50 - 0.75 → HIGH
0.75 - 1.00 → CRITICAL
```

Document the reasoning behind the weights.

---

# 15. FastAPI Backend

Build a versioned API.

## Health

```http
GET /api/v1/health
```

## Logs

```http
POST /api/v1/logs/ingest
GET  /api/v1/logs
```

## Anomalies

```http
GET /api/v1/anomalies
POST /api/v1/anomalies/detect
```

## Incidents

```http
GET  /api/v1/incidents
GET  /api/v1/incidents/{incident_id}
POST /api/v1/incidents/analyze
PATCH /api/v1/incidents/{incident_id}/resolve
```

## Predictions

```http
POST /api/v1/predictions/severity
POST /api/v1/predictions/anomaly
```

## AI

```http
POST /api/v1/ai/investigate
POST /api/v1/ai/summarize
POST /api/v1/ai/similar-incidents
```

## Metrics

```http
GET /api/v1/metrics/{service}
GET /api/v1/metrics/{service}/anomalies
```

---

# 16. Database

Use PostgreSQL.

### Optimized Database Tables

To prevent database bloat under 5,000 logs/second load, raw normal logs are processed in-memory and discarded. Only anomalies, incidents, and aggregated metrics are persisted.

```text
services               - ID, name, environment, created_at
metrics_hourly         - service_id, timestamp, cpu_pct, memory_pct, error_rate, latency_p95
anomalies              - ID, service_id, timestamp, message, level, latency_ms, anomaly_score, request_id
incidents              - ID, title, severity, status (ACTIVE/RESOLVED), incident_score, root_cause, confidence, created_at, resolved_at
incident_anomalies     - incident_id, anomaly_id (Many-to-Many join table)
ai_reports             - ID, incident_id, report_markdown, generated_at
```

Use SQLAlchemy.

Requirements:

- Foreign keys
- Indexes (especially on service_id, timestamps, and request_id)
- Timestamps
- Pagination
- Migration support

Use Alembic for migrations.

---

# 17. Background Processing & Messaging

Do not perform expensive ML/LLM operations directly inside HTTP request-response cycles.

### Architecture Components

1. **Redis Pub/Sub:** 
   - Channels: `log-stream` (for raw ingested logs), `anomaly-alerts` (for broadcasting detected anomalies to WebSocket client).
2. **Streaming Analytics Worker:** 
   - Subscribes to `log-stream`.
   - Computes rolling metrics using Redis Sorted Sets.
   - Runs Isolation Forest anomaly detection.
   - Persists anomalies and publishes to `anomaly-alerts`.
3. **Celery Worker + Redis Broker:** 
   - Handles asynchronous, resource-heavy tasks.

### Background Jobs (Celery)

- `incident_clustering`: Groups temporal and semantically related anomalies into incidents using local FAISS vector matching.
- `severity_prediction`: Runs Random Forest severity classifier on incident features.
- `incident_ai_analysis`: Generates RAG prompt, retrieves top 3 similar historical incidents using FAISS, queries Ollama (local LLM), and saves the report.

---

# 18. Frontend Engineering

Build a professional frontend that explicitly demonstrates practical **JavaScript / TypeScript** development.

## Required Stack

```text
React
TypeScript
JavaScript
HTML
CSS
Recharts or ECharts
WebSocket
```

## Required Frontend Capabilities

Implement:

- Component-based architecture
- React Hooks
- Reusable components
- REST API integration
- WebSocket integration
- Async/await and Promise handling
- Typed API models/interfaces
- Form handling and validation
- Loading/error/empty states
- Search and filtering
- Pagination
- Responsive layout
- Data visualization
- Real-time incident updates

## JavaScript / TypeScript Requirements

The codebase should demonstrate practical knowledge of:

- `async/await`
- Promise handling
- Array methods such as `map`, `filter`, `reduce`
- Object/array transformations
- ES modules
- Destructuring
- Event handling
- TypeScript interfaces and types
- Generics where appropriate
- Union types
- Typed API responses
- Reusable custom hooks
- API service layer
- Error handling

Example frontend architecture:

```text
frontend/
├── src/
│   ├── components/
│   │   ├── IncidentCard.tsx
│   │   ├── MetricChart.tsx
│   │   ├── LogTable.tsx
│   │   └── SeverityBadge.tsx
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Incidents.tsx
│   │   └── IncidentDetails.tsx
│   │
│   ├── hooks/
│   │   ├── useIncidents.ts
│   │   ├── useMetrics.ts
│   │   └── useWebSocket.ts
│   │
│   ├── services/
│   │   └── api.ts
│   │
│   ├── types/
│   │   └── incident.ts
│   │
│   └── App.tsx
```

---

# 19. Dashboard

Build a professional and high-fidelity frontend.

Recommended:

```text
React + TypeScript + Vite + Vanilla CSS
```

Dashboard pages & capabilities:

### 1. Overview Dashboard

Display:

- **KPI Cards:** Total Services, Active Incidents (with red pulse animations for CRITICAL severity), Anomalies Today, Average MTTR (Mean Time to Resolution).
- **Real-Time Ingestion Chart (Recharts):** Area/Line chart updating every second via WebSocket, showing incoming log rates, latency metrics, and anomaly counts.
- **Active Incidents Table:** Lists currently unresolved incidents sorted by severity with color-coded badges (Low, Medium, High, Critical).

### 2. Incident Details Page

Display:

- **Incident Header:** Incident ID, Title, Status, and Severity (with color-coded badge).
- **Incident Timeline:** Interactive vertical timeline showing the cascade of events (e.g. `10:23:10 Latency spike` -> `10:23:15 DB Timeout anomaly` -> `10:23:30 HTTP 500 spike` -> `10:24:00 Incident created`).
- **AI Report Panel:** Markdown-rendered investigation report generated by Ollama (Summary, Impact, Probable Cause, Recommended investigation steps).
- **RAG Panel (Similar Incidents):** Side-by-side comparison with the top 3 similar historical incidents retrieved by FAISS.
- **Triggering Anomalies Table:** Lists the actual raw anomalous log events that triggered the incident.

### 3. Real-Time Experience

- Custom hook `useWebSocket` listening to the `anomaly-alerts` and incident update channels.
- Toast notifications and minor alert sounds when new CRITICAL incidents are created to showcase immediate reactivity in demos.

---

# 19. Dataset

Create a reproducible dataset.

Possible sources:

- Public system log datasets
- Public anomaly detection datasets
- Synthetic microservice logs
- Generated metric streams

Recommended approach:

### Real data

Use a public log dataset for baseline experiments.

### Synthetic data

Generate controlled incidents such as:

```text
Database failure
Memory leak
CPU spike
Network latency
Authentication failure
Disk exhaustion
Service dependency failure
```

Synthetic data is important because it gives precise ground truth.

---

# 20. Synthetic Incident Generator

Create:

```text
scripts/generate_incidents.py
```

It should:

- Stream both normal behavior (background traffic) and specific incident scenarios dynamically via HTTP POST to the `/api/v1/logs/ingest` and metrics endpoints.
- Generate structured, ground-truth label indicators for incident scenarios (root cause, expected severity).
- Support options to control ingestion speed (e.g. logs/second) and event duration.

Example Scenario:
`database_connection_exhaustion`

Effects:
- DB latency increases +300%
- HTTP 500 rate increases +20%
- Connection pool utilization reaches +95%
- Payment service latency increases +250%

This allows objective, real-time testing of the streaming pipeline and model evaluation.

---

# 21. Model Evaluation

Do not only show that the model works.

Measure it.

## Anomaly Detection

Report:

```text
Precision
Recall
F1-score
False Positive Rate
```

## Incident Classification

Report:

```text
Accuracy
Precision
Recall
F1-score
Confusion Matrix
```

## Root Cause Analysis

Report:

```text
Top-1 accuracy
Top-3 accuracy
```

## RAG

Evaluate:

```text
Retrieval Precision
Retrieval Recall
Context Relevance
Answer Groundedness
```

---

# 22. Explainability

Every ML prediction should expose useful reasoning.

Example:

```json
{
  "prediction": "CRITICAL",
  "confidence": 0.93,
  "important_features": [
    {
      "feature": "error_rate",
      "impact": 0.41
    },
    {
      "feature": "latency_p99",
      "impact": 0.27
    }
  ]
}
```

For tree-based models, use:

```text
SHAP
```

if practical.

---

# 23. Project Structure

Use a clean architecture:

```text
ai-observability-platform/
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── logs.py
│   │       ├── incidents.py
│   │       ├── anomalies.py
│   │       ├── predictions.py
│   │       └── ai.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── database.py
│   │   ├── schemas.py
│   │   └── ml_models.py
│   │
│   ├── services/
│   │   ├── log_parser.py
│   │   ├── feature_engineering.py
│   │   ├── anomaly_detector.py
│   │   ├── incident_correlator.py
│   │   ├── severity_classifier.py
│   │   ├── root_cause.py
│   │   ├── embedding_service.py
│   │   ├── rag_service.py
│   │   └── llm_service.py
│   │
│   ├── repositories/
│   │   ├── log_repository.py
│   │   └── incident_repository.py
│   │
│   └── main.py
│
├── ml/
│   ├── training/
│   ├── evaluation/
│   └── artifacts/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
│
├── scripts/
│   ├── generate_incidents.py
│   ├── train_models.py
│   └── seed_database.py
│
├── frontend/
│   └── ...
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── docker/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── alembic.ini
├── README.md
└── LICENSE
```

---

# 24. Technology Stack

### Required

```text
Python
FastAPI
Pydantic
SQLAlchemy
PostgreSQL
Pandas
NumPy
Scikit-learn
Git
Docker
```

### AI

```text
Isolation Forest
Random Forest / XGBoost
Sentence Transformers
FAISS / ChromaDB
LLM API
```

### Frontend

```text
React
TypeScript
JavaScript
HTML
CSS
Recharts / ECharts
WebSocket
```

### Optional

```text
Redis
Celery
SHAP
Prometheus
Grafana
MLflow
GitHub Actions
```

---

# 25. Docker

The whole system should start with:

```bash
docker compose up --build
```

Services:

```text
backend
frontend
postgres
redis
```

Optional:

```text
prometheus
grafana
```

---

# 26. Testing Requirements

Minimum:

### Unit tests

Test:

- Log parser
- Feature engineering
- Anomaly scoring
- Incident scoring
- Severity classification
- Root cause rules

### Integration tests

Test:

```text
Log ingestion
→ anomaly detection
→ incident creation
```

### API tests

Test:

```text
POST /logs/ingest
POST /anomalies/detect
GET /incidents
GET /incidents/{id}
POST /ai/investigate
```

Target:

```text
≥ 80% backend test coverage
```

---

# 27. CI/CD

Create GitHub Actions pipeline:

```text
Push
 ↓
Lint
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
Build Docker Image
 ↓
Success
```

Use:

```text
pytest
ruff
```

or equivalent tools.

---

# 28. Security Requirements

Implement basic security practices:

- Environment variables for secrets
- `.env` excluded from Git
- Input validation
- API rate limiting
- Request size limits
- No API keys in source code
- Sanitization of log content before LLM processing

Be especially careful with:

```text
Prompt Injection
```

because logs are untrusted input.

---

# 29. Observability of the AI System

The platform itself should expose:

```text
API latency
ML inference latency
LLM latency
LLM token usage
RAG retrieval latency
Error rate
```

This is important because the project should demonstrate **observability of an AI application**, not only AI-based observability.

---

# 30. Example End-to-End Scenario

Simulate:

```text
Payment Service
      ↓
Database connection pool starts saturating
      ↓
DB latency increases
      ↓
Payment API latency increases
      ↓
HTTP 500 increases
      ↓
Anomaly detector triggers
      ↓
Events are correlated
      ↓
Incident created
      ↓
Severity = CRITICAL
      ↓
Root cause candidate = DB connection saturation
      ↓
Historical incident retrieval
      ↓
LLM investigation
      ↓
Developer receives incident report
```

Final report:

```text
INC-20260816-001

Severity:
CRITICAL

Affected Service:
payment-service

Probable Root Cause:
Database connection pool saturation

Confidence:
87%

Impact:
- HTTP 500 increased by 18%
- P99 latency increased from 410ms to 2.4s
- DB pool utilization reached 98%

Evidence:
1. DB timeout increased 340%
2. Connection pool reached 98%
3. Payment latency increased within 30 seconds
4. HTTP 500 increased immediately afterward

Similar Incident:
INC-20260718-004

Recommended Actions:
1. Inspect active database connections.
2. Check connection pool configuration.
3. Identify long-running queries.
4. Verify database host health.
```

---

# 31. Definition of Done

The project is considered complete only when:

- [ ] Logs can be ingested through API.
- [ ] Logs are normalized into a common schema.
- [ ] Metrics can be processed as time-series data.
- [ ] Anomaly detection works on real/synthetic data.
- [ ] At least two anomaly detection approaches are compared.
- [ ] Related anomalies are grouped into incidents.
- [ ] Incident severity is predicted.
- [ ] Root-cause candidates are generated from structured evidence.
- [ ] Historical incidents can be retrieved semantically.
- [ ] RAG provides grounded context.
- [ ] LLM generates an incident report.
- [ ] LLM does not independently invent root causes.
- [ ] FastAPI exposes the complete pipeline.
- [ ] PostgreSQL stores application data.
- [ ] Background processing handles expensive tasks.
- [ ] React dashboard displays incidents.
- [ ] ML metrics are documented.
- [ ] RAG evaluation is documented.
- [ ] Unit tests are implemented.
- [ ] Integration tests are implemented.
- [ ] Docker Compose starts the system.
- [ ] GitHub Actions runs CI.
- [ ] README contains architecture and setup instructions.
- [ ] `.env.example` is provided.
- [ ] No secrets are committed.
- [ ] Demo scenario can reproduce a complete incident.

---

# 32. CV Positioning

After completion, the project should demonstrate these skills:

```text
Python
JavaScript
TypeScript
React
HTML
CSS
Machine Learning
Anomaly Detection
Classification
Time-Series Analysis
Feature Engineering
NLP
Embeddings
Vector Search
RAG
LLM
Prompt Engineering
FastAPI
REST API
PostgreSQL
Redis
WebSocket
Docker
Testing
CI/CD
Git
System Design
```

The key selling point is:

> **Built an end-to-end AI observability platform that combines anomaly detection, incident correlation, machine learning, semantic retrieval, RAG, LLM-based investigation, and production-style backend engineering.**

This project should replace the LSTM project on the CV because it demonstrates significantly broader **AI Engineering + Software Engineering** capability rather than only showing a single deep-learning model.

---

# 33. Architectural Decision Log

During the initial design and brainstorming phase, the following core decisions were made to shape the project:

### Decision 1: Streaming Ingestion & High-Throughput Processing
- **Choice:** **Option 1: Redis Pub/Sub + Celery/Redis Worker**.
- **Alternatives considered:** Pure Async In-Memory (Option 2), Kafka + Faust (Option 3).
- **Rationale:** Option 1 offers the best balance for a CV project. It provides a robust, decoupled architecture capable of handling 5,000 logs/second by immediately offloading raw logs to Redis Pub/Sub. Unlike Option 2, it demonstrates real-world distributed system patterns. Unlike Option 3, it avoids the heavy resource overhead of Kafka, which would strain a local demo environment.

### Decision 2: Log Storage & Database Write Mitigation
- **Choice:** **Streaming Analysis with Write Filtering**.
- **Alternatives considered:** Writing all raw logs to database, writing raw logs to flat files.
- **Rationale:** Writing 5,000 logs/second directly to PostgreSQL via SQLAlchemy would saturate the database. By analyzing logs in-memory on the worker stream and discarding normal logs, we prevent database bloat. PostgreSQL only stores filtered Anomalies, clustered Incidents, and hourly aggregated metrics.

### Decision 3: Local-Only AI/LLM Infrastructure
- **Choice:** **100% Local / Open-Source (Ollama + SentenceTransformers + FAISS)**.
- **Alternatives considered:** OpenAI/Gemini APIs + Cloud Vector DB (Pinecone).
- **Rationale:** Eliminates external API token costs and ensures the demo runs completely offline in a self-contained local environment. The host machine runs Ollama locally to utilize hardware/GPU acceleration, while SentenceTransformers and FAISS run in the worker containers.

### Decision 4: Demo Simulation Workflow
- **Choice:** **Real-Time Streaming Generator**.
- **Alternatives considered:** Static Database Seeding.
- **Rationale:** Running an independent script to continuously stream logs over HTTP POST allows the frontend to showcase real-time alerts, live charts, and active WebSocket updates, creating a much more interactive and impressive demonstration.

