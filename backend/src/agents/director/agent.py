"""Director Agent — classifies intent, routes to handler, returns sourced response."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import AgentContext, AgentResponse, BaseAgent
from src.agents.director.prompts import DIRECTOR_SYSTEM_PROMPT
from src.agents.director.router import IntentRouter
from src.agents.director.tools import check_fees, get_attendance_summary
from src.llm.base import LLMMessage, LLMProvider
from src.rag.pipeline import RAGPipeline
from src.rules.attendance_rules import evaluate_attendance
from src.rules.engine import RuleEngine
from src.rules.fee_rules import evaluate_fees


class DirectorAgent(BaseAgent):
    """Director Agent that classifies intent, routes to handler, and builds response."""

    def __init__(
        self,
        llm: LLMProvider,
        rag: RAGPipeline,
        db: AsyncSession,
        rule_engine: RuleEngine | None = None,
    ):
        self._llm = llm
        self._rag = rag
        self._db = db
        self._router = IntentRouter(llm)
        self._rule_engine = rule_engine or RuleEngine()

    async def process_message(
        self, message: str, context: AgentContext | None = None
    ) -> AgentResponse:
        session_id = context.session_id if context else str(uuid.uuid4())

        # 1. Classify intent
        intent = await self._router.classify(message)

        # 2. Route to handler
        handler = self._get_handler(intent)
        result = await handler(message, context)

        result.intent = intent
        result.session_id = session_id
        return result

    def _get_handler(self, intent: str):
        handlers = {
            "course_inquiry": self._handle_rag,
            "enrollment": self._handle_rag,
            "fee_query": self._handle_fee_query,
            "attendance_query": self._handle_attendance_query,
            "counseling": self._handle_rag,
            "complaint": self._handle_complaint,
            "general": self._handle_rag,
            "class_related": self._handle_stub,
            "lab_related": self._handle_stub,
        }
        return handlers.get(intent, self._handle_rag)

    async def _handle_rag(
        self, message: str, context: AgentContext | None
    ) -> AgentResponse:
        """Handle queries that need RAG pipeline."""
        try:
            rag_response = await self._rag.query(message)
            sources = [
                {
                    "collection": s.collection,
                    "document": s.document,
                    "relevance_score": round(1 - (s.distance or 0), 2) if s.distance else None,
                }
                for s in rag_response.sources
            ]
            return AgentResponse(
                reply=rag_response.answer,
                sources=sources,
            )
        except Exception as e:
            return AgentResponse(
                reply="I'm having trouble accessing my knowledge base right now. Please try again later.",
                sources=[],
            )

    async def _handle_attendance_query(
        self, message: str, context: AgentContext | None
    ) -> AgentResponse:
        """Handle attendance queries using rule engine."""
        if not context or not context.user_id:
            return AgentResponse(
                reply="I need to know which student to check attendance for. Please provide your student ID or log in.",
            )

        try:
            user_id = uuid.UUID(context.user_id)
        except (ValueError, TypeError):
            # Fall back to RAG if user_id is not a valid UUID
            return await self._handle_rag(message, context)

        summary = await get_attendance_summary(self._db, user_id)

        if summary["total_classes"] == 0:
            return AgentResponse(
                reply="No attendance records found for your account.",
                action_taken="attendance_checked",
                data=summary,
            )

        # Evaluate against rules
        alert = self._rule_engine.evaluate_attendance_percentage(summary["percentage"])

        reply = (
            f"Your attendance summary:\n"
            f"- Total classes: {summary['total_classes']}\n"
            f"- Present: {summary['present']}, Absent: {summary['absent']}, Late: {summary['late']}\n"
            f"- Attendance: {summary['percentage']}%\n"
        )

        if alert.level != "none":
            reply += f"\n⚠️ Alert ({alert.level}): {alert.message}"

        action = "rule_alert_triggered" if alert.level != "none" else "attendance_checked"
        data = {
            "attendance_percentage": summary["percentage"],
            "alert_level": alert.level,
        }
        if alert.level != "none":
            data["threshold"] = 85 if alert.level == "yellow" else (75 if alert.level == "orange" else 60)

        return AgentResponse(
            reply=reply,
            action_taken=action,
            data=data,
        )

    async def _handle_fee_query(
        self, message: str, context: AgentContext | None
    ) -> AgentResponse:
        """Handle fee queries with DB lookup + RAG fallback."""
        if context and context.user_id:
            try:
                user_id = uuid.UUID(context.user_id)
                fee_data = await check_fees(self._db, user_id)

                if fee_data["fees"]:
                    reply = "Here's your fee summary:\n\n"
                    for f in fee_data["fees"]:
                        reply += f"- **{f['course']}**: PKR {f['amount']:,.0f} (Paid: PKR {f['paid']:,.0f}, Remaining: PKR {f['remaining']:,.0f})\n"
                        if f["days_overdue"] > 0:
                            reply += f"  ⚠️ Overdue by {f['days_overdue']} days\n"

                    reply += f"\n**Total Due: PKR {fee_data['total_due']:,.0f}**"

                    return AgentResponse(
                        reply=reply,
                        action_taken="fee_checked",
                        data=fee_data,
                    )
            except (ValueError, TypeError):
                pass

        # Fall back to RAG for general fee questions
        return await self._handle_rag(message, context)

    async def _handle_complaint(
        self, message: str, context: AgentContext | None
    ) -> AgentResponse:
        """Handle complaints with LLM response."""
        system_prompt = DIRECTOR_SYSTEM_PROMPT.format(
            context="The user has a complaint. Respond empathetically, acknowledge their concern, and guide them on next steps. If the issue requires human intervention, suggest contacting the administration."
        )
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=message),
        ]

        try:
            response = await self._llm.generate(messages)
            return AgentResponse(
                reply=response.content,
                action_taken="complaint_acknowledged",
            )
        except Exception:
            return AgentResponse(
                reply="I'm sorry to hear about your concern. Please contact the administration directly at the front desk or via email for immediate assistance.",
                action_taken="complaint_acknowledged",
            )

    async def _handle_stub(
        self, message: str, context: AgentContext | None
    ) -> AgentResponse:
        """Stub handler for Phase 2 features."""
        return AgentResponse(
            reply="This feature is coming soon in Phase 2. For now, please contact the administration for assistance with class scheduling and lab bookings.",
            action_taken="stub_response",
        )
