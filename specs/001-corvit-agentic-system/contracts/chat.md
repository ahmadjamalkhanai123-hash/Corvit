# API Contract: Agent Chat

**Base**: `/api/chat`
**Auth**: Bearer JWT (any role)

## POST /api/chat

**Description**: Send a message to the Director Agent and receive an intent-classified, sourced response.

**Request**:
```json
{
  "message": "What courses do you offer?",
  "session_id": "optional-uuid-for-continuity"
}
```

**Response 200**:
```json
{
  "reply": "Corvit Systems offers 5 courses:\n\n1. **CCNA** (12 weeks, PKR 25,000)\n2. **CCNP** (16 weeks, PKR 40,000)\n3. **AI & Machine Learning** (12 weeks, PKR 35,000)\n4. **Cyber Security** (12 weeks, PKR 30,000)\n5. **Cloud Computing** (10 weeks, PKR 28,000)\n\nWould you like details about any specific course?",
  "intent": "course_inquiry",
  "action_taken": null,
  "data": null,
  "sources": [
    {
      "collection": "courses",
      "document": "Corvit offers CCNA, CCNP...",
      "relevance_score": 0.92
    }
  ],
  "session_id": "uuid"
}
```

**Response 200** (with action):
```json
{
  "reply": "I can enroll you in the CCNA Batch-1 starting January 15. Please confirm.",
  "intent": "enrollment",
  "action_taken": "enrollment_proposed",
  "data": {
    "student_id": "uuid",
    "batch_id": "uuid",
    "batch_name": "CCNA-Batch-1",
    "requires_confirmation": true
  },
  "sources": [],
  "session_id": "uuid"
}
```

**Response 200** (rule-based alert):
```json
{
  "reply": "Your attendance is at 72%, which is below the 75% threshold. This is an orange-level alert. Please improve your attendance to avoid escalation.",
  "intent": "attendance_query",
  "action_taken": "rule_alert_triggered",
  "data": {
    "attendance_percentage": 72.0,
    "alert_level": "orange",
    "threshold": 75
  },
  "sources": [],
  "session_id": "uuid"
}
```

**Response 503**:
```json
{
  "detail": "AI service temporarily unavailable. Please try again later.",
  "error_code": "LLM_UNAVAILABLE"
}
```

## Intent Categories

| Intent | Handler | Uses LLM |
|--------|---------|----------|
| course_inquiry | RAG Pipeline | Yes |
| enrollment | DB Action + LLM | Yes |
| fee_query | RAG + DB | Yes |
| attendance_query | Rule Engine + DB | No |
| counseling | RAG Pipeline | Yes |
| complaint | LLM | Yes |
| general | RAG Pipeline | Yes |
| class_related | Stub (Phase 2) | No |
| lab_related | Stub (Phase 2) | No |
