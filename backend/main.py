"""
FastAPI application entry point.

Configures middleware, lifespan events (database connect/disconnect),
and exposes the health-check endpoint.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.core.config import get_settings
from app.core.database import MongoDB
from app.core.vector_db import VectorDB
from app.api.webhooks import router as webhook_router
from app.api.razorpay_webhooks import router as razorpay_webhook_router
from app.api.auth import router as auth_router
from app.api.business import router as business_router
from app.api.menu import router as menu_router
from app.api.orders import router as orders_router
from app.api.analytics import router as analytics_router
from app.api.engagement import router as engagement_router
from app.api.demo import router as demo_router
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ── Lifespan (startup / shutdown) ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.

    On startup:
        - Connect to MongoDB
        - Connect to Qdrant
    On shutdown:
        - Disconnect from MongoDB
        - Disconnect from Qdrant
    """
    logger.info("🚀 Starting AI WhatsApp Business Assistant …")

    # --- Startup --------------------------------------------------
    try:
        await MongoDB.connect()
        # ── Create performance indexes ─────────────────────────────────
        db = MongoDB.get_database()
        await db.businesses.create_index("owner_email", unique=True)
        await db.menu.create_index([("business_id", 1), ("available", 1)])
        await db.menu_items.create_index([("business_id", 1), ("available", 1)])
        await db.orders.create_index([("business_id", 1), ("created_at", -1)])
        await db.orders.create_index("customer_phone")
        await db.chats.create_index([("business_id", 1), ("customer_phone", 1)])
        await db.engagement_events.create_index([("business_id", 1), ("sent_at", -1)])
        logger.info("MongoDB indexes ensured")
    except Exception as exc:
        logger.warning("MongoDB unavailable at startup: %s", exc)

    try:
        await VectorDB.connect()
    except Exception as exc:
        logger.warning("Qdrant unavailable at startup: %s", exc)

    # ── Start background scheduler for proactive engagement ────────
    try:
        from app.services.scheduler import scheduler, setup_scheduler
        setup_scheduler()
        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler started with QSR policy jobs")
    except Exception as exc:
        logger.warning("Scheduler startup skipped: %s", exc)

    logger.info(
        "Server ready — %s mode on %s:%s",
        settings.ENVIRONMENT,
        settings.HOST,
        settings.PORT,
    )

    yield  # --- application runs here ---

    # --- Shutdown -------------------------------------------------
    logger.info("Shutting down …")
    try:
        from app.services.scheduler import scheduler
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("APScheduler shut down")
    except Exception:
        pass
    await MongoDB.disconnect()
    await VectorDB.disconnect()
    logger.info("Goodbye 👋")


# ── FastAPI instance ───────────────────────────────────────────────────
app = FastAPI(
    title="AI WhatsApp Business Assistant",
    description=(
        "Backend API for an AI-powered WhatsApp assistant that handles "
        "customer queries, takes orders, and processes payments 24/7 "
        "for SMBs in India."
    ),
    version="0.1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# ── Middleware ─────────────────────────────────────────────────────────

# CORS — allow everything during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request with its duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "%s %s → %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ── Routes ─────────────────────────────────────────────────────────────

app.include_router(webhook_router)
app.include_router(razorpay_webhook_router)
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(menu_router)
app.include_router(orders_router)
app.include_router(analytics_router)
app.include_router(engagement_router)
app.include_router(demo_router)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the connectivity status of MongoDB and Qdrant along with the
    current UTC timestamp.
    """
    mongo_ok = await MongoDB.is_connected()
    qdrant_ok = await VectorDB.is_connected()

    overall = "healthy" if (mongo_ok and qdrant_ok) else "degraded"

    return {
        "status": overall,
        "mongodb": "connected" if mongo_ok else "disconnected",
        "qdrant": "connected" if qdrant_ok else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": app.version,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — simple welcome message."""
    return {
        "message": "AI WhatsApp Business Assistant API",
        "docs": "/docs",
        "health": "/health",
    }


# ── Entrypoint ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
