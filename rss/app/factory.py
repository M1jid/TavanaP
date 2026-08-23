"""
Application Factory for RSS Service

This module creates and configures the FastAPI application with proper
dependency injection, middleware, and routing setup.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.services.rss_service import RSSService
from app.startup import (
    proxy_server,
    ksql_handler,
    redis_db,
    kafka_router,
    elastic_handler,
    init_elastic_indexes
)

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown logic"""
    # Startup logic
    try:
        logger.info("Starting RSS Service...")

        await init_elastic_indexes()

        # Initialize RSS service
        rss_service = RSSService(
            redis_db=redis_db,
            ksql_handler=ksql_handler,
            kafka_router=kafka_router,
            proxy_server=proxy_server,
            elastic_handler=elastic_handler
        )
        # Start RSS service
        await rss_service.start_service()
        logger.info("RSS Service started successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    yield
    # Shutdown logic
    logger.info("RSS Service shutting down...")
    await rss_service.shutdown_service()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        lifespan=lifespan,
        title="RSS Feed Processing Service",
        description="Service for fetching, processing, and distributing RSS feed content",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        root_path="/rss",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app 