from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.agent_chat import router as agent_chat_router
from src.api.routes.attendance import router as attendance_router
from src.api.routes.auth import router as auth_router
from src.api.routes.batches import router as batches_router
from src.api.routes.courses import router as courses_router
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.enrollments import router as enrollments_router
from src.api.routes.exams import router as exams_router
from src.api.routes.fees import router as fees_router
from src.api.routes.health import router as health_router
from src.api.routes.students import router as students_router
from src.api.routes.teachers import router as teachers_router
from src.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    app.state.settings = settings
    yield
    # Shutdown
    from src.database.connection import engine

    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(students_router, prefix=settings.api_prefix)
    app.include_router(teachers_router, prefix=settings.api_prefix)
    app.include_router(courses_router, prefix=settings.api_prefix)
    app.include_router(batches_router, prefix=settings.api_prefix)
    app.include_router(enrollments_router, prefix=settings.api_prefix)
    app.include_router(attendance_router, prefix=settings.api_prefix)
    app.include_router(fees_router, prefix=settings.api_prefix)
    app.include_router(exams_router, prefix=settings.api_prefix)
    app.include_router(agent_chat_router, prefix=settings.api_prefix)
    app.include_router(dashboard_router, prefix=settings.api_prefix)

    return app


app = create_app()
