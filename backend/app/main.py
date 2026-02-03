"""
Nekazari Odoo ERP Module - FastAPI Application

Main entry point for the Odoo orchestration backend.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.routers import tenant, sync, webhook, health
from app.middleware.auth import JWTAuthMiddleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Nekazari Odoo ERP Module API")
    logger.info(f"Odoo URL: {settings.odoo_url}")
    logger.info(f"Orion-LD URL: {settings.ORION_URL}")

    # Initialize database tables if needed
    from app.services.database import init_db
    await init_db()

    yield

    # Shutdown
    logger.info("Shutting down Nekazari Odoo ERP Module API")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    Nekazari Odoo ERP Module API

    Provides orchestration layer for multitenant Odoo integration.

    ## Features

    - Tenant provisioning and management (Multi-DB architecture)
    - NGSI-LD entity synchronization via subscriptions
    - N8N workflow integration
    - Intelligence module predictions

    ## Author

    **Kate Benetis** - kate@robotika.cloud
    **Company**: Robotika
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# JWT Auth Middleware (validates tokens from Keycloak)
app.add_middleware(JWTAuthMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/odoo", tags=["Health"])
app.include_router(tenant.router, prefix="/api/odoo/tenant", tags=["Tenant Management"])
app.include_router(sync.router, prefix="/api/odoo/sync", tags=["Synchronization"])
app.include_router(webhook.router, prefix="/api/odoo/webhook", tags=["Webhooks"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Nekazari Odoo ERP Module",
        "version": settings.API_VERSION,
        "author": "Kate Benetis <kate@robotika.cloud>",
        "company": "Robotika"
    }
