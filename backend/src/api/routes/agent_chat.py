"""Agent chat route per contracts/chat.md: POST /api/chat."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import AgentContext
from src.agents.director.agent import DirectorAgent
from src.api.deps import get_db
from src.api.schemas.agent import ChatRequest, ChatResponse, SourceCitation
from src.auth.dependencies import get_current_user
from src.config.settings import get_settings
from src.database.models import User
from src.llm.factory import get_llm_provider
from src.rag.pipeline import RAGPipeline
from src.vectordb.store import VectorStore

router = APIRouter(prefix="/chat", tags=["Agent Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    settings = get_settings()
    llm = get_llm_provider(settings)

    # Check LLM availability
    try:
        available = await llm.is_available()
        if not available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable. Please try again later.",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again later.",
        )

    # Build RAG pipeline
    store = VectorStore(path=settings.chroma_db_path)
    rag = RAGPipeline(store=store, llm=llm)

    # Build agent
    agent = DirectorAgent(llm=llm, rag=rag, db=db)

    context = AgentContext(
        user_id=str(current_user.id),
        user_role=current_user.role.value,
        session_id=body.session_id or str(uuid.uuid4()),
    )

    result = await agent.process_message(body.message, context)

    return ChatResponse(
        reply=result.reply,
        intent=result.intent,
        action_taken=result.action_taken,
        data=result.data,
        sources=[
            SourceCitation(
                collection=s.get("collection", ""),
                document=s.get("document", ""),
                relevance_score=s.get("relevance_score"),
            )
            for s in result.sources
        ],
        session_id=result.session_id,
    )
