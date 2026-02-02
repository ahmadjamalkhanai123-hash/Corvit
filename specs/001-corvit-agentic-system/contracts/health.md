# API Contract: Health

## GET /api/health

**Auth**: None
**Description**: System health check for all backends

**Response 200**:
```json
{
  "status": "healthy",
  "checks": {
    "postgres": { "status": "up", "latency_ms": 5 },
    "redis": { "status": "up", "latency_ms": 2 },
    "ollama": { "status": "up", "model": "qwen2.5:7b" },
    "vectordb": { "status": "up", "collections": 4, "documents": 24 }
  },
  "timestamp": "2026-02-02T10:00:00Z"
}
```

**Response 503** (degraded):
```json
{
  "status": "degraded",
  "checks": {
    "postgres": { "status": "up", "latency_ms": 5 },
    "redis": { "status": "up", "latency_ms": 2 },
    "ollama": { "status": "down", "error": "Connection refused" },
    "vectordb": { "status": "up", "collections": 4, "documents": 24 }
  },
  "timestamp": "2026-02-02T10:00:00Z"
}
```
