import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from app.api.routes import (
    auth,
    dashboard,
    incidents,
    alerts,
    services,
    escalation_policies,
    users,
    audit
)
from app.workers.escalation_worker import start_in_process_escalation_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opspulse")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: spawn escalation check background loop
    escalation_task = asyncio.create_task(start_in_process_escalation_loop())
    logger.info("OpsPulse AI backend initialized.")
    yield
    # Shutdown: cancel background task
    escalation_task.cancel()
    try:
        await escalation_task
    except asyncio.CancelledError:
        pass
    logger.info("OpsPulse AI backend stopped.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Incident Management & Service Reliability Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(incidents.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(services.router, prefix=settings.API_V1_STR)
app.include_router(escalation_policies.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Diagnostics"])
def health_check():
    """Liveness probe: verifies the application process is running."""
    return {"status": "healthy", "service": "opspulse-ai", "environment": settings.ENVIRONMENT}

@app.get("/ready", tags=["Diagnostics"])
def readiness_check():
    """Readiness probe: verifies PostgreSQL database reachability and system readiness."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
    except Exception as e:
        logger.error("Readiness check database failure: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failure"
        )

    redis_status = "skipped"
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        if r.ping():
            redis_status = "connected"
    except Exception:
        redis_status = "offline_or_unreachable"

    return {
        "status": "ready",
        "database": db_status,
        "redis": redis_status,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
