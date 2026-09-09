"""Custom Prometheus metrics for AEO Platform."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# ── HTTP 请求指标 ─────────────────────────────────────────────────────

HTTP_REQUESTS_TOTAL = Counter(
    "aeo_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "aeo_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "aeo_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)

# ── Agent 执行指标 ────────────────────────────────────────────────────

AGENT_EXECUTIONS_TOTAL = Counter(
    "aeo_agent_executions_total",
    "Total agent executions",
    ["agent", "status"],
)

AGENT_EXECUTION_DURATION_SECONDS = Histogram(
    "aeo_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# ── LLM 调用指标 ─────────────────────────────────────────────────────

LLM_CALLS_TOTAL = Counter(
    "aeo_llm_calls_total",
    "Total LLM API calls",
    ["provider", "status"],
)

LLM_CALL_DURATION_SECONDS = Histogram(
    "aeo_llm_call_duration_seconds",
    "LLM API call duration in seconds",
    ["provider"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

LLM_TOKENS_TOTAL = Counter(
    "aeo_llm_tokens_total",
    "Total LLM tokens consumed",
    ["provider", "type"],
)

# ── 任务指标 ─────────────────────────────────────────────────────────

TASKS_TOTAL = Counter(
    "aeo_tasks_total",
    "Total tasks created",
    ["platform", "status"],
)

TASKS_IN_PROGRESS = Gauge(
    "aeo_tasks_in_progress",
    "Number of tasks currently being processed",
)

# ── RAG 知识库指标 ───────────────────────────────────────────────────

RAG_QUERIES_TOTAL = Counter(
    "aeo_rag_queries_total",
    "Total RAG retrieval queries",
    ["status"],
)

RAG_QUERY_DURATION_SECONDS = Histogram(
    "aeo_rag_query_duration_seconds",
    "RAG query duration in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)

RAG_DOCUMENTS_LOADED = Gauge(
    "aeo_rag_documents_loaded",
    "Number of documents currently loaded in knowledge base",
)

RAG_CHUNKS_TOTAL = Gauge(
    "aeo_rag_chunks_total",
    "Total number of chunks in vector store",
)

# ── 系统健康指标 ─────────────────────────────────────────────────────

SYSTEM_INFO = Gauge(
    "aeo_system_info",
    "AEO Platform system information",
    ["version", "python_version"],
)

DATABASE_CONNECTIONS_ACTIVE = Gauge(
    "aeo_database_connections_active",
    "Number of active database connections",
)

REDIS_CONNECTIONS_ACTIVE = Gauge(
    "aeo_redis_connections_active",
    "Number of active Redis connections",
)
